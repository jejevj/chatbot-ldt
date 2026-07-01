"""
Admin Infografis API — generate SVG dari dokumen rujukan (beta)

Flow:
  1. Ambil konten teks dokumen dari t_kemhan_doc_chunks
  2. Panggil LLM dengan prompt khusus infografis SVG
  3. Normalisasi output (strip markdown fence jika ada)
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


SYSTEM = """\
Kamu adalah perancang infografis berbasis SVG untuk dokumen resmi pemerintah Indonesia.
Tugasmu:
  1. Membaca isi dokumen yang diberikan secara menyeluruh.
  2. Menyimpulkan data dan poin penting yang cocok divisualisasikan:
     - angka (jumlah, persentase, anggaran, tahun)
     - tanggal atau periode penting
     - nama program, kebijakan, atau unit organisasi
     - struktur atau hierarki jika ada
  3. Menghasilkan KODE SVG MURNI untuk infografis.

Spesifikasi SVG:
  - Width: 960, Height: 540 (rasio 16:9)
  - Tema: latar belakang gelap (#1a1a2e atau serupa), aksen emas/amber (#f59e0b), teks putih
  - Font: font-family sans-serif
  - Struktur: header judul, subjudul/ringkasan, 3-6 kartu/panel berisi data utama
  - Gunakan <rect>, <text>, <line>, <circle> — jangan gunakan foreignObject

Aturan WAJIB:
  - Output HANYA tag <svg>...</svg>, tanpa markdown, tanpa penjelasan lain
  - Jangan gunakan data di luar dokumen yang diberikan
  - Semua teks harus dalam bahasa Indonesia
"""

USER_TEMPLATE = """\
Dokumen: "{judul}"

Isi dokumen:
---
{konten}
---

Buat infografis SVG 960x540 dari dokumen di atas.
Output hanya berupa tag <svg>...</svg>, tanpa teks atau markdown lain.
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
            remaining = max_chars - total
            if remaining > 100:
                parts.append(text[:remaining])
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
        raise HTTPException(
            status_code=400,
            detail=f"Dokumen belum siap (status: {doc.status}). Tunggu proses selesai."
        )

    konten = _get_doc_text(db, payload.document_id)
    if not konten.strip():
        raise HTTPException(
            status_code=400,
            detail="Dokumen tidak memiliki konten teks yang cukup untuk infografis."
        )

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user",   "content": USER_TEMPLATE.format(judul=doc.judul, konten=konten)},
    ]

    raw = (await call_llm(messages, temperature=0.4)).strip()

    # Strip markdown fence jika ada: ```svg ... ``` atau ``` ... ```
    if raw.startswith("```"):
        lines = raw.split("\n")
        end_idx = next((i for i in range(len(lines) - 1, 0, -1) if lines[i].strip() == "```"), len(lines))
        raw = "\n".join(lines[1:end_idx]).strip()

    # Ambil substring <svg>...</svg>
    start = raw.find("<svg")
    end   = raw.lower().rfind("</svg>")
    if start != -1 and end != -1 and end > start:
        svg = raw[start:end + len("</svg>")]
    else:
        svg = raw  # fallback

    return {"judul_dokumen": doc.judul, "svg": svg}
