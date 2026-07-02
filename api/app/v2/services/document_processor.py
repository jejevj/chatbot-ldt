"""
Document processor — parse PDF/DOCX/TXT, OCR fallback via EasyOCR server, lalu chunk teks.

Alur untuk PDF:
  1. Baca teks native per halaman via PyMuPDF
  2. Halaman dengan teks < OCR_MIN_TEXT_LEN karakter → kirim ke OCR server (port 9003)
  3. Gabungkan semua teks → chunk dengan ukuran V2_CHUNK_SIZE kata

Fallback:
  - Jika OCR server tidak tersedia → pakai teks native saja (log warning)
  - Jika halaman benar-benar kosong setelah OCR → skip
"""
import os
import io
import logging
import httpx
from typing import List, Tuple

logger = logging.getLogger(__name__)


def _chunk_text(text: str, chunk_size: int = 256, overlap: int = 48) -> List[str]:
    """Potong teks menjadi chunks berdasarkan jumlah kata dengan overlap."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap
    return chunks


def parse_txt(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def parse_docx(filepath: str) -> str:
    try:
        from docx import Document
        doc = Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        raise RuntimeError("Install python-docx untuk membaca DOCX")


def _ocr_available(ocr_url: str, timeout: int = 5) -> bool:
    """Cek apakah OCR server aktif."""
    try:
        r = httpx.get(f"{ocr_url}/health", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def _ocr_pdf_via_server(filepath: str, ocr_url: str, min_text_len: int, timeout: int) -> str:
    """
    Kirim PDF ke OCR server, return full_text hasil gabungan
    teks native + OCR untuk halaman yang kosong/gambar.
    """
    with open(filepath, "rb") as f:
        pdf_bytes = f.read()

    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            f"{ocr_url}/ocr/pdf",
            files={"file": (os.path.basename(filepath), pdf_bytes, "application/pdf")},
            params={"min_text_len": min_text_len},
        )
        response.raise_for_status()
        data = response.json()

    total   = data.get("total_pages", 0)
    ocr_pg  = data.get("ocr_pages", 0)
    native  = data.get("native_pages", 0)
    logger.info(f"OCR selesai: {total} halaman | native={native} | ocr={ocr_pg}")
    return data.get("full_text", "")


def parse_pdf(filepath: str, ocr_url: str = None, min_text_len: int = 50, ocr_timeout: int = 300) -> str:
    """
    Parse PDF:
    - Jika OCR server tersedia → kirim ke server (native + OCR per halaman)
    - Jika tidak → baca teks native saja via PyMuPDF
    """
    try:
        import fitz
    except ImportError:
        raise RuntimeError("Install PyMuPDF (pip install pymupdf)")

    # Coba via OCR server dulu
    if ocr_url and _ocr_available(ocr_url):
        try:
            logger.info(f"Menggunakan OCR server: {ocr_url}")
            text = _ocr_pdf_via_server(filepath, ocr_url, min_text_len, ocr_timeout)
            if text.strip():
                return text
            logger.warning("OCR server return teks kosong, fallback ke native")
        except Exception as e:
            logger.warning(f"OCR server error ({e}), fallback ke native PyMuPDF")

    # Fallback: baca teks native
    logger.info("Membaca PDF dengan PyMuPDF (native text only)")
    doc = fitz.open(filepath)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text().strip()
        if text:
            pages.append(f"[Halaman {i+1}]\n{text}")
        else:
            logger.debug(f"Halaman {i+1} kosong (mungkin gambar/scan, OCR server tidak tersedia)")
    doc.close()
    return "\n\n".join(pages)


def process_document(
    filepath: str,
    chunk_size: int = 256,
    overlap: int = 48,
    ocr_url: str = None,
    ocr_enabled: bool = True,
    min_text_len: int = 50,
    ocr_timeout: int = 300,
) -> Tuple[str, List[str]]:
    """
    Parse dokumen dan kembalikan (full_text, list_of_chunks).
    Deteksi format berdasarkan ekstensi file.
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        effective_ocr_url = ocr_url if ocr_enabled else None
        text = parse_pdf(
            filepath,
            ocr_url=effective_ocr_url,
            min_text_len=min_text_len,
            ocr_timeout=ocr_timeout,
        )
    elif ext == ".docx":
        text = parse_docx(filepath)
    elif ext == ".txt":
        text = parse_txt(filepath)
    else:
        raise ValueError(f"Format tidak didukung: {ext}")

    chunks = _chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    logger.info(f"Dokumen {filepath} → {len(chunks)} chunks (chunk_size={chunk_size}, overlap={overlap})")
    return text, chunks
