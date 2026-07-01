"""
RAG service — retrieval + prompt building untuk Kemhan chatbot

Prioritas retrieval:
  1. Ground truth (feedback applied) — jika sangat mirip, langsung jadi jawaban tanpa LLM
  2. FAQ exact/semantic match
  3. Vector similarity dari dokumen
"""
import logging
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.v2.config import v2_settings
from app.v2.database import KemhanFeedback, KemhanFAQ, KemhanDocChunk, KemhanEmbedding
from app.v2.services.embedding_service import embed_single
from app.v2.services.llm_service import call_llm
from app.v2.schemas import ChatSource

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Kamu adalah {assistant_name}, asisten informasi resmi {scope}.
Jawab pertanyaan pengguna HANYA berdasarkan konteks dokumen yang diberikan.
Jika informasi tidak tersedia dalam konteks, katakan dengan jujur bahwa kamu tidak memiliki informasi tersebut.
Gunakan bahasa Indonesia yang formal, jelas, dan mudah dipahami.
Jangan mengarang informasi yang tidak ada dalam konteks.
"""


def _token_overlap_score(query: str, text_ref: str) -> float:
    """
    Hitung skor overlap token antara query dan teks referensi.
    Menggunakan semua kata (min 2 karakter) agar kata pendek seperti nama tetap tertangkap.
    Mengembalikan nilai 0.0 - 1.0.
    """
    q_tokens   = set(w.lower() for w in query.split()   if len(w) >= 2)
    ref_tokens = set(w.lower() for w in text_ref.split() if len(w) >= 2)
    if not q_tokens:
        return 0.0
    overlap = q_tokens & ref_tokens
    # Jaccard-like: overlap / union
    return len(overlap) / len(q_tokens | ref_tokens)


def _search_ground_truth(
    db: Session,
    query: str,
    limit: int = 3,
    threshold: float = 0.15,   # minimal skor overlap agar dianggap relevan
) -> List[Tuple[str, str, float]]:
    """
    Cari ground truth yang paling mirip dengan query.
    Scoring berdasarkan token overlap pada pertanyaan_asli.
    """
    feedbacks = db.query(KemhanFeedback).filter(
        KemhanFeedback.status == "applied"
    ).all()

    results = []
    for fb in feedbacks:
        score = _token_overlap_score(query, fb.pertanyaan_asli)
        if score >= threshold:
            results.append((fb.pertanyaan_asli, fb.jawaban_koreksi, score))

    results.sort(key=lambda x: x[2], reverse=True)
    return results[:limit]


def _search_faq(db: Session, query: str, limit: int = 3) -> List[Tuple[str, str, float]]:
    """Cari FAQ yang relevan dengan token overlap scoring."""
    faqs = db.query(KemhanFAQ).filter(KemhanFAQ.is_active == True).all()
    results = []
    for faq in faqs:
        score = _token_overlap_score(query, faq.pertanyaan) + \
                _token_overlap_score(query, faq.jawaban) * 0.5
        if score > 0:
            results.append((faq.pertanyaan, faq.jawaban, score))
    results.sort(key=lambda x: x[2], reverse=True)
    return results[:limit]


def _search_documents(db: Session, query_embedding: List[float], limit: int = 5) -> List[Tuple[str, str, float]]:
    """Cari chunk dokumen yang paling relevan via vector similarity."""
    if KemhanEmbedding is None:
        logger.warning("pgvector tidak tersedia, skip vector search")
        return []
    try:
        results = db.execute(
            text("""
                SELECT c.chunk_text, d.judul, e.embedding <=> CAST(:qvec AS vector) AS distance
                FROM t_kemhan_embeddings e
                JOIN t_kemhan_doc_chunks c ON c.id = e.chunk_id
                JOIN t_kemhan_documents d ON d.id = c.doc_id
                WHERE d.status = 'ready'
                  AND e.embedding <=> CAST(:qvec AS vector) < :threshold
                ORDER BY distance ASC
                LIMIT :limit
            """),
            {
                "qvec": str(query_embedding),
                "threshold": v2_settings.V2_EMBEDDING_THRESHOLD,
                "limit": limit,
            }
        ).fetchall()
        return [(row[0], row[1], 1 - row[2]) for row in results]
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        return []


async def answer_question(db: Session, question: str) -> Tuple[str, List[ChatSource]]:
    """
    Pipeline RAG:
    1. Cari ground truth — jika skor sangat tinggi (>=0.6), langsung return jawaban koreksi tanpa LLM
    2. Retrieve FAQ + dokumen sebagai konteks tambahan
    3. Build prompt dengan konteks
    4. Call LLM
    5. Return jawaban + sources
    """
    sources: List[ChatSource] = []
    context_parts: List[str] = []

    # 1. Ground truth — prioritas tertinggi
    ground_truths = _search_ground_truth(db, question)

    if ground_truths:
        best_q, best_a, best_score = ground_truths[0]

        # Kalau sangat mirip (>=0.6), langsung pakai jawaban koreksi tanpa perlu LLM
        if best_score >= 0.6:
            logger.info(f"Ground truth direct match (score={best_score:.2f}) untuk: {question!r}")
            sources.append(ChatSource(
                tipe="ground_truth",
                judul=f"Koreksi: {best_q[:60]}",
                relevansi=round(best_score, 4),
            ))
            return best_a, sources

        # Skor sedang (0.15-0.59): masukkan ke konteks sebagai referensi terverifikasi
        for q, a, score in ground_truths:
            context_parts.append(f"[REFERENSI TERVERIFIKASI]\nPertanyaan: {q}\nJawaban: {a}")
            sources.append(ChatSource(
                tipe="ground_truth",
                judul=f"Koreksi: {q[:60]}",
                relevansi=round(score, 4),
            ))

    # 2. FAQ
    faqs = _search_faq(db, question)
    for q, a, score in faqs:
        context_parts.append(f"[FAQ]\nPertanyaan: {q}\nJawaban: {a}")
        sources.append(ChatSource(tipe="faq", judul=q[:80], relevansi=round(score, 4)))

    # 3. Dokumen vector search
    try:
        q_emb = embed_single(question)
        doc_results = _search_documents(db, q_emb)
        for chunk_text, doc_judul, score in doc_results:
            context_parts.append(f"[DOKUMEN: {doc_judul}]\n{chunk_text}")
            sources.append(ChatSource(tipe="document", judul=doc_judul, relevansi=round(score, 4)))
    except Exception as e:
        logger.warning(f"Embedding/vector search gagal: {e}")

    # 4. Build prompt
    system_msg = SYSTEM_PROMPT.format(
        assistant_name=v2_settings.V2_ASSISTANT_NAME,
        scope=v2_settings.V2_ASSISTANT_SCOPE,
    )

    if context_parts:
        context_str = "\n\n---\n".join(context_parts)
        user_msg = f"Konteks:\n{context_str}\n\nPertanyaan: {question}"
    else:
        user_msg = f"Pertanyaan: {question}\n\n(Tidak ada dokumen referensi yang tersedia untuk pertanyaan ini.)"

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user",   "content": user_msg},
    ]

    answer = await call_llm(messages)
    return answer, sources
