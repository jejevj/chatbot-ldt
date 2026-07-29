"""
Search service for data retrieval
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database import DataTerbuka, DataEmbedding

logger = logging.getLogger(__name__)

# Lazy load embedding service
_embedding_service = None
_embedding_service_checked = False

# Stopwords Bahasa Indonesia yang tidak perlu di-index
STOPWORDS = {
    'dan', 'di', 'ke', 'dari', 'yang', 'ini', 'itu', 'atau', 'juga',
    'dengan', 'untuk', 'pada', 'adalah', 'ada', 'tidak', 'saya', 'anda',
    'kamu', 'kami', 'kita', 'mereka', 'akan', 'sudah', 'bisa', 'dapat',
    'tentang', 'apa', 'bagaimana', 'berapa', 'siapa', 'mana', 'kapan',
    'ingin', 'mau', 'tolong', 'mohon', 'saja', 'aja', 'dong', 'deh',
    'info', 'informasi', 'data', 'terkait', 'mengenai', 'seputar',
    'kirimkan', 'berikan', 'tampilkan', 'cari', 'carikan', 'lihat',
}


def get_embedding_service():
    """Lazy load embedding service"""
    global _embedding_service, _embedding_service_checked

    if not _embedding_service_checked:
        _embedding_service_checked = True
        try:
            from app.services.embedding_service import EmbeddingService
            _embedding_service = EmbeddingService()
            logger.info("Embedding service loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load embedding service: {str(e)}")
            _embedding_service = None

    return _embedding_service


def get_all_categories(db: Session) -> dict:
    """
    Ambil semua nilai unik tipe_data dan kategori_data dari view.
    Digunakan untuk memberi konteks ke LLM saat tidak ada hasil pencarian.
    """
    try:
        sql = text("""
            SELECT DISTINCT tipe_data, kategori_data
            FROM v_detail_data_terbuka
            WHERE tipe_data IS NOT NULL OR kategori_data IS NOT NULL
            ORDER BY tipe_data, kategori_data
        """)
        result = db.execute(sql)
        rows = result.fetchall()

        tipe_set = sorted(set(r[0] for r in rows if r[0]))
        kategori_set = sorted(set(r[1] for r in rows if r[1]))

        return {"tipe_data": tipe_set, "kategori_data": kategori_set}
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        return {"tipe_data": [], "kategori_data": []}


def search_data(
    db: Session,
    query: str,
    limit: int = None,
    use_embedding: bool = None
) -> List:
    """
    Search for relevant data based on query.
    Mencoba vector search terlebih dahulu, fallback ke keyword search.
    """
    limit = limit or settings.SEARCH_LIMIT
    use_embedding = use_embedding if use_embedding is not None else settings.USE_EMBEDDINGS

    try:
        if not DataEmbedding or not use_embedding:
            logger.info("Using keyword-based search")
            return _keyword_search(db, query, limit)

        try:
            embedding_count = db.query(DataEmbedding).count()
        except Exception:
            embedding_count = 0

        if embedding_count > 0:
            logger.info(f"Using vector search with {embedding_count} embeddings")
            return _vector_search(db, query, limit)

        logger.info("No embeddings found, using keyword search")
        return _keyword_search(db, query, limit)

    except Exception as e:
        logger.error(f"Error in search_data: {str(e)}", exc_info=True)
        return _keyword_search(db, query, limit)


def _vector_search(db: Session, query: str, limit: int) -> List:
    """Vector similarity search"""
    try:
        embedding_service = get_embedding_service()
        if not embedding_service:
            logger.warning("Embedding service not available")
            return _keyword_search(db, query, limit)

        query_embedding = embedding_service.encode(query)

        results = db.query(
            DataEmbedding,
            DataEmbedding.embedding.cosine_distance(query_embedding).label('distance')
        ).order_by('distance').limit(limit * 2).all()

        if not results:
            logger.info("No results from vector search, fallback to keyword")
            return _keyword_search(db, query, limit)

        top_results = results[:limit]
        kode_data_list = [r.DataEmbedding.kode_data for r in top_results]

        sql = text("""
            SELECT url, kode_data, tipe_data, kategori_data, sifat_data, deskripsi_data, judul_data
            FROM v_detail_data_terbuka
            WHERE kode_data = ANY(:kode_list)
        """)
        result = db.execute(sql, {"kode_list": kode_data_list})
        rows = result.fetchall()

        data_list = [_row_to_obj(row) for row in rows]
        logger.info(f"Found {len(data_list)} results using vector search")
        return data_list

    except Exception as e:
        logger.error(f"Error in vector search: {str(e)}", exc_info=True)
        return _keyword_search(db, query, limit)


def _keyword_search(db: Session, query: str, limit: int) -> List:
    """Keyword-based search with scoring.
    
    Perbaikan:
    - Filter stopwords agar keyword lebih relevan
    - Minimal panjang keyword diturunkan ke >= 2 karakter
    - Jika tidak ada keyword valid setelah filter stopwords,
      coba juga pencarian berdasarkan kategori/tipe dari full query
    """
    try:
        sql = text("""
            SELECT url, kode_data, tipe_data, kategori_data, sifat_data, deskripsi_data, judul_data
            FROM v_detail_data_terbuka
        """)
        result = db.execute(sql)
        all_data = result.fetchall()

        if not all_data:
            logger.warning("v_detail_data_terbuka is empty or inaccessible")
            return []

        # Ekstrak keywords: minimal 2 karakter, buang stopwords
        raw_tokens = [k.lower() for k in query.split()]
        keywords = [
            k for k in raw_tokens
            if len(k) >= 2 and k not in STOPWORDS
        ]

        # Jika semua token adalah stopwords, gunakan semua token >= 2 karakter
        if not keywords:
            keywords = [k for k in raw_tokens if len(k) >= 2]

        # Jika masih kosong, tidak ada yang bisa dicari
        if not keywords:
            logger.info("No valid keywords extracted from query")
            return []

        logger.info(f"Total data: {len(all_data)}, keywords after filter: {keywords}")

        scored_results = []
        for row in all_data:
            url, kode_data, tipe_data, kategori_data, sifat_data, deskripsi_data, judul_data = row

            score = 0
            judul_lower = (judul_data or '').lower()
            kategori_lower = (kategori_data or '').lower()
            tipe_lower = (tipe_data or '').lower()
            deskripsi_lower = (deskripsi_data or '').lower()
            kode_lower = (kode_data or '').lower()

            data_text = f"{judul_lower} {deskripsi_lower} {kategori_lower} {tipe_lower} {kode_lower}"

            for keyword in keywords:
                if keyword in data_text:
                    if keyword in judul_lower:
                        score += 5
                    elif keyword in kategori_lower or keyword in tipe_lower:
                        score += 3
                    elif keyword in deskripsi_lower:
                        score += 2
                    else:
                        score += 1

            if score > 0:
                scored_results.append((score, _row_to_obj(row)))

        scored_results.sort(key=lambda x: x[0], reverse=True)

        if not scored_results:
            logger.info(f"No keyword matches found for: {keywords}")
            return []

        logger.info(f"Found {len(scored_results)} matches, returning top {limit}")
        return [data for score, data in scored_results[:limit]]

    except Exception as e:
        logger.error(f"Error in keyword search: {str(e)}", exc_info=True)
        raise


def _row_to_obj(row):
    """Convert raw SQL row tuple ke object DataTerbuka-like"""
    return type('DataTerbuka', (), {
        'url': row[0],
        'kode_data': row[1],
        'tipe_data': row[2],
        'kategori_data': row[3],
        'sifat_data': row[4],
        'deskripsi_data': row[5],
        'judul_data': row[6]
    })()
