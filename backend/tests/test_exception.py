from app.core.exceptions.base import AppBaseExceptionError, AppNotFoundError
from app.core.exceptions.handlers import register_exception_handlers
from app.core.settings import AppSettings
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient


def _create_app():
    app = FastAPI()

    @app.get("/not_found")
    def not_found():
        raise AppNotFoundError(context={"id": "42"})

    @app.get("/http_error")
    def http_error():
        raise HTTPException(status_code=400, detail="bad request")

    @app.get("/unexpected")
    def unexpected():
        raise ValueError("boom")

    register_exception_handlers(app)
    return app


def test_app_exception_response_contains_trace_and_status():
    app = _create_app()
    client = TestClient(app)

    r = client.get("/not_found")
    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "AppNotFoundError"
    assert body.get("trace_id")
    # trace id also set on response headers
    assert "X-Trace-Id" in r.headers


def test_http_exception_handler_returns_detail_and_trace():
    app = _create_app()
    client = TestClient(app)

    r = client.get("/http_error")
    assert r.status_code == 400
    body = r.json()
    assert body["message"] == "bad request"
    assert body.get("trace_id")


def test_unexpected_exception_returns_internal_error():
    app = _create_app()
    client = TestClient(app, raise_server_exceptions=False)

    r = client.get("/unexpected")
    assert r.status_code == 500
    body = r.json()
    assert body["error"] == "InternalServerError"
    # Accept either default internal error message or English fallback
    assert body["message"] in [
        "Terjadi kesalahan sistem internal.",
        "Internal system error occurred.",
        "Terjadi kesalahan internal.",
        "Internal error occurred.",
    ]
    assert "trace_id" in body


def test_debug_exposes_context(monkeypatch):
    # Create app and a custom exception that exposes context when debug is True
    class ExposeError(AppBaseExceptionError):
        EXPOSE_CONTEXT = True
        DEFAULT_STATUS_CODE = 422
        DEFAULT_CODE = "expose_error"
        DEFAULT_MESSAGE = "expose"

    app = FastAPI()

    @app.get("/expose")
    def expose():
        raise ExposeError(context={"user": "alice"})

    # Force app settings to have debug=True
    monkeypatch.setattr(
        "app.core.exceptions.handlers.get_app_settings",
        lambda: AppSettings(debug=True),
    )

    register_exception_handlers(app)
    client = TestClient(app)

    r = client.get("/expose")
    assert r.status_code == 422
    body = r.json()
    assert body["error"] == "ExposeError"
    assert body["context"] == {"user": "alice"}
    assert "trace_id" in body


def test_expose_error_context_not_exposed_when_not_debug(monkeypatch):
    class ExposeError(AppBaseExceptionError):
        EXPOSE_CONTEXT = True
        DEFAULT_STATUS_CODE = 422
        DEFAULT_CODE = "expose_error"
        DEFAULT_MESSAGE = "expose"

    app = FastAPI()

    @app.get("/expose")
    def expose():
        raise ExposeError(context={"user": "bob"})

    monkeypatch.setattr(
        "app.core.exceptions.handlers.get_app_settings",
        lambda: AppSettings(debug=False),
    )

    register_exception_handlers(app)
    client = TestClient(app)

    r = client.get("/expose")
    assert r.status_code == 422
    body = r.json()
    assert body["error"] == "ExposeError"
    assert "context" not in body
    assert "trace_id" in body
