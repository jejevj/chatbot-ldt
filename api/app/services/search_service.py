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


def search_data(
    db: Session,
    query: str,
    limit: int = None,
    use_embedding: bool = None
) -> List:
    """
    Search for relevant data based on query
    
    Args:
        db: Database session
        query: Search query
        limit: Maximum results to return
        use_embedding: Whether to use vector search
        
    Returns:
        List of data objects
    """
    limit = limit or settings.SEARCH_LIMIT
    use_embedding = use_embedding if use_embedding is not None else settings.USE_EMBEDDINGS
    
    try:
        # Check if embeddings available
        if not DataEmbedding or not use_embedding:
            logger.info("Using keyword-based search")
            return _keyword_search(db, query, limit)
        
        # Check if embeddings exist in database
        try:
            embedding_count = db.query(DataEmbedding).count()
        except:
            embedding_count = 0
        
        if embedding_count > 0:
            logger.info(f"Using vector search with {embedding_count} embeddings")
            return _vector_search(db, query, limit)
        
        # Fallback to keyword search
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
        
        # Generate query embedding
        query_embedding = embedding_service.encode(query)
        
        # Search with cosine similarity
        results = db.query(
            DataEmbedding,
            DataEmbedding.embedding.cosine_distance(query_embedding).label('distance')
        ).order_by('distance').limit(limit * 2).all()
        
        if not results:
            logger.info("No results from vector search")
            return []
        
        # Filter by threshold
        filtered_results = [r for r in results if r.distance < settings.EMBEDDING_THRESHOLD]
        
        if not filtered_results:
            logger.info("No results below similarity threshold")
            return []
        
        # Get actual data
        kode_data_list = [r.DataEmbedding.kode_data for r in filtered_results[:limit]]
        
        # Use raw SQL to avoid primary key issues
        sql = text("""
            SELECT url, kode_data, tipe_data, kategori_data, sifat_data, deskripsi_data, judul_data
            FROM v_detail_data_terbuka
            WHERE kode_data = ANY(:kode_list)
        """)
        
        result = db.execute(sql, {"kode_list": kode_data_list})
        rows = result.fetchall()
        
        # Convert to objects
        data_list = []
        for row in rows:
            data_obj = type('DataTerbuka', (), {
                'url': row[0],
                'kode_data': row[1],
                'tipe_data': row[2],
                'kategori_data': row[3],
                'sifat_data': row[4],
                'deskripsi_data': row[5],
                'judul_data': row[6]
            })()
            data_list.append(data_obj)
        
        logger.info(f"Found {len(data_list)} results using vector search")
        return data_list
    
    except Exception as e:
        logger.error(f"Error in vector search: {str(e)}", exc_info=True)
        return _keyword_search(db, query, limit)


def _keyword_search(db: Session, query: str, limit: int) -> List:
    """Keyword-based search with scoring"""
    try:
        # Get all data using raw SQL
        sql = text("""
            SELECT url, kode_data, tipe_data, kategori_data, sifat_data, deskripsi_data, judul_data
            FROM v_detail_data_terbuka
        """)
        
        result = db.execute(sql)
        all_data = result.fetchall()
        
        # Extract keywords (minimal filtering)
        keywords = [k.lower() for k in query.split() if len(k) > 2]
        
        if not keywords:
            logger.info("No valid keywords found in query")
            return []
        
        logger.info(f"Total data: {len(all_data)}, keywords: {keywords}")
        
        # Score each data
        scored_results = []
        for row in all_data:
            url, kode_data, tipe_data, kategori_data, sifat_data, deskripsi_data, judul_data = row
            
            score = 0
            data_text = f"{judul_data or ''} {deskripsi_data or ''} {kategori_data or ''} {tipe_data or ''} {kode_data or ''}".lower()
            
            for keyword in keywords:
                if keyword in data_text:
                    # Higher score for title match
                    if keyword in (judul_data or '').lower():
                        score += 5
                    # Medium score for category/type
                    elif keyword in (kategori_data or '').lower() or keyword in (tipe_data or '').lower():
                        score += 3
                    # Lower score for description/code
                    else:
                        score += 1
            
            # Include if score > 0 (any match)
            if score > 0:
                data_obj = type('DataTerbuka', (), {
                    'url': url,
                    'kode_data': kode_data,
                    'tipe_data': tipe_data,
                    'kategori_data': kategori_data,
                    'sifat_data': sifat_data,
                    'deskripsi_data': deskripsi_data,
                    'judul_data': judul_data
                })()
                scored_results.append((score, data_obj))
        
        # Sort and return top results
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        if not scored_results:
            logger.info("No keyword matches found")
            return []
        
        logger.info(f"Found {len(scored_results)} matches, returning top {limit}")
        return [data for score, data in scored_results[:limit]]
    
    except Exception as e:
        logger.error(f"Error in keyword search: {str(e)}", exc_info=True)
        raise
