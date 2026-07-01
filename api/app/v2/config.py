"""
V2 Configuration — inherits base settings, adds v2-specific settings
"""
from app.config import Settings as BaseSettings
from typing import Optional


class V2Settings(BaseSettings):
    # Admin
    ADMIN_SECRET_KEY: str = "changeme-admin-secret"

    # Upload
    UPLOAD_DIR: str = "uploads/kemhan"
    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: list = ["pdf", "docx", "txt"]

    # RAG v2
    V2_SEARCH_LIMIT: int = 5
    V2_CHUNK_SIZE: int = 512
    V2_CHUNK_OVERLAP: int = 64
    V2_EMBEDDING_THRESHOLD: float = 1.2

    # Assistant identity
    V2_ASSISTANT_NAME: str = "Asisten Informasi Kemhan"
    V2_ASSISTANT_SCOPE: str = "Kementerian Pertahanan Republik Indonesia"

    class Config:
        env_file = ".env"
        case_sensitive = True


v2_settings = V2Settings()
