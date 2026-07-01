"""
Admin — manajemen dokumen rujukan
"""
import os
import uuid
import logging
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.v2.dependencies import require_admin
from app.v2.config import v2_settings
from app.v2.database import KemhanDocument, KemhanDocChunk, KemhanEmbedding
from app.v2.schemas import DocumentResponse
from app.v2.services.document_processor import process_document
from app.v2.services.embedding_service import embed_texts

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/documents", tags=["admin-documents"])


def _process_and_embed(doc_id: int, filepath: str, db_url: str):
    """Background task: parse dokumen, chunking, generate embedding, simpan ke DB"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.v2.database import KemhanDocument, KemhanDocChunk, KemhanEmbedding

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        doc = db.query(KemhanDocument).filter(KemhanDocument.id == doc_id).first()
        if not doc:
            return

        _, chunks = process_document(
            filepath,
            chunk_size=v2_settings.V2_CHUNK_SIZE,
            overlap=v2_settings.V2_CHUNK_OVERLAP,
        )

        # Simpan chunks
        chunk_objs = []
        for i, chunk_text in enumerate(chunks):
            c = KemhanDocChunk(
                doc_id=doc_id,
                chunk_index=i,
                chunk_text=chunk_text,
                token_count=len(chunk_text.split()),
            )
            db.add(c)
            chunk_objs.append(c)
        db.commit()
        for c in chunk_objs:
            db.refresh(c)

        # Generate embeddings
        if KemhanEmbedding is not None:
            texts = [c.chunk_text for c in chunk_objs]
            vectors = embed_texts(texts)
            for c, vec in zip(chunk_objs, vectors):
                emb = KemhanEmbedding(chunk_id=c.id, embedding=vec)
                db.add(emb)
            db.commit()

        doc.status = "ready"
        doc.total_chunks = len(chunks)
        db.commit()
        logger.info(f"Document {doc_id} processed: {len(chunks)} chunks")
    except Exception as e:
        logger.error(f"Error processing document {doc_id}: {e}")
        doc = db.query(KemhanDocument).filter(KemhanDocument.id == doc_id).first()
        if doc:
            doc.status = "error"
            doc.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.post("", response_model=DocumentResponse, dependencies=[Depends(require_admin)])
async def upload_document(
    background_tasks: BackgroundTasks,
    judul: str = Form(...),
    tipe: str = Form("umum"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload dokumen rujukan (PDF/DOCX/TXT). Chunking & embedding dilakukan di background."""
    ext = os.path.splitext(file.filename)[1].lower().strip(".")
    if ext not in v2_settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Format tidak didukung: .{ext}")

    # Cek ukuran
    content = await file.read()
    if len(content) > v2_settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File terlalu besar (max {v2_settings.MAX_UPLOAD_SIZE_MB}MB)")

    # Simpan file
    os.makedirs(v2_settings.UPLOAD_DIR, exist_ok=True)
    safe_filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(v2_settings.UPLOAD_DIR, safe_filename)
    with open(filepath, "wb") as f:
        f.write(content)

    # Simpan metadata ke DB
    doc = KemhanDocument(
        judul=judul,
        filename=file.filename,
        filepath=filepath,
        tipe=tipe,
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Proses di background
    background_tasks.add_task(_process_and_embed, doc.id, filepath, v2_settings.DATABASE_URL)

    return doc


@router.get("", response_model=List[DocumentResponse], dependencies=[Depends(require_admin)])
async def list_documents(db: Session = Depends(get_db)):
    """List semua dokumen yang sudah diupload"""
    return db.query(KemhanDocument).order_by(KemhanDocument.uploaded_at.desc()).all()


@router.delete("/{doc_id}", dependencies=[Depends(require_admin)])
async def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """Hapus dokumen beserta semua chunk dan embedding-nya"""
    doc = db.query(KemhanDocument).filter(KemhanDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")

    # Hapus file fisik
    if os.path.exists(doc.filepath):
        os.remove(doc.filepath)

    db.delete(doc)  # cascade akan hapus chunks + embeddings
    db.commit()
    return {"message": f"Dokumen '{doc.judul}' berhasil dihapus"}
