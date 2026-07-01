"""
Service: generate 5 FAQ dari dokumen rujukan menggunakan LLM.

Flow:
  1. Ambil semua chunk teks dari dokumen (max 3000 token gabungan)
  2. Kirim ke LLM dengan prompt khusus — minta output JSON array 5 FAQ
  3. Parse response JSON
  4. Simpan ke t_kemhan_faq dengan document_id
"""
import json
import logging
from typing import List, Dict

from sqlalchemy.orm import Session

from app.v2.database import KemhanDocument, KemhanDocChunk, KemhanFAQ

logger = logging.getLogger(__name__)

FAQ_COUNT = 5  # jumlah FAQ yang di-generate per dokumen

# Template prompt yang dikirim ke LLM
FAQ_PROMPT_TEMPLATE = """Kamu adalah asisten yang bertugas membuat FAQ (Frequently Asked Questions) \
berbahasa Indonesia dari dokumen berikut.

Dokumen: "{judul}"

Isi dokumen:
---
{konten}
---

Tugas:
Buat tepat {n} pertanyaan dan jawaban FAQ yang paling relevan dan informatif berdasarkan isi dokumen di atas.
Fokus pada informasi yang paling penting dan sering ditanyakan.

Format output HARUS berupa JSON array murni (tanpa markdown, tanpa komentar), contoh:
[
  {{
    "pertanyaan": "Apa itu ...?",
    "jawaban": "... adalah ...",
    "kategori": "umum"
  }}
]

Hanya output JSON array, tidak ada teks lain di luar array."""


def _get_doc_context(db: Session, document_id: int, max_chars: int = 8000) -> str:
    """Gabungkan chunk teks dokumen (dibatasi max_chars agar tidak overflow konteks LLM)."""
    chunks: List[KemhanDocChunk] = (
        db.query(KemhanDocChunk)
        .filter(KemhanDocChunk.doc_id == document_id)
        .order_by(KemhanDocChunk.chunk_index)
        .all()
    )
    parts = []
    total = 0
    for chunk in chunks:
        if total + len(chunk.chunk_text) > max_chars:
            break
        parts.append(chunk.chunk_text)
        total += len(chunk.chunk_text)
    return "\n\n".join(parts)


def _call_llm(prompt: str) -> str:
    """
    Panggil LLM melalui service chat yang sudah ada di project.
    Import lazy agar tidak circular import.
    """
    try:
        # Coba pakai ChatService v2 yang sudah ada
        from app.v2.services.chat_service import ChatService  # noqa: F401
        svc = ChatService()
        # Gunakan metode generate langsung tanpa RAG agar hasilnya murni dari prompt
        raw = svc.llm.invoke(prompt)
        # LangChain BaseMessage atau string
        return raw.content if hasattr(raw, "content") else str(raw)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise


def _parse_faq_json(raw: str) -> List[Dict]:
    """Parse JSON array dari response LLM; coba ekstrak jika ada teks di luar array."""
    raw = raw.strip()
    # Hapus markdown code block jika ada
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Response LLM bukan JSON array")
    return data


def generate_faq_for_document(
    db: Session,
    document_id: int,
    delete_existing: bool = False,
) -> List[KemhanFAQ]:
    """
    Generate (atau regenerate) 5 FAQ untuk sebuah dokumen.

    Args:
        db: SQLAlchemy session
        document_id: ID dokumen di t_kemhan_documents
        delete_existing: True = hapus FAQ lama dulu (untuk regenerate)

    Returns:
        List[KemhanFAQ] — FAQ yang baru disimpan
    """
    doc: KemhanDocument = db.query(KemhanDocument).filter(
        KemhanDocument.id == document_id
    ).first()
    if not doc:
        raise ValueError(f"Dokumen ID {document_id} tidak ditemukan")
    if doc.status != "ready":
        raise ValueError(f"Dokumen '{doc.judul}' belum siap (status: {doc.status})")

    # Hapus FAQ lama jika regenerate
    if delete_existing:
        db.query(KemhanFAQ).filter(KemhanFAQ.document_id == document_id).delete()
        db.commit()

    # Ambil konteks teks dokumen
    konten = _get_doc_context(db, document_id)
    if not konten.strip():
        raise ValueError("Dokumen tidak memiliki teks yang bisa diproses")

    # Buat prompt
    prompt = FAQ_PROMPT_TEMPLATE.format(
        judul=doc.judul,
        konten=konten,
        n=FAQ_COUNT,
    )

    # Panggil LLM
    raw_response = _call_llm(prompt)
    faq_data = _parse_faq_json(raw_response)

    # Simpan ke DB
    saved: List[KemhanFAQ] = []
    for item in faq_data[:FAQ_COUNT]:  # batasi max 5 walaupun LLM kadang lebih
        faq = KemhanFAQ(
            document_id=document_id,
            pertanyaan=item.get("pertanyaan", "").strip(),
            jawaban=item.get("jawaban", "").strip(),
            kategori=item.get("kategori", "umum"),
            is_active=True,
        )
        db.add(faq)
        saved.append(faq)

    db.commit()
    for faq in saved:
        db.refresh(faq)

    logger.info(f"Generated {len(saved)} FAQ untuk dokumen '{doc.judul}' (id={document_id})")
    return saved
