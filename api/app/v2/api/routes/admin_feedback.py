"""
Admin — kelola koreksi jawaban AI (feedback training)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List
from app.database import get_db
from app.v2.dependencies import require_admin
from app.v2.database import KemhanFeedback
from app.v2.schemas import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/admin/feedback", tags=["admin-feedback"])


@router.post("", response_model=FeedbackResponse, dependencies=[Depends(require_admin)])
async def create_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)):
    """Admin submit koreksi jawaban AI"""
    fb = KemhanFeedback(**payload.model_dump())
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb


@router.get("", response_model=List[FeedbackResponse], dependencies=[Depends(require_admin)])
async def list_feedback(db: Session = Depends(get_db)):
    """List semua feedback koreksi"""
    return db.query(KemhanFeedback).order_by(KemhanFeedback.created_at.desc()).all()


@router.post("/{feedback_id}/apply", response_model=FeedbackResponse, dependencies=[Depends(require_admin)])
async def apply_feedback(feedback_id: int, db: Session = Depends(get_db)):
    """
    Terapkan koreksi sebagai ground truth.
    Setelah di-apply, jawaban koreksi ini akan dipakai sebagai referensi
    prioritas tertinggi dalam RAG pipeline.
    """
    fb = db.query(KemhanFeedback).filter(KemhanFeedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback tidak ditemukan")
    if fb.status == "applied":
        raise HTTPException(status_code=400, detail="Feedback sudah diterapkan sebelumnya")

    fb.status = "applied"
    fb.applied_at = func.now()
    db.commit()
    db.refresh(fb)
    return fb


@router.delete("/{feedback_id}", dependencies=[Depends(require_admin)])
async def delete_feedback(feedback_id: int, db: Session = Depends(get_db)):
    """Hapus feedback"""
    fb = db.query(KemhanFeedback).filter(KemhanFeedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback tidak ditemukan")
    db.delete(fb)
    db.commit()
    return {"message": "Feedback berhasil dihapus"}
