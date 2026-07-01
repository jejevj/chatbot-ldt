"""
Service: generate 5 FAQ dari dokumen rujukan menggunakan LLM.

Flow:
  1. Ambil chunk teks HANYA dari dokumen yang dipilih (filter strict by doc_id)
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
MAX_CHARS = 8000

SYSTEM_FAQ = (
    "Kamu adalah asisten yang bertugas membuat FAQ (Frequently Asked Questions) "
    "berbahasa Indonesia HANYA dari dokumen yang diberikan di bawah ini.\n"
    "JANGAN menggunakan informasi dari luar dokumen tersebut.\n"
    "Tugas kamu hanya menghasilkan output JSON array, "
    "tidak ada penjelasan atau teks lain di luar array."
)

USER_FAQ_TEMPLATE = """Dokumen: "{judul}"

Isi dokumen (hanya dari dokumen ini):
---
{konten}
---

Buat tepat {n} pertanyaan dan jawaban FAQ yang paling relevan dan informatif \
DARI DOKUMEN DI ATAS SAJA. Jangan buat FAQ tentang topik lain.

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


def _get_doc_context(db: Session, document_id: int, max_chars: int = MAX_CHARS) -> str:
    """
    Ambil dan gabungkan chunk teks HANYA dari dokumen dengan id = document_id.
    Filter dilakukan secara eksplisit dengan .filter(KemhanDocChunk.doc_id == document_id).
    """
    chunks: List[KemhanDocChunk] = (
        db.query(KemhanDocChunk)
        .filter(KemhanDocChunk.doc_id == document_id)   # <-- filter ketat per dokumen
        .order_by(KemhanDocChunk.chunk_index.asc())
        .all()
    )

    logger.info(f"[faq_generator] doc_id={document_id}: ditemukan {len(chunks)} chunks")

    parts = []
    total = 0
    for chunk in chunks:
        text = chunk.chunk_text or ""
        if total + len(text) > max_chars:
            # potong sebagian agar tetap dalam batas
            remaining = max_chars - total
            if remaining > 100:
                parts.append(text[:remaining])
            break
        parts.append(text)
        total += len(text)

    logger.info(f"[faq_generator] doc_id={document_id}: total chars konteks = {total}")
    return "\n\n".join(parts)


def _parse_faq_json(raw: str) -> List[Dict]:
    """Parse JSON array dari response LLM; strip markdown code block jika ada."""
    raw = raw.strip()

    # Coba strip markdown code fence
    if raw.startswith("```"):
        lines = raw.split("\n")
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        raw = "\n".join(inner).strip()

    # Coba ambil substring JSON array jika ada teks pembuka dari LLM
    start = raw.find("[")
    end   = raw.rfind("]")
    if start != -1 and end != -1 and end > start:
        raw = raw[start:end + 1]

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
    Generate (atau regenerate) FAQ untuk SATU dokumen saja.

    Args:
        db             : SQLAlchemy session
        document_id    : ID dokumen di t_kemhan_documents
        delete_existing: True = hapus FAQ lama dulu (untuk regenerate)

    Returns:
        List[KemhanFAQ] yang baru disimpan
    """
    # Validasi dokumen
    doc: KemhanDocument = (
        db.query(KemhanDocument)
        .filter(KemhanDocument.id == document_id)
        .first()
    )
    if not doc:
        raise ValueError(f"Dokumen ID {document_id} tidak ditemukan")
    if doc.status != "ready":
        raise ValueError(f"Dokumen '{doc.judul}' belum siap (status: {doc.status})")

    logger.info(f"[faq_generator] Generate FAQ untuk dokumen '{doc.judul}' (id={document_id})")

    # Hapus FAQ lama kalau regenerate
    if delete_existing:
        deleted = db.query(KemhanFAQ).filter(KemhanFAQ.document_id == document_id).delete()
        db.commit()
        logger.info(f"[faq_generator] Dihapus {deleted} FAQ lama untuk doc_id={document_id}")

    # Ambil HANYA konteks dari dokumen ini
    konten = _get_doc_context(db, document_id)
    if not konten.strip():
        raise ValueError(
            f"Dokumen '{doc.judul}' tidak memiliki teks yang bisa diproses. "
            "Pastikan dokumen sudah selesai diproses (status: ready) dan memiliki chunks."
        )

    # Bangun prompt
    messages = [
        {"role": "system", "content": SYSTEM_FAQ},
        {
            "role": "user",
            "content": USER_FAQ_TEMPLATE.format(
                judul=doc.judul,
                konten=konten,
                n=FAQ_COUNT,
            ),
        },
    ]

    logger.info(f"[faq_generator] Memanggil LLM untuk doc_id={document_id} ...")
    raw_response = await call_llm(messages, temperature=0.3)
    logger.debug(f"[faq_generator] Raw LLM response: {raw_response[:300]}")

    # Parse JSON
    try:
        faq_data = _parse_faq_json(raw_response)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(
            f"[faq_generator] Gagal parse JSON dari LLM: {e}\n"
            f"Raw response: {raw_response[:500]}"
        )
        raise ValueError(f"LLM tidak menghasilkan JSON yang valid: {e}")

    # Simpan ke DB dengan document_id yang tepat
    saved: List[KemhanFAQ] = []
    for item in faq_data[:FAQ_COUNT]:
        pertanyaan = str(item.get("pertanyaan", "")).strip()
        jawaban    = str(item.get("jawaban",    "")).strip()
        kategori   = str(item.get("kategori",   "umum")).strip()

        if not pertanyaan or not jawaban:
            logger.warning(f"[faq_generator] Item FAQ dilewati (kosong): {item}")
            continue

        faq = KemhanFAQ(
            document_id=document_id,   # selalu set ke dokumen yang dipilih
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

    logger.info(
        f"[faq_generator] Selesai: {len(saved)} FAQ disimpan "
        f"untuk dokumen '{doc.judul}' (id={document_id})"
    )
    return saved
