"""
Service: generate 5 FAQ dari dokumen rujukan menggunakan LLM.

Flow:
  1. Ambil semua chunk teks dari dokumen (dibatasi 8000 karakter)
  2. Kirim ke LLM dengan prompt khusus — minta output JSON array 5 FAQ
  3. Parse response JSON
  4. Simpan ke t_kemhan_faq dengan document_id
"""
import json
import logging
from typing import List, Dict

from sqlalchemy.orm import Session

from app.v2.database import KemhanDocument, KemhanDocChunk, KemhanFAQ
from app.v2.services.llm_service import call_llm

logger = logging.getLogger(__name__)

FAQ_COUNT = 5

SYSTEM_FAQ = """Kamu adalah asisten yang bertugas membuat FAQ (Frequently Asked Questions) \
berbahasa Indonesia dari sebuah dokumen.
Tugas kamu hanya menghasilkan output JSON array, tidak ada penjelasan atau teks lain di luar array."""

USER_FAQ_TEMPLATE = """Dokumen: "{judul}"

Isi dokumen:
---
{konten}
---

Buat tepat {n} pertanyaan dan jawaban FAQ yang paling relevan dan informatif dari dokumen di atas.
Fokus pada informasi penting yang kemungkinan sering ditanyakan.

Output HARUS berupa JSON array murni, tanpa markdown, tanpa komentar, contoh format:
[
  {{
    "pertanyaan": "Apa itu ...?",
    "jawaban": "... adalah ...",
    "kategori": "umum"
  }}
]

Kategori yang valid: umum, regulasi, teknis, faq
Hanya output JSON array, tidak ada teks apapun di luar array."""


def _get_doc_context(db: Session, document_id: int, max_chars: int = 8000) -> str:
    """Gabungkan chunk teks dokumen (dibatasi max_chars)."""
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


def _parse_faq_json(raw: str) -> List[Dict]:
    """Parse JSON array dari response LLM; strip markdown code block jika ada."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        # buang baris pertama (```json) dan terakhir (```)
        raw = "\n".join(lines[1:-1]).strip()
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Response LLM bukan JSON array")
    return data


async def generate_faq_for_document(
    db: Session,
    document_id: int,
    delete_existing: bool = False,
) -> List[KemhanFAQ]:
    """
    Generate (atau regenerate) 5 FAQ untuk sebuah dokumen.

    Args:
        db             : SQLAlchemy session
        document_id    : ID dokumen di t_kemhan_documents
        delete_existing: True = hapus FAQ lama dulu (untuk regenerate)

    Returns:
        List[KemhanFAQ] yang baru disimpan
    """
    doc: KemhanDocument = db.query(KemhanDocument).filter(
        KemhanDocument.id == document_id
    ).first()
    if not doc:
        raise ValueError(f"Dokumen ID {document_id} tidak ditemukan")
    if doc.status != "ready":
        raise ValueError(f"Dokumen '{doc.judul}' belum siap (status: {doc.status})")

    # Hapus FAQ lama kalau regenerate
    if delete_existing:
        db.query(KemhanFAQ).filter(KemhanFAQ.document_id == document_id).delete()
        db.commit()

    # Ambil konteks teks
    konten = _get_doc_context(db, document_id)
    if not konten.strip():
        raise ValueError("Dokumen tidak memiliki teks yang bisa diproses")

    # Bangun messages (format sama dengan rag_service)
    messages = [
        {"role": "system", "content": SYSTEM_FAQ},
        {
            "role": "user",
            "content": USER_FAQ_TEMPLATE.format(
                judul=doc.judul,
                konten=konten,
                n=FAQ_COUNT,
            )
        },
    ]

    # Panggil LLM (async, sama persis dengan rag_service)
    raw_response = await call_llm(messages, temperature=0.4)

    # Parse JSON
    try:
        faq_data = _parse_faq_json(raw_response)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Gagal parse JSON dari LLM: {e}\nRaw response: {raw_response[:500]}")
        raise ValueError(f"LLM tidak menghasilkan JSON yang valid: {e}")

    # Simpan ke DB
    saved: List[KemhanFAQ] = []
    for item in faq_data[:FAQ_COUNT]:
        pertanyaan = str(item.get("pertanyaan", "")).strip()
        jawaban    = str(item.get("jawaban",    "")).strip()
        kategori   = str(item.get("kategori",  "umum")).strip()

        if not pertanyaan or not jawaban:
            logger.warning(f"Item FAQ dilewati karena kosong: {item}")
            continue

        faq = KemhanFAQ(
            document_id=document_id,
            pertanyaan=pertanyaan,
            jawaban=jawaban,
            kategori=kategori,
            is_active=True,
        )
        db.add(faq)
        saved.append(faq)

    db.commit()
    for faq in saved:
        db.refresh(faq)

    logger.info(f"Generated {len(saved)} FAQ untuk dokumen '{doc.judul}' (id={document_id})")
    return saved
