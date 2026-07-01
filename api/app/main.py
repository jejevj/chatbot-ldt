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
from app.api.docs_auth import register_protected_docs
from app.scheduler import start_scheduler, stop_scheduler

# V2 router
from app.v2.router import v2_router
from app.v2.database import init_v2_tables

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
    ## Retrieval-Augmented Generation API

    ### V1 — Data Terbuka Indonesia
    * Pencarian data terbuka
    * Chat berbasis RAG dataset

    ### V2 — Kemhan Chatbot
    * Upload dokumen rujukan (PDF/DOCX/TXT)
    * Tanya jawab seputar Kemhan & regulasi
    * FAQ management
    * Feedback & training koreksi jawaban AI
    """,
    version="2.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    },
    root_path="/chatbot-api",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

register_protected_docs(app)

# ── Startup ────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """Start background scheduler dan inisialisasi tabel v2"""
    logger.info("Starting application...")

    # Init tabel v2
    try:
        init_v2_tables()
        logger.info("V2 tables initialized")
    except Exception as e:
        logger.warning(f"Could not initialize v2 tables: {e}")

    # Check embeddings v1
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

    start_scheduler()
    logger.info("Starting RAG Chatbot API...")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1]}")
    logger.info(f"Qwen: {settings.QWEN_API_URL}")
    logger.info(f"Embeddings: {'enabled' if settings.USE_EMBEDDINGS else 'disabled'}")
    if settings.MAINTENANCE_MODE:
        logger.warning(f"\u26a0\ufe0f  MAINTENANCE MODE ENABLED: {settings.MAINTENANCE_MESSAGE}")


# ── Shutdown ───────────────────────────────────────────────────────────────
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")
    stop_scheduler()


# ── Middleware ─────────────────────────────────────────────────────────────
@app.middleware("http")
async def maintenance_mode_middleware(request: Request, call_next):
    if settings.MAINTENANCE_MODE and request.url.path not in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": settings.MAINTENANCE_MESSAGE,
                "eta": settings.MAINTENANCE_ETA,
                "status": "maintenance"
            }
        )
    return await call_next(request)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    if settings.TRUST_PROXY_HEADERS:
        forwarded_proto = request.headers.get("X-Forwarded-Proto", "http")
        if forwarded_proto == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── V1 Routers ─────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(sessions.router)
app.include_router(device.router)
app.include_router(data.router)

# ── V2 Routers (prefix /v2) ────────────────────────────────────────────────
app.include_router(v2_router, prefix="/v2")


# ── Root ───────────────────────────────────────────────────────────────────
@app.get("/", tags=["root"])
async def root():
    return {
        "message": "RAG Chatbot API",
        "version": "2.0.0",
        "v1": "/chatbot-api/",
        "v2": "/chatbot-api/v2/",
        "docs": "/docs",
        "health_v1": "/health",
        "health_v2": "/v2/health",
        "maintenance": settings.MAINTENANCE_MODE,
    }
