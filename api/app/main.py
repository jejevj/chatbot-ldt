"""
Main FastAPI application
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys

from app.config import settings
from app.api.routes import chat, sessions, device, data, health
from app.scheduler import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RAG Chatbot API",
    description="""
    ## Retrieval-Augmented Generation API untuk Data Terbuka Indonesia
    
    API ini menyediakan chatbot berbasis RAG yang dapat:
    * 🔍 Mencari data terbuka Indonesia
    * 💬 Menjawab pertanyaan dengan konteks
    * 📚 Menyimpan riwayat percakapan
    * 🔐 Autentikasi berbasis device fingerprint
    
    ### Features
    * **Smart Search**: Keyword-based dan vector similarity search
    * **Chat History**: Per-device session management
    * **Context-Aware**: Mengingat percakapan sebelumnya
    * **Real-time**: Streaming responses (coming soon)
    
    ### Tech Stack
    * FastAPI + PostgreSQL + pgvector
    * Qwen3 LLM untuk generation
    * Sentence Transformers untuk embeddings
    """,
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    },
    root_path="/chatbot-api"
)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Start background scheduler on app startup"""
    logger.info("Starting application...")
    
    # Check if embeddings exist, generate if not
    try:
        from app.database import SessionLocal, DataEmbedding
        db = SessionLocal()
        embedding_count = db.query(DataEmbedding).count()
        db.close()
        
        if embedding_count == 0:
            logger.info("No embeddings found, generating initial embeddings...")
            import subprocess
            subprocess.run(["python", "scripts/generate_embeddings.py"], check=True)
            logger.info("Initial embeddings generated successfully")
        else:
            logger.info(f"Found {embedding_count} existing embeddings")
    except Exception as e:
        logger.warning(f"Could not check/generate embeddings: {str(e)}")
    
    # Start scheduler for periodic updates
    start_scheduler()

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Stop background scheduler on app shutdown"""
    logger.info("Shutting down application...")
    stop_scheduler()

# Maintenance mode middleware
@app.middleware("http")
async def maintenance_mode_middleware(request: Request, call_next):
    """Check if maintenance mode is enabled"""
    # Allow health check and root endpoint during maintenance
    if settings.MAINTENANCE_MODE and request.url.path not in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": settings.MAINTENANCE_MESSAGE,
                "eta": settings.MAINTENANCE_ETA,
                "status": "maintenance"
            }
        )
    
    response = await call_next(request)
    return response

# Security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers"""
    response = await call_next(request)
    
    # Check if request came through HTTPS (from HAProxy)
    if settings.TRUST_PROXY_HEADERS:
        forwarded_proto = request.headers.get("X-Forwarded-Proto", "http")
        if forwarded_proto == "https":
            # Add HSTS header only for HTTPS requests
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(sessions.router)
app.include_router(device.router)
app.include_router(data.router)

@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("Starting RAG Chatbot API...")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1]}")
    logger.info(f"Qwen3: {settings.QWEN_API_URL}")
    logger.info(f"Embeddings: {'enabled' if settings.USE_EMBEDDINGS else 'disabled'}")
    if settings.MAINTENANCE_MODE:
        logger.warning(f"⚠️  MAINTENANCE MODE ENABLED: {settings.MAINTENANCE_MESSAGE}")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    logger.info("Shutting down RAG Chatbot API...")

@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint - API information
    
    Returns basic API information and links to documentation.
    """
    return {
        "message": "RAG Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "maintenance": settings.MAINTENANCE_MODE
    }
