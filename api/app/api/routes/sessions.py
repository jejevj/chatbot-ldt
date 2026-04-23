"""
Session management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List
import logging
import json

from app.database import get_db, ChatSession, ChatMessage, Device
from app.schemas import SessionInfo, SessionDetail

router = APIRouter(prefix="/chat/sessions", tags=["sessions"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[SessionInfo])
async def list_sessions(
    device_id: str = Header(..., alias="X-Device-ID"),
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """List all chat sessions for this device"""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=401, detail="Device not registered")
    
    sessions = db.query(ChatSession).filter(
        ChatSession.device_id == device_id
    ).order_by(ChatSession.updated_at.desc()).limit(limit).all()
    
    return [
        SessionInfo(
            session_id=s.session_id,
            title=s.title,
            created_at=s.created_at.isoformat() + 'Z' if s.created_at else None,
            updated_at=s.updated_at.isoformat() + 'Z' if s.updated_at else None
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session_messages(
    session_id: str,
    device_id: str = Header(..., alias="X-Device-ID"),
    db: Session = Depends(get_db)
):
    """Get all messages from a session"""
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.device_id != device_id:
        raise HTTPException(status_code=403, detail="Session does not belong to this device")
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    return SessionDetail(
        session_id=session.session_id,
        title=session.title,
        created_at=session.created_at.isoformat() + 'Z' if session.created_at else None,
        updated_at=session.updated_at.isoformat() + 'Z' if session.updated_at else None,
        messages=[
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "sources": json.loads(m.sources) if m.sources and isinstance(m.sources, str) else (m.sources if m.sources else []),
                "created_at": m.created_at.isoformat() + 'Z' if m.created_at else None  # Add Z to indicate UTC
            }
            for m in messages
        ]
    )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    device_id: str = Header(..., alias="X-Device-ID"),
    db: Session = Depends(get_db)
):
    """Delete a session and all its messages"""
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.device_id != device_id:
        raise HTTPException(status_code=403, detail="Session does not belong to this device")
    
    db.delete(session)
    db.commit()
    
    return {"message": "Session deleted successfully"}


@router.put("/{session_id}/title")
async def update_session_title(
    session_id: str,
    title: str,
    device_id: str = Header(..., alias="X-Device-ID"),
    db: Session = Depends(get_db)
):
    """Update session title"""
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.device_id != device_id:
        raise HTTPException(status_code=403, detail="Session does not belong to this device")
    
    session.title = title
    db.commit()
    
    return {"message": "Title updated successfully", "title": title}
