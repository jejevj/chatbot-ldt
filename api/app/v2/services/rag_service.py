"""
RAG service — retrieval + prompt building untuk Kemhan chatbot

Prioritas retrieval:
  1. Ground truth (feedback applied) — semantic cosine similarity via pgvector
     - cosine score >= 0.82 : bypass LLM, return jawaban koreksi verbatim
     - cosine score >= 0.50 : inject ke prompt, LLM WAJIB gunakan verbatim
     - Fallback ke lexical (bigram Jaccard) jika embedding belum ada
  2. FAQ — lexical scoring
  3. Dokumen — vector similarity
"""
import re
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

# ── Threshold ──────────────────────────────────────────────────
GT_BYPASS_COSINE    = 0.82   # bypass LLM langsung
GT_INJECT_COSINE    = 0.50   # inject ke konteks + paksa LLM
GT_BYPASS_LEXICAL   = 0.55   # fallback lexical bypass
GT_INJECT_LEXICAL   = 0.20   # fallback lexical inject
FAQ_MIN_SCORE       = 0.05

# ── Prompt ──────────────────────────────────────────────────
SYSTEM_PROMPT = """\
Kamu adalah {assistant_name}, asisten informasi resmi {scope}.
{gt_instruction}\
Jawab pertanyaan pengguna HANYA berdasarkan konteks dokumen yang diberikan.
Jika informasi tidak tersedia dalam konteks, katakan dengan jujur bahwa kamu tidak memiliki informasi tersebut.
Gunakan bahasa Indonesia yang formal, jelas, dan mudah dipahami.
Jangan mengarang informasi yang tidak ada dalam konteks.
"""

GT_INSTRUCTION = """\
PERHATIAN KRITIS: Konteks mengandung [REFERENSI TERVERIFIKASI] yang merupakan
jawaban yang sudah dikoreksi dan divalidasi oleh admin secara resmi.
KAMU WAJIB menggunakan jawaban dari [REFERENSI TERVERIFIKASI] tersebut KATA PER KATA
tanpa mengubah, menambah, atau mengurangi isinya.
Abaikan semua konteks lain jika bertentangan dengan [REFERENSI TERVERIFIKASI].
"""

_STOPWORDS = {
    "apa", "siapa", "bagaimana", "dimana", "kapan", "mengapa", "berapa",
    "apakah", "adalah", "yang", "di", "ke", "dari", "dan", "atau", "ini",
    "itu", "dengan", "untuk", "dalam", "pada", "oleh", "juga", "tidak",
    "bisa", "ada", "ya", "iya", "saya", "kamu", "anda", "nya", "lah",
}


# ── Lexical helpers ───────────────────────────────────────────
def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", s.lower())).strip()

def _tokenize(s: str) -> set:
    return {t for t in _normalize(s).split() if len(t) >= 2 and t not in _STOPWORDS}

def _bigrams(tokens: set) -> set:
    lst = sorted(tokens)
    return {f"{lst[i]}_{lst[j]}" for i in range(len(lst)) for j in range(i + 1, len(lst))}

def _jaccard(a: set, b: set) -> float:
    if not a and not b: return 1.0
    if not a or  not b: return 0.0
    return len(a & b) / len(a | b)

def _lexical_score(q: str, ref: str) -> float:
    qu, ru = _tokenize(q), _tokenize(ref)
    qb, rb = _bigrams(qu),  _bigrams(ru)
    return round(0.70 * _jaccard(qu, ru) + 0.30 * _jaccard(qb, rb), 4)


# ── Cosine similarity (pure Python, tidak butuh DB) ──────────────
def _cosine(a: List[float], b: List[float]) -> float:
    dot  = sum(x * y for x, y in zip(a, b))
    na   = sum(x * x for x in a) ** 0.5
    nb   = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return round(dot / (na * nb), 4)


# ── Ground truth search ─────────────────────────────────────
def _search_ground_truth(
    db: Session,
    query: str,
    query_embedding: Optional[List[float]],
    limit: int = 3,
) -> List[Tuple[str, str, float, str]]:  # (pertanyaan, jawaban, score, metode)
    """
    Cari ground truth paling relevan.
    Strategi:
      A) Jika query_embedding tersedia DAN feedback punya question_embedding
         → cosine similarity (akurat, tahan parafrase)
      B) Fallback: bigram Jaccard lexical
    Return: list of (pertanyaan_asli, jawaban_koreksi, score, method)
    """
    feedbacks = db.query(KemhanFeedback).filter(
        KemhanFeedback.status == "applied"
    ).all()

    if not feedbacks:
        return []

    results = []
    for fb in feedbacks:
        emb = fb.question_embedding

        if query_embedding is not None and emb is not None:
            # Konversi dari berbagai tipe (list, pgvector type, str)
            if isinstance(emb, str):
                import json
                try:
                    emb = json.loads(emb)
                except Exception:
                    emb = None
            if emb is not None:
                score  = _cosine(query_embedding, list(emb))
                method = "cosine"
                results.append((fb.pertanyaan_asli, fb.jawaban_koreksi, score, method))
                continue

        # Fallback lexical
        score = _lexical_score(query, fb.pertanyaan_asli)
        results.append((fb.pertanyaan_asli, fb.jawaban_koreksi, score, "lexical"))

    results.sort(key=lambda x: x[2], reverse=True)
    return results[:limit]


