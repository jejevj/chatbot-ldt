"""
Admin — kelola koreksi jawaban AI (feedback / ground truth)

Perubahan v2.1:
  - Saat `apply`, otomatis generate dan simpan question_embedding ke DB
    agar RAG service bisa matching via cosine similarity (pgvector).
  - Endpoint baru: POST /admin/feedback/reembed — regenerate embedding
    untuk semua feedback yang question_embedding-nya masih NULL.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List

from app.database import get_db
from app.v2.dependencies import require_admin
from app.v2.database import KemhanFeedback
from app.v2.schemas import FeedbackCreate, FeedbackResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/feedback", tags=["admin-feedback"])


def _embed_question(text: str):
    """Generate embedding 384-dim dari teks pertanyaan. Return None jika gagal."""
    try:
        from app.v2.services.embedding_service import embed_single
        return embed_single(text)
    except Exception as e:
        logger.warning(f"[feedback] Gagal generate embedding: {e}")
        return None


@router.post("", response_model=FeedbackResponse, dependencies=[Depends(require_admin)])
async def create_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)):
    """Admin submit koreksi jawaban AI."""
    fb = KemhanFeedback(**payload.model_dump())
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb


@router.get("", response_model=List[FeedbackResponse], dependencies=[Depends(require_admin)])
async def list_feedback(db: Session = Depends(get_db)):
    """List semua feedback koreksi."""
    return db.query(KemhanFeedback).order_by(KemhanFeedback.created_at.desc()).all()


@router.post(
    "/{feedback_id}/apply",
    response_model=FeedbackResponse,
    dependencies=[Depends(require_admin)],
)
async def apply_feedback(
    feedback_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Terapkan koreksi sebagai ground truth.
    Otomatis generate & simpan question_embedding dari pertanyaan_asli
    agar matching berikutnya bisa via cosine similarity.
    """
    fb = db.query(KemhanFeedback).filter(KemhanFeedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback tidak ditemukan")
    if fb.status == "applied":
        raise HTTPException(status_code=400, detail="Feedback sudah diterapkan sebelumnya")

    fb.status     = "applied"
    fb.applied_at = func.now()
    db.commit()
    db.refresh(fb)

    # Generate embedding di background agar response tetap cepat
    def _save_embedding(fb_id: int, pertanyaan: str):
        from app.database import SessionLocal
        session = SessionLocal()
        try:
            vec = _embed_question(pertanyaan)
            if vec is not None:
                row = session.query(KemhanFeedback).filter(KemhanFeedback.id == fb_id).first()
                if row:
                    row.question_embedding = vec
                    session.commit()
                    logger.info(f"[feedback] Embedding disimpan untuk feedback id={fb_id}")
        except Exception as e:
            logger.error(f"[feedback] Gagal simpan embedding id={fb_id}: {e}")
        finally:
            session.close()

    background_tasks.add_task(_save_embedding, fb.id, fb.pertanyaan_asli)
    return fb


@router.post(
    "/reembed",
    dependencies=[Depends(require_admin)],
    summary="Regenerate embedding untuk semua feedback applied yang belum punya embedding",
)
async def reembed_all(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Jalankan sekali setelah deploy untuk mengisi question_embedding
    pada data feedback lama yang belum punya embedding.
    """
    # Ambil ID feedback applied tanpa embedding
    rows = db.query(KemhanFeedback).filter(
        KemhanFeedback.status == "applied",
        KemhanFeedback.question_embedding == None,  # noqa: E711
    ).all()

    ids_and_qs = [(r.id, r.pertanyaan_asli) for r in rows]
    total = len(ids_and_qs)

    def _batch_embed(items):
        from app.database import SessionLocal
        from app.v2.services.embedding_service import embed_single
        session = SessionLocal()
        success = 0
        try:
            for fb_id, pertanyaan in items:
                try:
                    vec = embed_single(pertanyaan)
                    row = session.query(KemhanFeedback).filter(KemhanFeedback.id == fb_id).first()
                    if row:
                        row.question_embedding = vec
                        success += 1
                except Exception as e:
                    logger.error(f"[reembed] id={fb_id} gagal: {e}")
            session.commit()
            logger.info(f"[reembed] Selesai: {success}/{len(items)} embedding tersimpan")
        finally:
            session.close()

    background_tasks.add_task(_batch_embed, ids_and_qs)
    return {"message": f"Regenerate embedding dimulai untuk {total} feedback di background."}


@router.delete("/{feedback_id}", dependencies=[Depends(require_admin)])
async def delete_feedback(feedback_id: int, db: Session = Depends(get_db)):
    """Hapus feedback."""
    fb = db.query(KemhanFeedback).filter(KemhanFeedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback tidak ditemukan")
    db.delete(fb)
    db.commit()
    return {"message": "Feedback berhasil dihapus"}
