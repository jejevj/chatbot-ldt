"""
Health check endpoint v2
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter(prefix="/health", tags=["health-v2"])


@router.get("")
async def health_check(db: Session = Depends(get_db)):
    """Health check untuk Kemhan API v2"""
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "version": "2.0.0",
        "service": "Kemhan Chatbot API v2",
        "database": db_status,
    }
