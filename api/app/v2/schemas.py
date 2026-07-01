"""
Pydantic schemas untuk V2 API
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# ── Document ──────────────────────────────────────────────
class DocumentResponse(BaseModel):
    id: int
    judul: str
    filename: str
    tipe: str
    status: str
    total_chunks: int
    uploaded_at: Optional[datetime]
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


# ── FAQ ───────────────────────────────────────────────────
class FAQCreate(BaseModel):
    pertanyaan: str = Field(..., min_length=5)
    jawaban: str = Field(..., min_length=5)
    kategori: str = "umum"
    is_active: bool = True


class FAQUpdate(BaseModel):
    pertanyaan: Optional[str] = None
    jawaban: Optional[str] = None
    kategori: Optional[str] = None
    is_active: Optional[bool] = None


class FAQResponse(BaseModel):
    id: int
    pertanyaan: str
    jawaban: str
    kategori: str
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── Feedback ──────────────────────────────────────────────
class FeedbackCreate(BaseModel):
    pertanyaan_asli: str
    jawaban_ai: str
    jawaban_koreksi: str
    catatan_admin: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    pertanyaan_asli: str
    jawaban_ai: str
    jawaban_koreksi: str
    catatan_admin: Optional[str]
    status: str
    applied_at: Optional[datetime]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── Chat ──────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    device_id: Optional[str] = None


class ChatSource(BaseModel):
    tipe: str  # document, faq, ground_truth
    judul: str
    relevansi: float


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[ChatSource] = []
    model: str


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sources: Optional[Any]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class SessionHistoryResponse(BaseModel):
    session_id: str
    title: Optional[str]
    messages: List[MessageResponse]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
