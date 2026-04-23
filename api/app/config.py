"""
Application configuration
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:qwert12345!@127.0.0.1:5433/satu_data_db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    
    # Qwen3 LLM
    QWEN_API_URL: str = "http://localhost:9002/v1/chat/completions"
    QWEN_MODEL: str = "Qwen/Qwen2.5-7B-Instruct-AWQ"
    QWEN_TIMEOUT: int = 120
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    API_RELOAD: bool = True
    
    # CORS
    CORS_ORIGINS: list = ["*"]  # Allow all origins
    FORCE_HTTPS: bool = False  # Let HAProxy handle HTTPS redirect
    TRUST_PROXY_HEADERS: bool = True  # Trust X-Forwarded-* headers from HAProxy
    
    # Search
    SEARCH_LIMIT: int = 5
    EMBEDDING_THRESHOLD: float = 0.7
    USE_EMBEDDINGS: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/api.log"
    
    # Session
    SESSION_EXPIRY_DAYS: int = 30
    MAX_MESSAGES_PER_SESSION: int = 100
    CHAT_HISTORY_LIMIT: int = 10  # Number of previous messages to include in context
    
    # AI Assistant Configuration
    ASSISTANT_NAME: str = "Asisten Satu Data Pertahanan"
    ASSISTANT_SCOPE: str = "Kementerian Pertahanan Republik Indonesia"
    ASSISTANT_GREETING_STYLE: str = "singkat"  # singkat, formal, ramah
    
    # Maintenance Mode
    MAINTENANCE_MODE: bool = False
    MAINTENANCE_MESSAGE: str = "Sistem sedang dalam pemeliharaan untuk meningkatkan kualitas layanan"
    MAINTENANCE_ETA: Optional[str] = None  # e.g., "2 jam" or "23:00 WIB"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
