"""Flask API for the AI/ML/CNN/RNN term-paper model laboratory."""

from __future__ import annotations

import logging
import os
import secrets
import sys
import threading
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from flask import Flask, g, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, HTTPException, RequestEntityTooLarge
from werkzeug.middleware.proxy_fix import ProxyFix

# Support both ``python -m backend.app`` and ``python backend/app.py`` locally.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from term_paper.deployment.app.model_service import ModelService
from term_paper.deployment.app.schemas import ValidationError


API_VERSION = "2.0.0"
MAX_JSON_BYTES = 7 * 1024 * 1024
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
LOGGER = logging.getLogger("term_paper.api")


class ApiError(Exception):
    """An expected API error whose message is safe to return."""

    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


class RateLimiter:
    """Small in-memory limiter suitable for a single Gunicorn worker."""

    def __init__(self, limit: int = 120, window_seconds: float = 60):
        self.limit = int(limit)
        self.window_seconds = float(window_seconds)
        self.events: dict[str, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, client: str) -> bool:
        now = time.monotonic()
        with self.lock:
            events = self.events[client]
            while events and events[0] <= now - self.window_seconds:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(now)
            return True


def _normalise_origin(value: str) -> str:
    origin = value.strip().rstrip("/")
    if origin and not origin.startswith(("http://", "https://")):
        origin = f"https://{origin}"
    return origin


def allowed_origins() -> list[str]:
    """Return the explicit CORS allow-list for local and hosted React clients."""

    origins = {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    }
    configured = os.getenv("WEB_ORIGIN", "")
    origins.update(
        origin
        for origin in (_normalise_origin(item) for item in configured.split(","))
        if origin
    )
    return sorted(origins)


def _error_payload(code: str, message: str) -> dict[str, Any]:
    return {
        "error": {"code": code, "message": message},
        "request_id": getattr(g, "request_id", None),
    }


def _public_registry(service: ModelService) -> dict[str, dict[str, Any]]:
    safe_keys = {
        "version",
        "chapter",
        "model_sha256",
        "model_bytes",
        "hash_verified",
        "threshold",
    }
    return {
        model_id: {key: value for key, value in entry.items() if key in safe_keys}
        for model_id, entry in service.public_registry().items()
    }


def _json_body() -> Any:
    if not request.is_json:
        raise ApiError(
            415,
            "unsupported_media_type",
            "Content-Type phải là application/json.",
        )
    try:
        return request.get_json(silent=False)
    except BadRequest as error:
        raise ApiError(400, "invalid_json", "JSON không hợp lệ.") from error


def create_app(
    model_service: ModelService | None = None,
    rate_limiter: RateLimiter | None = None,
) -> Flask:
    service = model_service or ModelService(WORKSPACE_ROOT)
    limiter = rate_limiter or RateLimiter(
        limit=int(os.getenv("RATE_LIMIT_PER_MINUTE", "120")),
    )

    application = Flask(__name__)
    application.config.update(
        JSON_SORT_KEYS=False,
        MAX_CONTENT_LENGTH=MAX_JSON_BYTES,
    )
    # Render terminates TLS at its trusted proxy. ProxyFix lets Flask generate
    # correct scheme/host data while limiting trust to one proxy hop.
    application.wsgi_app = ProxyFix(
        application.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
    )
    CORS(
        application,
        resources={
            r"/api/*": {"origins": allowed_origins()},
            r"/health": {"origins": allowed_origins()},
        },
        supports_credentials=False,
    )

    @application.before_request
    def prepare_request():
        g.request_id = "req_" + secrets.token_hex(6)
        if request.method == "POST" and request.path.startswith("/api/predict/"):
            client = request.remote_addr or "unknown"
            if not limiter.allow(client):
                raise ApiError(
                    429,
                    "rate_limited",
                    "Quá nhiều yêu cầu; vui lòng thử lại sau.",
                )

    @application.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        )
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Request-ID"] = getattr(g, "request_id", "")
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

    @application.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        return jsonify(_error_payload(error.code, error.message)), error.status

    @application.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        return jsonify(_error_payload("invalid_input", str(error))), 400

    @application.errorhandler(RequestEntityTooLarge)
    def handle_large_payload(_error):
        return (
            jsonify(
                _error_payload(
                    "payload_too_large",
                    "JSON rỗng hoặc vượt giới hạn 7 MB.",
                )
            ),
            413,
        )

    @application.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        code = "not_found" if error.code == 404 else "http_error"
        message = (
            "Đường dẫn không tồn tại."
            if error.code == 404
            else "Yêu cầu HTTP không hợp lệ."
        )
        return jsonify(_error_payload(code, message)), error.code

    @application.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        LOGGER.exception(
            "Inference failure request_id=%s path=%s",
            getattr(g, "request_id", "unknown"),
            request.path,
        )
        return (
            jsonify(
                _error_payload(
                    "internal_error",
                    "Không thể xử lý yêu cầu lúc này.",
                )
            ),
            500,
        )

    @application.get("/")
    def index():
        return jsonify(
            {
                "name": "AI/ML/CNN/RNN Term Paper API",
                "docs": "/api/models",
                "health": "/health",
                "version": API_VERSION,
            }
        )

    @application.get("/health")
    def health():
        return jsonify(service.health())

    @application.get("/api/models")
    def models():
        return jsonify({"models": _public_registry(service)})

    @application.get("/api/demo/<use_case>")
    def demo(use_case: str):
        try:
            return jsonify(service.demo(use_case))
        except KeyError as error:
            raise ApiError(404, "not_found", "Demo không tồn tại.") from error

    @application.post("/api/predict/<use_case>")
    def predict(use_case: str):
        payload = _json_body()
        if use_case == "diabetes":
            result = service.predict_diabetes(payload)
        elif use_case == "eurosat":
            if not isinstance(payload, dict) or set(payload) != {"image_base64"}:
                raise ValidationError(
                    "Payload ảnh phải chỉ có trường image_base64."
                )
            result = service.predict_eurosat(payload["image_base64"])
        elif use_case in {"customer", "aapl"}:
            if not isinstance(payload, dict) or set(payload) != {"sequence"}:
                raise ValidationError(
                    f"Payload {use_case} phải chỉ có trường sequence."
                )
            predictor = (
                service.predict_customer
                if use_case == "customer"
                else service.predict_aapl
            )
            result = predictor(payload["sequence"])
        else:
            raise ApiError(404, "not_found", "Endpoint không tồn tại.")

        result["request_id"] = g.request_id
        return jsonify(result)

    return application


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
