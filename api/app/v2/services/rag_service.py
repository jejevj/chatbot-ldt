"""
RAG service — retrieval + prompt building untuk Kemhan chatbot

Prioritas retrieval:
  1. Ground truth (feedback applied)
     - score >= 0.55 : bypass LLM, langsung return jawaban koreksi
     - score >= 0.20 : inject ke prompt sebagai [REFERENSI TERVERIFIKASI],
                       LLM DIWAJIBKAN menggunakannya via system prompt
  2. FAQ semantic match
  3. Vector similarity dari dokumen
"""
import re
import logging
from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.v2.config import v2_settings
from app.v2.database import KemhanFeedback, KemhanFAQ, KemhanDocChunk, KemhanEmbedding
from app.v2.services.embedding_service import embed_single
from app.v2.services.llm_service import call_llm
from app.v2.schemas import ChatSource

logger = logging.getLogger(__name__)

# Stopword bahasa Indonesia yang diabaikan saat matching
_STOPWORDS = {
    "apa", "siapa", "bagaimana", "dimana", "kapan", "mengapa", "berapa",
    "apakah", "adalah", "yang", "di", "ke", "dari", "dan", "atau", "ini",
    "itu", "dengan", "untuk", "dalam", "pada", "oleh", "juga", "tidak",
    "bisa", "ada", "ya", "tidak", "iya", "saya", "kamu", "anda",
}

SYSTEM_PROMPT = """\
Kamu adalah {assistant_name}, asisten informasi resmi {scope}.
{gt_instruction}\
Jawab pertanyaan pengguna HANYA berdasarkan konteks dokumen yang diberikan.
Jika informasi tidak tersedia dalam konteks, katakan dengan jujur bahwa kamu tidak memiliki informasi tersebut.
Gunakan bahasa Indonesia yang formal, jelas, dan mudah dipahami.
Jangan mengarang informasi yang tidak ada dalam konteks.
"""

GT_INSTRUCTION = """\
PERHATIAN PENTING: Konteks mengandung [REFERENSI TERVERIFIKASI] yang merupakan \
jawaban yang sudah dikoreksi dan divalidasi oleh admin.
KAMU WAJIB menggunakan jawaban dari [REFERENSI TERVERIFIKASI] tersebut secara verbatim \
(kata per kata) tanpa mengubah isinya.
Jangan menambahkan, mengurangi, atau memparafrase jawaban dari [REFERENSI TERVERIFIKASI].
"""


