"""
Admin Authentication — Login via tabel app_user
Endpoint: POST /v2/admin/login
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Boolean, SmallInteger, Text, TIMESTAMP
from app.database import Base, SessionLocal
from app.v2.schemas import AdminLoginRequest, AdminLoginResponse
from app.v2.config import v2_settings
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin Auth"])

SECRET_KEY = os.getenv("JWT_SECRET_KEY", v2_settings.ADMIN_SECRET_KEY)
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 8


# ── Model AppUser (reflect tabel existing app_user) ──────────────────────────
class AppUser(Base):
    """Model untuk tabel app_user yang sudah ada di database"""
    __tablename__ = "app_user"
    __table_args__ = {"extend_existing": True}

    id_user             = Column("id_user", Integer, primary_key=True, index=True)
    role_id             = Column(Integer, nullable=True)
    organisasi_id       = Column(Integer, nullable=True)
    nama_user           = Column(String(255), nullable=True)
    username_user       = Column(String(255), unique=True, nullable=True, index=True)
    password_user       = Column(String(255), nullable=True)
    foto_user           = Column(String(255), nullable=True)
    status_user         = Column(Boolean, nullable=False, default=True)
    created_at          = Column(TIMESTAMP, nullable=True)
    updated_at          = Column(TIMESTAMP, nullable=True)
    identitas_user      = Column(String(100), nullable=True)
    telepon_user        = Column(String(100), nullable=True)
    pekerjaan_user      = Column(String(255), nullable=True)
    alamat_user         = Column(Text, nullable=True)
    last_login_user     = Column(TIMESTAMP, nullable=True)
    gagal_password_user = Column(SmallInteger, nullable=True, default=0)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _verify_bcrypt(plain_password: str, hashed: str) -> bool:
    """
    Verifikasi password bcrypt.
    Hash dari PHP menggunakan prefix $2y$, Python menggunakan $2b$.
    Keduanya identik secara algoritma — cukup ganti prefix sebelum verifikasi.
    """
    if hashed.startswith("$2y$"):
        hashed = "$2b$" + hashed[4:]
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as e:
        logger.error(f"bcrypt checkpw error: {e}")
        return False


def _create_token(user: AppUser) -> str:
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {
        "sub":      str(user.id_user),
        "username": user.username_user,
        "role":     "admin",
        "exp":      expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ── POST /v2/admin/login ──────────────────────────────────────────────────────
@router.post(
    "/login",
    response_model=AdminLoginResponse,
    summary="Login Admin",
    description=(
        "Autentikasi admin menggunakan username_user dan password_user "
        "dari tabel app_user. Mengembalikan JWT token."
    ),
)
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    # 1. Cari user berdasarkan username
    user = db.query(AppUser).filter(
        AppUser.username_user == payload.username_user
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
        )

    # 2. Cek status_user aktif
    if not user.status_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun tidak aktif, hubungi administrator",
        )

    # 3. Verifikasi password bcrypt ($2y$ PHP → $2b$ Python)
    if not _verify_bcrypt(payload.password_user, user.password_user or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
        )

    # 4. Generate JWT token
    token = _create_token(user)

    logger.info(f"Admin login success: {user.username_user} (id_user={user.id_user})")

    return AdminLoginResponse(
        token=token,
        token_type="bearer",
        expires_in=TOKEN_EXPIRE_HOURS * 3600,
        user={
            "id_user":     user.id_user,
            "username":    user.username_user,
            "nama_user":   user.nama_user,
            "role_id":     user.role_id,
            "status_user": user.status_user,
        }
    )


# ── Dependency: validasi token untuk endpoint lain ───────────────────────────
def get_current_admin(
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """
    Dependency untuk endpoint yang butuh autentikasi admin via JWT.
    Tambahkan header: Authorization: Bearer <token>
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak ditemukan",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1]
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = data.get("username")
        if not username or data.get("role") != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akses ditolak")
        user = db.query(AppUser).filter(AppUser.username_user == username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User tidak ditemukan")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sudah kadaluarsa")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token tidak valid")
