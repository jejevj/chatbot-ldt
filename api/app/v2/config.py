"""
V2 Configuration — inherits base settings, adds v2-specific settings
"""
from app.config import Settings as BaseSettings


class V2Settings(BaseSettings):
    # Admin
    ADMIN_SECRET_KEY: str = "changeme-admin-secret"

    # Upload
    UPLOAD_DIR: str = "uploads/kemhan"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list = ["pdf", "docx", "txt"]

    # RAG v2 — chunk lebih kecil agar retrieval lebih presisi per pasal
    V2_SEARCH_LIMIT: int = 5
    V2_CHUNK_SIZE: int = 256
    V2_CHUNK_OVERLAP: int = 48
    V2_EMBEDDING_THRESHOLD: float = 1.2

    # OCR Server (EasyOCR GPU via SSH tunnel)
    OCR_SERVER_URL: str = "http://localhost:9003"
    OCR_ENABLED: bool = True
    OCR_MIN_TEXT_LEN: int = 50   # halaman dengan teks < 50 karakter dianggap perlu OCR
    OCR_TIMEOUT: int = 300       # timeout 5 menit untuk PDF besar

    # Assistant identity
    V2_ASSISTANT_NAME: str = "Asisten Informasi Kemhan"
    V2_ASSISTANT_SCOPE: str = "Kementerian Pertahanan Republik Indonesia"

    class Config:
        env_file = ".env"
        case_sensitive = True


v2_settings = V2Settings()