def _normalize(text: str) -> str:
    """Lowercase, hapus tanda baca, strip whitespace."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)  # hapus tanda baca
    text = re.sub(r"\s+", " ", text)
    return text


def _tokenize(text: str, remove_stopwords: bool = True) -> set:
    """Tokenize teks, opsional buang stopwords, min 2 karakter."""
    tokens = set(_normalize(text).split())
    tokens = {t for t in tokens if len(t) >= 2}
    if remove_stopwords:
        tokens -= _STOPWORDS
    return tokens


def _bigrams(tokens: set) -> set:
    """Generate bigram dari set token (urutan tidak penting, kombinasi 2 token)."""
    lst = sorted(tokens)
    return {f"{lst[i]}_{lst[j]}" for i in range(len(lst)) for j in range(i+1, len(lst))}


def _similarity_score(query: str, reference: str) -> float:
    """
    Skor similaritas gabungan:
    - 70% dari unigram Jaccard (token overlap, stopword dihapus)
    - 30% dari bigram Jaccard (menangkap frasa, lebih tahan parafrase)
    Mengembalikan 0.0 - 1.0.
    """
    q_uni  = _tokenize(query)
    r_uni  = _tokenize(reference)
    q_bi   = _bigrams(q_uni)
    r_bi   = _bigrams(r_uni)

    def jaccard(a: set, b: set) -> float:
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    uni_score = jaccard(q_uni, r_uni)
    bi_score  = jaccard(q_bi,  r_bi) if (q_bi and r_bi) else 0.0

    return round(0.70 * uni_score + 0.30 * bi_score, 4)


def _search_ground_truth(
    db: Session,
    query: str,
    limit: int = 3,
    threshold: float = 0.20,
) -> List[Tuple[str, str, float]]:
    """
    Cari ground truth (status=applied) yang paling mirip dengan query.
    Scoring: gabungan unigram + bigram Jaccard.
    """
    feedbacks = db.query(KemhanFeedback).filter(
        KemhanFeedback.status == "applied"
    ).all()

    results = []
    for fb in feedbacks:
        score = _similarity_score(query, fb.pertanyaan_asli)
        if score >= threshold:
            results.append((fb.pertanyaan_asli, fb.jawaban_koreksi, score))

    results.sort(key=lambda x: x[2], reverse=True)
    return results[:limit]


def _search_faq(db: Session, query: str, limit: int = 3) -> List[Tuple[str, str, float]]:
    """Cari FAQ yang relevan menggunakan scoring yang sama."""
    faqs = db.query(KemhanFAQ).filter(KemhanFAQ.is_active == True).all()
    results = []
    for faq in faqs:
        score = _similarity_score(query, faq.pertanyaan)
        if score > 0:
            results.append((faq.pertanyaan, faq.jawaban, score))
    results.sort(key=lambda x: x[2], reverse=True)
    return results[:limit]


def _search_documents(
    db: Session,
    query_embedding: List[float],
    limit: int = 5,
) -> List[Tuple[str, str, float]]:
    """Cari chunk dokumen yang paling relevan via vector similarity."""
    if KemhanEmbedding is None:
        logger.warning("pgvector tidak tersedia, skip vector search")
        return []
    try:
        rows = db.execute(
            text("""
                SELECT c.chunk_text, d.judul,
                       e.embedding <=> CAST(:qvec AS vector) AS distance
                FROM t_kemhan_embeddings e
                JOIN t_kemhan_doc_chunks c ON c.id = e.chunk_id
                JOIN t_kemhan_documents  d ON d.id = c.doc_id
                WHERE d.status = 'ready'
                  AND e.embedding <=> CAST(:qvec AS vector) < :threshold
                ORDER BY distance ASC
                LIMIT :limit
            """),
            {
                "qvec":      str(query_embedding),
                "threshold": v2_settings.V2_EMBEDDING_THRESHOLD,
                "limit":     limit,
            }
        ).fetchall()
        return [(r[0], r[1], round(1 - r[2], 4)) for r in rows]
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        return []


async def answer_question(
    db: Session,
    question: str,
) -> Tuple[str, List[ChatSource]]:
    """
    Pipeline RAG dengan prioritas:
      1. Ground truth >= 0.55  -> bypass LLM, return verbatim
      2. Ground truth 0.20-0.54 -> inject + LLM wajib pakai
      3. FAQ + Dokumen          -> konteks biasa
    """
    sources:       List[ChatSource] = []
    context_parts: List[str]        = []
    has_verified   = False

    # ── 1. Ground truth ──────────────────────────────────────────
    ground_truths = _search_ground_truth(db, question)

    if ground_truths:
        best_q, best_a, best_score = ground_truths[0]
        logger.info(
            f"[rag] Ground truth best match score={best_score:.4f} "
            f"untuk: {question!r} | ref: {best_q!r}"
        )

        if best_score >= 0.55:
            # ── Bypass LLM: langsung return jawaban koreksi ──────
            logger.info(f"[rag] BYPASS LLM — ground truth score={best_score:.4f}")
            sources.append(ChatSource(
                tipe="ground_truth",
                judul=f"Koreksi terverifikasi: {best_q[:60]}",
                relevansi=best_score,
            ))
            return best_a, sources

        # ── Inject ke konteks, LLM akan diwajibkan menggunakannya ─
        has_verified = True
        for q, a, score in ground_truths:
            context_parts.append(
                f"[REFERENSI TERVERIFIKASI — GUNAKAN JAWABAN INI VERBATIM]\n"
                f"Pertanyaan: {q}\n"
                f"Jawaban: {a}"
            )
            sources.append(ChatSource(
                tipe="ground_truth",
                judul=f"Koreksi: {q[:60]}",
                relevansi=best_score,
            ))

    # ── 2. FAQ ───────────────────────────────────────────────────
    if not has_verified:  # kalau sudah ada GT, skip FAQ agar tidak campur
        faqs = _search_faq(db, question)
        for q, a, score in faqs:
            context_parts.append(f"[FAQ]\nPertanyaan: {q}\nJawaban: {a}")
            sources.append(ChatSource(tipe="faq", judul=q[:80], relevansi=score))

    # ── 3. Dokumen vector search ─────────────────────────────────
    try:
        q_emb = embed_single(question)
        doc_results = _search_documents(db, q_emb)
        for chunk_text, doc_judul, score in doc_results:
            context_parts.append(f"[DOKUMEN: {doc_judul}]\n{chunk_text}")
            sources.append(ChatSource(tipe="document", judul=doc_judul, relevansi=score))
    except Exception as e:
        logger.warning(f"Embedding/vector search gagal: {e}")

    # ── 4. Build prompt ──────────────────────────────────────────
    gt_instruction = GT_INSTRUCTION if has_verified else ""
    system_msg = SYSTEM_PROMPT.format(
        assistant_name=v2_settings.V2_ASSISTANT_NAME,
        scope=v2_settings.V2_ASSISTANT_SCOPE,
        gt_instruction=gt_instruction,
    )

    if context_parts:
        context_str = "\n\n---\n".join(context_parts)
        user_msg = f"Konteks:\n{context_str}\n\nPertanyaan: {question}"
    else:
        user_msg = (
            f"Pertanyaan: {question}\n\n"
            "(Tidak ada dokumen referensi yang tersedia untuk pertanyaan ini.)"
        )

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user",   "content": user_msg},
    ]

    answer = await call_llm(messages)
    return answer, sources
