"""
Dependencies v2 — admin authentication
"""
from fastapi import Header, HTTPException, status
from app.v2.config import v2_settings
import secrets


async def require_admin(x_admin_key: str = Header(..., alias="X-Admin-Key")):
    """
    Dependency: validasi admin key via header X-Admin-Key.
    Gunakan secrets.compare_digest untuk mencegah timing attack.
    """
    if not secrets.compare_digest(x_admin_key, v2_settings.ADMIN_SECRET_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return True
