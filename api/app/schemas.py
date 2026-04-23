"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime


class ChatRequest(BaseModel):
    """Simple chat request"""
    pertanyaan: str = Field(..., min_length=1, max_length=500)
    kategori: Optional[str] = None
    tipe: Optional[str] = None
    
    @validator('pertanyaan')
    def sanitize_input(cls, v):
        return v.strip()


class ChatResponse(BaseModel):
    """Chat response with sources"""
    jawaban: str
    sumber: List[dict]


class ChatHistoryRequest(BaseModel):
    """Chat request with session support"""
    session_id: Optional[str] = None
    pertanyaan: str = Field(..., min_length=1, max_length=500)
    kategori: Optional[str] = None
    tipe: Optional[str] = None
    
    @validator('pertanyaan')
    def sanitize_input(cls, v):
        return v.strip()


class ChatHistoryResponse(BaseModel):
    """Chat response with session ID"""
    session_id: str
    jawaban: str
    sumber: List[dict]


class DeviceRegisterRequest(BaseModel):
    """Device registration request"""
    device_fingerprint: str = Field(..., min_length=32, max_length=256)


class DeviceRegisterResponse(BaseModel):
    """Device registration response"""
    device_id: str
    message: str


class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    title: str
    created_at: Optional[str]
    updated_at: Optional[str]


class MessageInfo(BaseModel):
    """Message information"""
    id: int
    role: str
    content: str
    sources: List[dict]
    created_at: Optional[str]


class SessionDetail(BaseModel):
    """Session with messages"""
    session_id: str
    title: str
    created_at: Optional[str]
    updated_at: Optional[str]
    messages: List[MessageInfo]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    database: str
    qwen3: str
    embeddings: Optional[str] = None


class OpenAIMessage(BaseModel):
    """OpenAI-compatible message"""
    role: str
    content: str


class OpenAIChatRequest(BaseModel):
    """OpenAI-compatible chat request"""
    model: str = "rag-data-terbuka"
    messages: List[OpenAIMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 800
