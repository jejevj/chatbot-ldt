"""
Admin — CRUD FAQ
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.v2.dependencies import require_admin
from app.v2.database import KemhanFAQ
from app.v2.schemas import FAQCreate, FAQUpdate, FAQResponse

router = APIRouter(prefix="/admin/faq", tags=["admin-faq"])


@router.post("", response_model=FAQResponse, dependencies=[Depends(require_admin)])
async def create_faq(payload: FAQCreate, db: Session = Depends(get_db)):
    """Tambah FAQ baru"""
    faq = KemhanFAQ(**payload.model_dump())
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return faq


@router.get("", response_model=List[FAQResponse], dependencies=[Depends(require_admin)])
async def list_faq_admin(db: Session = Depends(get_db)):
    """List semua FAQ termasuk yang nonaktif"""
    return db.query(KemhanFAQ).order_by(KemhanFAQ.created_at.desc()).all()


@router.put("/{faq_id}", response_model=FAQResponse, dependencies=[Depends(require_admin)])
async def update_faq(faq_id: int, payload: FAQUpdate, db: Session = Depends(get_db)):
    """Update FAQ"""
    faq = db.query(KemhanFAQ).filter(KemhanFAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ tidak ditemukan")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(faq, field, value)
    db.commit()
    db.refresh(faq)
    return faq


@router.delete("/{faq_id}", dependencies=[Depends(require_admin)])
async def delete_faq(faq_id: int, db: Session = Depends(get_db)):
    """Hapus FAQ"""
    faq = db.query(KemhanFAQ).filter(KemhanFAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ tidak ditemukan")
    db.delete(faq)
    db.commit()
    return {"message": "FAQ berhasil dihapus"}
