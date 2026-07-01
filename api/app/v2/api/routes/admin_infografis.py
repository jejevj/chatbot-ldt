"""
Admin Infografis API — generate SVG infografis dari dokumen rujukan (beta)

Flow:
  1. Ambil teks dokumen dari t_kemhan_doc_chunks (maks 9000 karakter)
  2. Panggil LLM dengan prompt infografis SVG
  3. Normalisasi output (strip markdown fence)
  4. Return JSON: { judul_dokumen, svg }
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.v2.dependencies import require_admin
from app.v2.database import KemhanDocument, KemhanDocChunk
from app.v2.services.llm_service import call_llm

router = APIRouter(prefix="/admin/infografis", tags=["admin-infografis"])


class InfografisRequest(BaseModel):
    document_id: int


SYSTEM_PROMPT = """\
Kamu adalah perancang infografis berbasis SVG untuk dokumen resmi pemerintah Indonesia.
Tugas:
  1. Baca isi dokumen yang diberikan secara menyeluruh.
  2. Simpulkan data penting: angka, tanggal, program, struktur organisasi.
  3. Hasilkan kode SVG murni untuk infografis.

Spesifikasi SVG wajib:
  - width="960" height="540" (rasio 16:9)
  - Latar belakang gelap (#1a1a2e), aksen emas (#f59e0b), teks putih (#ffffff)
  - font-family="Arial, sans-serif"
  - Struktur: judul header, subjudul ringkasan, 3-6 panel data utama
  - Gunakan elemen: rect, text, line, circle (JANGAN foreignObject)

Aturan:
  - Output HANYA tag <svg>...</svg> tanpa markdown, tanpa teks lain
  - Hanya gunakan data dari dokumen yang diberikan
  - Semua teks dalam bahasa Indonesia
"""

USER_PROMPT = """\
Dokumen: "{judul}"

Isi:
---
{konten}
---

Hasilkan infografis SVG 960x540. Output hanya <svg>...</svg>.
"""


def _get_doc_text(db: Session, document_id: int, max_chars: int = 9000) -> str:
    chunks = (
        db.query(KemhanDocChunk)
          .filter(KemhanDocChunk.doc_id == document_id)
          .order_by(KemhanDocChunk.chunk_index.asc())
          .all()
    )
    parts, total = [], 0
    for ch in chunks:
        text = ch.chunk_text or ""
        if total + len(text) > max_chars:
            sisa = max_chars - total
            if sisa > 100:
                parts.append(text[:sisa])
            break
        parts.append(text)
        total += len(text)
    return "\n\n".join(parts)


@router.post("/generate")
async def generate_infografis(
    payload: InfografisRequest,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """Generate infografis SVG dari dokumen. Butuh Bearer JWT admin."""
    doc = db.query(KemhanDocument).filter(KemhanDocument.id == payload.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    if doc.status != "ready":
        raise HTTPException(status_code=400, detail=f"Dokumen belum siap (status: {doc.status})")

    konten = _get_doc_text(db, payload.document_id)
    if not konten.strip():
        raise HTTPException(status_code=400, detail="Dokumen tidak memiliki konten teks yang cukup")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": USER_PROMPT.format(judul=doc.judul, konten=konten)},
    ]

    raw = await call_llm(messages)
    raw = raw.strip()

    # Strip markdown fence jika ada
    if raw.startswith("```"):
        lines   = raw.split("\n")
        end_idx = next((i for i in range(len(lines) - 1, 0, -1) if lines[i].strip() == "```"), len(lines))
        raw     = "\n".join(lines[1:end_idx]).strip()

    # Ekstrak <svg>...</svg>
    start = raw.find("<svg")
    end   = raw.lower().rfind("</svg>")
    svg   = raw[start:end + len("</svg>")] if start != -1 and end > start else raw

    return {"judul_dokumen": doc.judul, "svg": svg}
