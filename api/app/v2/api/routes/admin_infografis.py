"""
Admin Infografis API — generate SVG dari dokumen rujukan (beta)

Flow:
  1. Ambil konten teks dokumen (chunk PGVector sama seperti RAG)
  2. Panggil LLM dengan prompt khusus untuk menyusun struktur infografis
     - judul utama
     - ringkasan singkat
     - poin-poin data yang penting (angka, tanggal, entitas)
  3. LLM mengembalikan kode SVG murni (tanpa markdown)
  4. API mengembalikan JSON: { judul_dokumen, svg }
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.v2.dependencies import require_admin
from app.v2.database import KemhanDocument, KemhanDocChunk
from app.v2.services.llm_service import call_llm

router = APIRouter(prefix="/admin/infografis", tags=["admin-infografis"])

SYSTEM = """\
Kamu adalah perancang infografis berbasis SVG untuk dokumen resmi.
Tugasmu:
  1. Membaca isi dokumen yang diberikan.
  2. Menyimpulkan data dan poin penting yang cocok divisualisasikan:
     - angka (jumlah, persentase, tahun)
     - tanggal penting
     - nama program/kebijakan
  3. Menghasilkan KODE SVG MURNI untuk infografis dengan tema gelap (dark) dan aksen emas.

Aturan penting:
  - Output HARUS berupa tag <svg> lengkap, tanpa penjelasan tambahan.
  - Jangan mengandung markdown, komentar, atau teks di luar <svg>.
  - Jangan menarik data dari luar dokumen; gunakan hanya informasi dalam konteks.
  - Gunakan ukuran lebar 960px dan tinggi 540px (rasio 16:9).
"""

USER_TEMPLATE = """\
Dokumen: "{judul}"

Isi dokumen:
---
{konten}
---

Buat satu infografis SVG dengan struktur:
  - Header judul di bagian atas.
  - Subjudul/ringkasan singkat di bawah judul.
  - 3–6 kartu/panel berisi data utama (angka/tanggal/poin penting).
Gunakan font sans-serif yang bersih dan mudah dibaca.
Tema warna: latar belakang gelap, aksen emas/amber, teks putih.

Output hanya berupa tag <svg> tanpa markdown dan tanpa teks lain.
"""


def _get_doc_text(db: Session, document_id: int, max_chars: int = 9000) -> str:
  chunks = (
    db.query(KemhanDocChunk)
      .filter(KemhanDocChunk.doc_id == document_id)
      .order_by(KemhanDocChunk.chunk_index.asc())
      .all()
  )
  parts = []
  total = 0
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
async def generate_infografis(document_id: int, db: Session = Depends(get_db), admin = Depends(require_admin)):
  doc = db.query(KemhanDocument).filter(KemhanDocument.id == document_id).first()
  if not doc:
    raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
  if doc.status != "ready":
    raise HTTPException(status_code=400, detail=f"Dokumen belum siap (status: {doc.status})")

  konten = _get_doc_text(db, document_id)
  if not konten.strip():
    raise HTTPException(status_code=400, detail="Dokumen tidak memiliki konten teks yang cukup untuk infografis")

  messages = [
    {"role": "system", "content": SYSTEM},
    {
      "role": "user",
      "content": USER_TEMPLATE.format(judul=doc.judul, konten=konten),
    },
  ]

  raw = await call_llm(messages, temperature=0.4)
  raw = raw.strip()

  # Jika LLM membungkus dengan markdown ```svg ...```, strip dulu
  if raw.startswith("```"):
    lines = raw.split("\n")
    inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
    raw = "\n".join(inner).strip()

  # Ambil substring <svg>...</svg> jika ada teks lain
  start = raw.find("<svg")
  end   = raw.lower().rfind("</svg>")
  if start != -1 and end != -1 and end > start:
    svg = raw[start:end + len("</svg>")]
  else:
    svg = raw  # fallback, biarkan apa adanya

  return {
    "judul_dokumen": doc.judul,
    "svg": svg,
  }