# ── FAQ search ────────────────────────────────────────────
def _search_faq(db: Session, query: str, limit: int = 3) -> List[Tuple[str, str, float]]:
    faqs = db.query(KemhanFAQ).filter(KemhanFAQ.is_active == True).all()
    results = [
        (faq.pertanyaan, faq.jawaban, _lexical_score(query, faq.pertanyaan))
        for faq in faqs
        if _lexical_score(query, faq.pertanyaan) >= FAQ_MIN_SCORE
    ]
    results.sort(key=lambda x: x[2], reverse=True)
    return results[:limit]


# ── Document vector search ─────────────────────────────────
def _search_documents(
    db: Session,
    query_embedding: List[float],
    limit: int = 5,
) -> List[Tuple[str, str, float]]:
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


# ── Main pipeline ───────────────────────────────────────────
async def answer_question(
    db: Session,
    question: str,
) -> Tuple[str, List[ChatSource]]:
    """
    Pipeline RAG:
      1. Embed query sekali, pakai untuk GT cosine + doc vector search
      2. Ground truth cosine >= 0.82  -> bypass LLM
      3. Ground truth cosine >= 0.50  -> inject + wajib dipakai LLM
      4. FAQ + Dokumen                -> konteks biasa
    """
    sources:       List[ChatSource] = []
    context_parts: List[str]        = []
    has_verified                    = False

    # ── Embed query (dipakai untuk GT cosine + doc search) ────────
    query_embedding: Optional[List[float]] = None
    try:
        query_embedding = embed_single(question)
    except Exception as e:
        logger.warning(f"[rag] Gagal embed query: {e} — fallback ke lexical")

    # ── 1. Ground truth ───────────────────────────────────────
    ground_truths = _search_ground_truth(db, question, query_embedding)

    if ground_truths:
        best_q, best_a, best_score, method = ground_truths[0]
        logger.info(
            f"[rag] GT best match: score={best_score:.4f} method={method} "
            f"| query={question!r} | ref={best_q!r}"
        )

        bypass_thr = GT_BYPASS_COSINE  if method == "cosine" else GT_BYPASS_LEXICAL
        inject_thr = GT_INJECT_COSINE  if method == "cosine" else GT_INJECT_LEXICAL

        if best_score >= bypass_thr:
            logger.info(f"[rag] BYPASS LLM — {method} score={best_score:.4f}")
            sources.append(ChatSource(
                tipe="ground_truth",
                judul=f"Koreksi terverifikasi: {best_q[:60]}",
                relevansi=best_score,
            ))
            return best_a, sources

        if best_score >= inject_thr:
            has_verified = True
            for q, a, score, m in ground_truths:
                if score < inject_thr:
                    break
                context_parts.append(
                    f"[REFERENSI TERVERIFIKASI — GUNAKAN JAWABAN INI KATA PER KATA]\n"
                    f"Pertanyaan: {q}\nJawaban: {a}"
                )
                sources.append(ChatSource(
                    tipe="ground_truth",
                    judul=f"Koreksi ({m}): {q[:60]}",
                    relevansi=score,
                ))

    # ── 2. FAQ ───────────────────────────────────────────────
    if not has_verified:
        faqs = _search_faq(db, question)
        for q, a, score in faqs:
            context_parts.append(f"[FAQ]\nPertanyaan: {q}\nJawaban: {a}")
            sources.append(ChatSource(tipe="faq", judul=q[:80], relevansi=score))

    # ── 3. Dokumen vector search ─────────────────────────────
    if query_embedding is not None:
        try:
            doc_results = _search_documents(db, query_embedding)
            for chunk_text, doc_judul, score in doc_results:
                context_parts.append(f"[DOKUMEN: {doc_judul}]\n{chunk_text}")
                sources.append(ChatSource(tipe="document", judul=doc_judul, relevansi=score))
        except Exception as e:
            logger.warning(f"[rag] Doc search gagal: {e}")

    # ── 4. Build prompt ───────────────────────────────────────
    system_msg = SYSTEM_PROMPT.format(
        assistant_name=v2_settings.V2_ASSISTANT_NAME,
        scope=v2_settings.V2_ASSISTANT_SCOPE,
        gt_instruction=GT_INSTRUCTION if has_verified else "",
    )

    if context_parts:
        user_msg = "Konteks:\n" + "\n\n---\n".join(context_parts) + f"\n\nPertanyaan: {question}"
    else:
        user_msg = (
            f"Pertanyaan: {question}\n\n"
            "(Tidak ada dokumen referensi yang tersedia untuk pertanyaan ini.)"
        )

    answer = await call_llm([
        {"role": "system", "content": system_msg},
        {"role": "user",   "content": user_msg},
    ])
    return answer, sources
