"""
V2 Database models — tabel khusus Kemhan chatbot
"""
from sqlalchemy import (
    Column, Integer, String, Text, TIMESTAMP, Boolean, Float, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False

from app.database import Base, engine


class KemhanDocument(Base):
    """Dokumen rujukan yang diupload admin (PDF/DOCX/TXT)"""
    __tablename__ = "t_kemhan_documents"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    judul = Column(String(500), nullable=False)
    filename = Column(String(500), nullable=False)
    filepath = Column(Text, nullable=False)
    tipe = Column(String(50), default="umum")  # regulasi, uu, faq, umum
    status = Column(String(20), default="processing")  # processing, ready, error
    error_message = Column(Text, nullable=True)
    total_chunks = Column(Integer, default=0)
    uploaded_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    chunks = relationship("KemhanDocChunk", back_populates="document", cascade="all, delete-orphan")


class KemhanDocChunk(Base):
    """Potongan teks dari dokumen"""
    __tablename__ = "t_kemhan_doc_chunks"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, ForeignKey("t_kemhan_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())

    document = relationship("KemhanDocument", back_populates="chunks")
    embedding = relationship("KemhanEmbedding", back_populates="chunk", uselist=False, cascade="all, delete-orphan")


class KemhanFAQ(Base):
    """FAQ yang dikelola admin"""
    __tablename__ = "t_kemhan_faq"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    pertanyaan = Column(Text, nullable=False)
    jawaban = Column(Text, nullable=False)
    kategori = Column(String(100), default="umum")
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class KemhanFeedback(Base):
    """Koreksi jawaban AI oleh admin — digunakan sebagai ground truth"""
    __tablename__ = "t_kemhan_feedback"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    pertanyaan_asli = Column(Text, nullable=False)
    jawaban_ai = Column(Text, nullable=False)
    jawaban_koreksi = Column(Text, nullable=False)
    catatan_admin = Column(Text, nullable=True)
    status = Column(String(20), default="pending")  # pending, applied
    applied_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class KemhanChatSession(Base):
    """Sesi percakapan chatbot Kemhan"""
    __tablename__ = "t_kemhan_chat_sessions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    device_id = Column(String(255), nullable=True, index=True)
    title = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    messages = relationship("KemhanChatMessage", back_populates="session", cascade="all, delete-orphan")


class KemhanChatMessage(Base):
    """Pesan dalam sesi percakapan"""
    __tablename__ = "t_kemhan_chat_messages"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("t_kemhan_chat_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    session = relationship("KemhanChatSession", back_populates="messages")


if PGVECTOR_AVAILABLE:
    class KemhanEmbedding(Base):
        """Vector embedding per chunk dokumen"""
        __tablename__ = "t_kemhan_embeddings"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        chunk_id = Column(Integer, ForeignKey("t_kemhan_doc_chunks.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
        embedding = Column(Vector(384))
        created_at = Column(TIMESTAMP, server_default=func.now())

        chunk = relationship("KemhanDocChunk", back_populates="embedding")
else:
    KemhanEmbedding = None


def init_v2_tables():
    """Buat semua tabel v2 jika belum ada"""
    Base.metadata.create_all(bind=engine)
