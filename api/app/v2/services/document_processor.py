"""
Document processor — parse PDF/DOCX/TXT dan chunk teks
"""
import os
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


def _chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    """Potong teks menjadi chunks dengan overlap"""
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


def parse_pdf(filepath: str) -> str:
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except ImportError:
        logger.warning("PyMuPDF tidak tersedia, mencoba pypdf")
        try:
            from pypdf import PdfReader
            reader = PdfReader(filepath)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            raise RuntimeError("Install PyMuPDF atau pypdf untuk membaca PDF")


def parse_docx(filepath: str) -> str:
    try:
        from docx import Document
        doc = Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        raise RuntimeError("Install python-docx untuk membaca DOCX")


def process_document(filepath: str, chunk_size: int = 512, overlap: int = 64) -> Tuple[str, List[str]]:
    """
    Parse dokumen dan kembalikan (full_text, list_of_chunks).
    Deteksi format berdasarkan ekstensi file.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        text = parse_pdf(filepath)
    elif ext == ".docx":
        text = parse_docx(filepath)
    elif ext == ".txt":
        text = parse_txt(filepath)
    else:
        raise ValueError(f"Format tidak didukung: {ext}")

    chunks = _chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    logger.info(f"Dokumen {filepath} → {len(chunks)} chunks")
    return text, chunks
