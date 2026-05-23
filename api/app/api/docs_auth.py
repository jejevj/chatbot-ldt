"""HTTP Basic Auth for Swagger / API documentation endpoints."""
import secrets
from typing import Callable

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config import settings


def _build_dependency() -> Callable[..., str]:
    security = HTTPBasic(realm=settings.SWAGGER_AUTH_REALM, auto_error=False)
    realm_header = {"WWW-Authenticate": f'Basic realm="{settings.SWAGGER_AUTH_REALM}"'}

    def _require_docs_auth(
        credentials: HTTPBasicCredentials = Depends(security),
    ) -> str:
        expected_user = settings.SWAGGER_AUTH_USERNAME
        expected_pass = settings.SWAGGER_AUTH_PASSWORD

        if not expected_user or not expected_pass:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API documentation is not configured for access.",
                headers=realm_header,
            )

        provided_user = (credentials.username if credentials else "") or ""
        provided_pass = (credentials.password if credentials else "") or ""

        user_ok = secrets.compare_digest(
            provided_user.encode("utf-8"), expected_user.encode("utf-8")
        )
        pass_ok = secrets.compare_digest(
            provided_pass.encode("utf-8"), expected_pass.encode("utf-8")
        )

        if not (user_ok and pass_ok):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers=realm_header,
            )
        return provided_user

    return _require_docs_auth


OPENAPI_PATH = "/openapi.json"
DOCS_PATH = "/docs"
REDOC_PATH = "/redoc"


def register_protected_docs(app: FastAPI) -> None:
    """Register Basic-Auth-protected /docs, /redoc, /openapi.json routes.

    The FastAPI app should be constructed with docs_url=None, redoc_url=None,
    and openapi_url=None so the default unprotected routes are not registered.
    """
    require_auth = _build_dependency()

    @app.get(OPENAPI_PATH, include_in_schema=False)
    async def protected_openapi(_: str = Depends(require_auth)):
        return app.openapi()

    @app.get(DOCS_PATH, include_in_schema=False)
    async def protected_swagger_ui(_: str = Depends(require_auth)):
        return get_swagger_ui_html(
            openapi_url=(app.root_path or "") + OPENAPI_PATH,
            title=f"{app.title} - Swagger UI",
        )

    @app.get(REDOC_PATH, include_in_schema=False)
    async def protected_redoc(_: str = Depends(require_auth)):
        return get_redoc_html(
            openapi_url=(app.root_path or "") + OPENAPI_PATH,
            title=f"{app.title} - ReDoc",
        )
