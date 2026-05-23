"""Tests for Swagger / API docs Basic Auth protection.

These tests construct a minimal FastAPI app that mirrors the docs setup used in
``app.main``, so they don't require DB / scheduler / model dependencies.
"""
import base64
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def app_with_docs(monkeypatch):
    from app.config import settings
    from app.api.docs_auth import register_protected_docs

    monkeypatch.setattr(settings, "SWAGGER_AUTH_USERNAME", "chatbot_api_user")
    monkeypatch.setattr(settings, "SWAGGER_AUTH_PASSWORD", "qwert21345!")
    monkeypatch.setattr(settings, "SWAGGER_AUTH_REALM", "Swagger")

    app = FastAPI(
        title="Test",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    @app.get("/api/ping")
    def ping():
        return {"ok": True}

    register_protected_docs(app)
    return app


def _basic_header(user: str, password: str) -> dict:
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_docs_endpoint_requires_auth(app_with_docs, path):
    client = TestClient(app_with_docs)
    resp = client.get(path)
    assert resp.status_code == 401
    assert resp.headers.get("www-authenticate", "").lower().startswith("basic")
    assert 'realm="Swagger"' in resp.headers["www-authenticate"]


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_docs_endpoint_rejects_wrong_credentials(app_with_docs, path):
    client = TestClient(app_with_docs)
    resp = client.get(path, headers=_basic_header("nope", "wrong"))
    assert resp.status_code == 401
    assert 'realm="Swagger"' in resp.headers.get("www-authenticate", "")


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_docs_endpoint_accepts_correct_credentials(app_with_docs, path):
    client = TestClient(app_with_docs)
    resp = client.get(path, headers=_basic_header("chatbot_api_user", "qwert21345!"))
    assert resp.status_code == 200


def test_normal_api_endpoint_is_unaffected(app_with_docs):
    client = TestClient(app_with_docs)
    resp = client.get("/api/ping")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_docs_locked_when_credentials_unset(monkeypatch):
    from app.config import settings
    from app.api.docs_auth import register_protected_docs

    monkeypatch.setattr(settings, "SWAGGER_AUTH_USERNAME", None)
    monkeypatch.setattr(settings, "SWAGGER_AUTH_PASSWORD", None)
    monkeypatch.setattr(settings, "SWAGGER_AUTH_REALM", "Swagger")

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    register_protected_docs(app)
    client = TestClient(app)

    resp = client.get("/docs", headers=_basic_header("anything", "anything"))
    assert resp.status_code == 401
