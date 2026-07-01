"""
Admin Infografis API — generate visualisasi SVG (chart/pie/bar) dari dokumen (beta)

Flow:
  1. Ambil teks dokumen dari KemhanDocChunk
  2. Minta LLM ekstrak data numerik terlebih dahulu (JSON)
  3. Jika tidak ada data numerik -> return pesan "tidak tersedia"
  4. Jika ada -> minta LLM buat SVG chart yang sesuai
  5. Normalisasi output, return JSON: { judul_dokumen, svg, has_data, message }
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import json
import re

from app.database import get_db
from app.v2.dependencies import require_admin
from app.v2.database import KemhanDocument, KemhanDocChunk
from app.v2.services.llm_service import call_llm

router = APIRouter(prefix="/admin/infografis", tags=["admin-infografis"])


class InfografisRequest(BaseModel):
    document_id: int


# Step 1: ekstrak data numerik dari dokumen
EKSTRAK_SYSTEM = """\
Kamu adalah analis data dokumen pemerintah Indonesia.
Tugasmu: cari dan ekstrak SEMUA data numerik yang ada dalam dokumen.

Yang termasuk data numerik:
- Anggaran, biaya, nilai rupiah
- Persentase (%)
- Jumlah personel, unit, satuan
- Tahun + nilai (misal: tahun 2023: 1.200 orang)
- Pasal + angka yang bermakna statistik
- Ranking, indeks, skor
- Apapun yang bisa divisualisasikan sebagai chart/pie/bar

Output wajib JSON dengan format:
{
  "has_data": true atau false,
  "tipe_chart": "pie" | "bar" | "line" | "none",
  "judul_chart": "judul singkat chart",
  "data": [
    {"label": "...", "nilai": 123},
    ...
  ],
  "satuan": "orang" atau "rupiah" atau "%" atau ""
}

Jika sama sekali tidak ada data numerik yang bermakna, output:
{"has_data": false, "tipe_chart": "none", "judul_chart": "", "data": [], "satuan": ""}

OUTPUT HANYA JSON, tanpa markdown, tanpa penjelasan lain.
"""

EKSTRAK_USER = """\
Dokumen: "{judul}"

Isi dokumen:
---
{konten}
---

Ekstrak semua data numerik yang bisa dijadikan chart/pie/bar. Output JSON saja.
"""

# Step 2A: buat pie chart SVG
PIE_SYSTEM = """\
Kamu adalah engineer SVG. Buat pie chart profesional sesuai data yang diberikan.

Spesifikasi:
- width="960" height="540"
- Latar: rect fill="#0f172a" (gelap)
- Judul: text font-family="Arial" font-size="22" fill="#f8fafc" text-anchor="middle" di atas
- Pie chart di tengah-kiri (cx=280, cy=290, radius=180)
- Legend di sebelah kanan (x=520)
- Warna slice: ["#f59e0b","#3b82f6","#10b981","#ef4444","#8b5cf6","#ec4899","#14b8a6"]
- Setiap slice: path dengan arc, label persentase di dalam slice
- Legend: rect 14x14 + text label + nilai
- Sumber/satuan di bawah kanan kecil
- Gunakan elemen SVG murni: path, rect, text, line, circle
- JANGAN foreignObject

Output HANYA tag <svg>...</svg> tanpa markdown apapun.
"""

# Step 2B: buat bar chart SVG
BAR_SYSTEM = """\
Kamu adalah engineer SVG. Buat bar chart profesional sesuai data yang diberikan.

Spesifikasi:
- width="960" height="540"
- Latar: rect fill="#0f172a"
- Judul: text font-size="22" fill="#f8fafc" text-anchor="middle" x="480" y="45"
- Area chart: x=80, y=80, width=820, height=380
- Bar warna amber #f59e0b, hover tidak perlu
- Sumbu X: label di bawah setiap bar (wrap jika panjang, max 12 karakter)
- Sumbu Y: garis horizontal tipis #334155, nilai di kiri
- Nilai di atas setiap bar
- Satuan di pojok kiri bawah
- Gunakan elemen SVG murni: rect, text, line
- JANGAN foreignObject

