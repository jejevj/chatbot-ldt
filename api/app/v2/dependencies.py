"""
Dependencies v2 — admin authentication via Bearer JWT
"""
from fastapi import Header, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
import os
import logging

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=True)


def get_db():
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """
    Dependency: validasi Bearer JWT dari endpoint POST /v2/admin/login.
    Gantikan require_admin lama yang pakai X-Admin-Key header.
    """
    from app.v2.config import v2_settings

    SECRET_KEY = os.getenv("JWT_SECRET_KEY", v2_settings.ADMIN_SECRET_KEY)
    ALGORITHM  = "HS256"

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        role: str     = payload.get("role")
        if not username or role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akses ditolak: bukan admin",
            )
        # Verifikasi user masih ada & aktif di DB
        from app.v2.api.routes.admin_auth import AppUser
        user = db.query(AppUser).filter(AppUser.username_user == username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User tidak ditemukan",
            )
        if not user.status_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akun tidak aktif",
            )
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sudah kadaluarsa, silakan login kembali",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid",
            headers={"WWW-Authenticate": "Bearer"},
        )
