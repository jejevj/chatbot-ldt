from fastapi import APIRouter

from app.v2.api.routes import admin_auth, admin_documents, admin_faq, admin_feedback, chat, faq, health, admin_infografis

api_router = APIRouter(prefix="/v2")

api_router.include_router(admin_auth.router)
api_router.include_router(admin_documents.router)
api_router.include_router(admin_faq.router)
api_router.include_router(admin_feedback.router)
api_router.include_router(admin_infografis.router)
api_router.include_router(chat.router)
api_router.include_router(faq.router)
api_router.include_router(health.router)
