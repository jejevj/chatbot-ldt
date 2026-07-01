"""
Public FAQ endpoint v2
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.v2.database import KemhanFAQ
from app.v2.schemas import FAQResponse

router = APIRouter(prefix="/faq", tags=["faq-v2"])


@router.get("", response_model=List[FAQResponse])
async def list_faq(
    kategori: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Ambil daftar FAQ aktif. Filter opsional berdasarkan kategori."""
    query = db.query(KemhanFAQ).filter(KemhanFAQ.is_active == True)
    if kategori:
        query = query.filter(KemhanFAQ.kategori == kategori)
    return query.order_by(KemhanFAQ.created_at.desc()).all()
