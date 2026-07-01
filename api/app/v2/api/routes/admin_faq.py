"""
Admin — FAQ: CRUD + Generate + Regenerate per dokumen
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.v2.dependencies import require_admin
from app.v2.database import KemhanFAQ, KemhanDocument
from app.v2.schemas import (
    FAQCreate, FAQUpdate, FAQResponse,
    FAQGenerateRequest, FAQGenerateResponse,
)
from app.v2.services.faq_generator import generate_faq_for_document

router = APIRouter(prefix="/admin/faq", tags=["admin-faq"])


# ────────────────────────────────────────────────────────
# LIST FAQ
# ────────────────────────────────────────────────────────
@router.get("", response_model=List[FAQResponse], dependencies=[Depends(require_admin)])
async def list_faq(
    document_id: Optional[int] = Query(None, description="Filter FAQ berdasarkan ID dokumen"),
    db: Session = Depends(get_db),
):
    """List FAQ. Jika document_id diberikan, hanya FAQ milik dokumen itu."""
    q = db.query(KemhanFAQ)
    if document_id is not None:
        q = q.filter(KemhanFAQ.document_id == document_id)
    return q.order_by(KemhanFAQ.created_at.desc()).all()


# ────────────────────────────────────────────────────────
# GENERATE FAQ
# POST /v2/admin/faq/generate   body: { "document_id": 3 }
# ────────────────────────────────────────────────────────
@router.post("/generate", response_model=FAQGenerateResponse, dependencies=[Depends(require_admin)])
async def generate_faq(
    payload: FAQGenerateRequest,
    db: Session = Depends(get_db),
):
    """
    Generate 5 FAQ dari dokumen yang belum punya FAQ.
    Jika sudah ada, gunakan /regenerate.
    """
    existing = db.query(KemhanFAQ).filter(KemhanFAQ.document_id == payload.document_id).count()
    if existing > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Dokumen sudah memiliki {existing} FAQ. Gunakan endpoint /regenerate untuk generate ulang."
        )
    try:
        faqs = await generate_faq_for_document(db, payload.document_id, delete_existing=False)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal generate FAQ: {e}")

    doc = db.query(KemhanDocument).filter(KemhanDocument.id == payload.document_id).first()
    return FAQGenerateResponse(
        document_id=payload.document_id,
        judul_dokumen=doc.judul,
        generated=len(faqs),
        faqs=faqs,
    )


# ────────────────────────────────────────────────────────
# REGENERATE FAQ
# POST /v2/admin/faq/regenerate   body: { "document_id": 3 }
# ────────────────────────────────────────────────────────
@router.post("/regenerate", response_model=FAQGenerateResponse, dependencies=[Depends(require_admin)])
async def regenerate_faq(
    payload: FAQGenerateRequest,
    db: Session = Depends(get_db),
):
    """Hapus semua FAQ lama milik dokumen ini, lalu generate ulang 5 FAQ baru."""
    try:
        faqs = await generate_faq_for_document(db, payload.document_id, delete_existing=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal regenerate FAQ: {e}")

    doc = db.query(KemhanDocument).filter(KemhanDocument.id == payload.document_id).first()
    return FAQGenerateResponse(
        document_id=payload.document_id,
        judul_dokumen=doc.judul,
        generated=len(faqs),
        faqs=faqs,
    )


# ────────────────────────────────────────────────────────
# CRUD MANUAL
# ────────────────────────────────────────────────────────
@router.post("", response_model=FAQResponse, dependencies=[Depends(require_admin)])
async def create_faq(payload: FAQCreate, db: Session = Depends(get_db)):
    """Tambah FAQ manual (tanpa AI)."""
    faq = KemhanFAQ(**payload.model_dump())
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return faq


@router.put("/{faq_id}", response_model=FAQResponse, dependencies=[Depends(require_admin)])
async def update_faq(faq_id: int, payload: FAQUpdate, db: Session = Depends(get_db)):
    """Update FAQ."""
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
    """Hapus satu FAQ."""
    faq = db.query(KemhanFAQ).filter(KemhanFAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ tidak ditemukan")
    db.delete(faq)
    db.commit()
    return {"message": "FAQ berhasil dihapus"}