Output HANYA tag <svg>...</svg> tanpa markdown apapun.
"""

CHART_USER = """\
Buat {tipe_chart} chart SVG dengan data berikut:

Judul: {judul_chart}
Satuan: {satuan}
Data:
{data_str}

Output hanya <svg>...</svg>.
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


def _extract_svg(raw: str) -> str:
    """Ekstrak <svg>...</svg> dari output LLM, strip markdown fence jika ada."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines   = raw.split("\n")
        end_idx = next((i for i in range(len(lines) - 1, 0, -1) if lines[i].strip() == "```"), len(lines))
        raw     = "\n".join(lines[1:end_idx]).strip()
    start = raw.find("<svg")
    end   = raw.lower().rfind("</svg>")
    if start != -1 and end > start:
        return raw[start:end + len("</svg>")]
    return raw


def _extract_json(raw: str) -> dict:
    """Ekstrak JSON dari output LLM."""
    raw = raw.strip()
    # strip markdown fence
    if raw.startswith("```"):
        lines   = raw.split("\n")
        end_idx = next((i for i in range(len(lines) - 1, 0, -1) if lines[i].strip() == "```"), len(lines))
        raw     = "\n".join(lines[1:end_idx]).strip()
    # cari { ... }
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if m:
        return json.loads(m.group())
    return json.loads(raw)


@router.post("/generate")
async def generate_infografis(
    payload: InfografisRequest,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """Generate chart SVG dari dokumen. Jika tidak ada data numerik, return has_data=false."""
    doc = db.query(KemhanDocument).filter(KemhanDocument.id == payload.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    if doc.status != "ready":
        raise HTTPException(status_code=400, detail=f"Dokumen belum siap (status: {doc.status})")

    konten = _get_doc_text(db, payload.document_id)
    if not konten.strip():
        raise HTTPException(status_code=400, detail="Dokumen tidak memiliki konten teks")

    # --- Step 1: ekstrak data numerik ---
    ekstrak_messages = [
        {"role": "system", "content": EKSTRAK_SYSTEM},
        {"role": "user",   "content": EKSTRAK_USER.format(judul=doc.judul, konten=konten)},
    ]
    try:
        raw_json = await call_llm(ekstrak_messages)
        info = _extract_json(raw_json)
    except Exception:
        return {
            "judul_dokumen": doc.judul,
            "has_data": False,
            "svg": "",
            "message": "Gagal menganalisis dokumen. Coba lagi."
        }

    # --- Step 2: jika tidak ada data numerik ---
    if not info.get("has_data") or not info.get("data"):
        return {
            "judul_dokumen": doc.judul,
            "has_data": False,
            "svg": "",
            "message": "Dokumen ini tidak mengandung data numerik yang cukup untuk divisualisasikan sebagai chart atau infografis. Dokumen seperti peraturan, definisi, atau narasi kebijakan tidak memiliki data statistik yang bisa ditampilkan."
        }

    # --- Step 3: buat chart SVG ---
    tipe  = info.get("tipe_chart", "bar")
    data  = info.get("data", [])
    data_str = "\n".join(f"- {d['label']}: {d['nilai']}" for d in data)

    system_prompt = PIE_SYSTEM if tipe == "pie" else BAR_SYSTEM
    chart_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": CHART_USER.format(
            tipe_chart=tipe,
            judul_chart=info.get("judul_chart", doc.judul),
            satuan=info.get("satuan", ""),
            data_str=data_str,
        )},
    ]

    raw_svg = await call_llm(chart_messages)
    svg = _extract_svg(raw_svg)

    return {
        "judul_dokumen": doc.judul,
        "has_data": True,
        "svg": svg,
        "message": f"Chart {tipe} berhasil dibuat dari {len(data)} data poin."
    }
