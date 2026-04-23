"""
Database models and connection
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from typing import Generator

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False

from app.config import settings

# Encode password untuk handle karakter khusus
password = quote_plus(settings.DATABASE_URL.split(":")[-1].split("@")[0])
DATABASE_URL = settings.DATABASE_URL

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DataTerbuka(Base):
    """Model untuk view v_detail_data_terbuka"""
    __tablename__ = "v_detail_data_terbuka"
    __table_args__ = {
        'schema': 'public',
        'extend_existing': True,
        'info': {'without_rowid': False}
    }
    
    kode_data = Column(String, primary_key=True)
    url = Column(Text)
    tipe_data = Column(String)
    kategori_data = Column(String)
    sifat_data = Column(String)
    deskripsi_data = Column(Text)
    judul_data = Column(String)


class Device(Base):
    """Model untuk device tracking"""
    __tablename__ = "t_devices"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(255), unique=True, nullable=False, index=True)
    device_fingerprint = Column(Text)
    user_agent = Column(Text)
    last_seen_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)


class ChatSession(Base):
    """Model untuk chat sessions"""
    __tablename__ = "t_chat_sessions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    device_id = Column(String(255), nullable=False, index=True)
    title = Column(String(500))
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)


class ChatMessage(Base):
    """Model untuk chat messages"""
    __tablename__ = "t_chat_messages"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(Text)
    created_at = Column(TIMESTAMP)


if PGVECTOR_AVAILABLE:
    class DataEmbedding(Base):
        """Model untuk embeddings"""
        __tablename__ = "t_data_embeddings"
        __table_args__ = {'extend_existing': True}
        
        id = Column(Integer, primary_key=True, index=True)
        kode_data = Column(String(255), unique=True, nullable=False, index=True)
        embedding = Column(Vector(384))
        text_content = Column(Text)
        created_at = Column(TIMESTAMP)
        updated_at = Column(TIMESTAMP)
else:
    DataEmbedding = None


def get_db() -> Generator:
    """Database dependency"""
    db = SessionLocal()
    try:
        from sqlalchemy import text
        db.execute(text("SET search_path TO public"))
        db.commit()
        yield db
    finally:
        db.close()
