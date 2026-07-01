"""
Swagger / ReDoc docs untuk V2 — hanya menampilkan route /v2/...
Dilindungi HTTP Basic Auth (sama dengan v1).
"""
import secrets
from typing import Callable

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse

from app.config import settings

V2_OPENAPI_PATH = "/v2/openapi.json"
V2_DOCS_PATH = "/v2/docs"
V2_REDOC_PATH = "/v2/redoc"


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


def _get_v2_openapi_schema(app: FastAPI) -> dict:
    """
    Generate OpenAPI schema yang HANYA berisi route dengan prefix /v2/.
    Filter dilakukan pada routes yang terdaftar di app.
    """
    full_schema = app.openapi()

    # Filter paths: hanya yang berawalan /v2/
    v2_paths = {
        path: ops
        for path, ops in full_schema.get("paths", {}).items()
        if path.startswith("/v2/")
    }

    # Kumpulkan tag yang dipakai route v2
    used_tags = set()
    for ops in v2_paths.values():
        for method_data in ops.values():
            for tag in method_data.get("tags", []):
                used_tags.add(tag)

    # Filter tags
    v2_tags = [
        t for t in full_schema.get("tags", [])
        if t.get("name") in used_tags
    ]

    v2_schema = {
        **full_schema,
        "info": {
            **full_schema.get("info", {}),
            "title": "Kemhan Chatbot API v2",
            "description": (
                "## Kemhan Chatbot API v2\n\n"
                "API chatbot berbasis RAG untuk Kementerian Pertahanan RI.\n\n"
                "### Fitur\n"
                "* **Chat** — tanya jawab seputar Kemhan berbasis dokumen\n"
                "* **FAQ** — pertanyaan umum yang dikelola admin\n"
                "* **Admin: Dokumen** — upload PDF/DOCX/TXT sebagai referensi AI\n"
                "* **Admin: FAQ** — CRUD FAQ\n"
                "* **Admin: Feedback** — koreksi jawaban AI & training ground truth\n\n"
                "### Admin Auth\n"
                "Endpoint `/v2/admin/*` membutuhkan header: `X-Admin-Key: <secret>`"
            ),
            "version": "2.0.0",
        },
        "paths": v2_paths,
        "tags": v2_tags,
    }

    return v2_schema


def register_v2_docs(app: FastAPI) -> None:
    """
    Daftarkan /v2/docs, /v2/redoc, /v2/openapi.json
    dengan Basic Auth protection dan schema khusus v2.
    """
    require_auth = _build_dependency()
    root = app.root_path or ""

    @app.get(V2_OPENAPI_PATH, include_in_schema=False)
    async def v2_openapi_schema(_: str = Depends(require_auth)):
        return JSONResponse(_get_v2_openapi_schema(app))

    @app.get(V2_DOCS_PATH, include_in_schema=False)
    async def v2_swagger_ui(_: str = Depends(require_auth)):
        return get_swagger_ui_html(
            openapi_url=root + V2_OPENAPI_PATH,
            title="Kemhan Chatbot API v2 - Swagger UI",
            swagger_ui_parameters={"persistAuthorization": True},
        )

    @app.get(V2_REDOC_PATH, include_in_schema=False)
    async def v2_redoc(_: str = Depends(require_auth)):
        return get_redoc_html(
            openapi_url=root + V2_OPENAPI_PATH,
            title="Kemhan Chatbot API v2 - ReDoc",
        )
