"""
Public chat endpoint v2 — tanya jawab berbasis RAG Kemhan
"""
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.v2.schemas import ChatRequest, ChatResponse, SessionHistoryResponse, MessageResponse
from app.v2.database import KemhanChatSession, KemhanChatMessage
from app.v2.services.rag_service import answer_question
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat-v2"])


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """Kirim pertanyaan dan dapatkan jawaban dari AI Kemhan"""
    session_id = req.session_id or str(uuid.uuid4())

    # Pastikan session ada
    session = db.query(KemhanChatSession).filter(
        KemhanChatSession.session_id == session_id
    ).first()
    if not session:
        session = KemhanChatSession(
            session_id=session_id,
            device_id=req.device_id,
            title=req.message[:80],
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # Simpan pesan user
    user_msg = KemhanChatMessage(
        session_id=session_id,
        role="user",
        content=req.message,
    )
    db.add(user_msg)
    db.commit()

    # RAG
    try:
        answer, sources = await answer_question(db, req.message)
    except Exception as e:
        logger.error(f"RAG error: {e}")
        raise HTTPException(status_code=500, detail="Terjadi kesalahan saat memproses pertanyaan")

    # Simpan jawaban AI
    ai_msg = KemhanChatMessage(
        session_id=session_id,
        role="assistant",
        content=answer,
        sources=[s.model_dump() for s in sources],
    )
    db.add(ai_msg)
    db.commit()

    return ChatResponse(
        session_id=session_id,
        answer=answer,
        sources=sources,
        model=settings.QWEN_MODEL,
    )


@router.get("/sessions/{session_id}", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str, db: Session = Depends(get_db)):
    """Ambil riwayat percakapan berdasarkan session_id"""
    session = db.query(KemhanChatSession).filter(
        KemhanChatSession.session_id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session tidak ditemukan")

    messages = db.query(KemhanChatMessage).filter(
        KemhanChatMessage.session_id == session_id
    ).order_by(KemhanChatMessage.created_at.asc()).all()

    return SessionHistoryResponse(
        session_id=session.session_id,
        title=session.title,
        messages=[MessageResponse.model_validate(m) for m in messages],
        created_at=session.created_at,
    )
