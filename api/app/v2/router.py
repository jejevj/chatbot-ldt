"""
V2 Router aggregator — semua route v2 dikumpulkan di sini
lalu di-include ke main app dengan prefix /v2
"""
from fastapi import APIRouter
from app.v2.api.routes import health, chat, faq, admin_documents, admin_faq, admin_feedback, admin_auth, admin_infografis

v2_router = APIRouter()

v2_router.include_router(health.router)
v2_router.include_router(chat.router)
v2_router.include_router(faq.router)
v2_router.include_router(admin_documents.router)
v2_router.include_router(admin_faq.router)
v2_router.include_router(admin_feedback.router)
v2_router.include_router(admin_auth.router)
v2_router.include_router(admin_infografis.router)
