"""
Health check endpoint
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import httpx
import logging

from app.database import get_db, DataEmbedding
from app.config import settings
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "qwen3": "unknown",
        "embeddings": "unknown"
    }
    
    # Test database
    try:
        result = db.execute(text("SELECT COUNT(*) FROM v_detail_data_terbuka"))
        count = result.scalar()
        health_status["database"] = f"connected ({count} records)"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Test Qwen3
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.QWEN_API_URL.replace('/v1/chat/completions', '/v1/models')}"
            )
            if response.status_code == 200:
                health_status["qwen3"] = "connected"
            else:
                health_status["qwen3"] = f"error: status {response.status_code}"
    except Exception as e:
        health_status["qwen3"] = f"error: {str(e)}"
    
    # Test embeddings
    if DataEmbedding:
        try:
            count = db.query(DataEmbedding).count()
            health_status["embeddings"] = f"available ({count} embeddings)"
        except:
            health_status["embeddings"] = "not configured"
    else:
        health_status["embeddings"] = "not available"
    
    return HealthResponse(**health_status)
