"""Secure local HTTP server for the Phase 6 academic inference demo."""

import argparse
import json
import logging
import secrets
import threading
import time
from collections import defaultdict, deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from term_paper.deployment.app.model_service import ModelService
from term_paper.deployment.app.schemas import ValidationError


MAX_JSON_BYTES = 7 * 1024 * 1024
STATIC_ROOT = Path(__file__).resolve().parent / "static"
LOGGER = logging.getLogger("term_paper.deployment")


class RateLimiter:
    def __init__(self, limit=120, window_seconds=60):
        self.limit = int(limit); self.window = float(window_seconds)
        self.events = defaultdict(deque); self.lock = threading.Lock()

    def allow(self, client):
        now = time.monotonic()
        with self.lock:
            events = self.events[client]
            while events and events[0] <= now - self.window:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(now); return True


def make_handler(service, rate_limiter=None):
    limiter = rate_limiter or RateLimiter()

    class AppHandler(BaseHTTPRequestHandler):
        server_version = "AcademicModelLab/1.0"

        def log_message(self, format_string, *args):
            LOGGER.info("%s - %s", self.client_address[0], format_string % args)

        def _headers(self, content_type, length, status=200):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(length))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
            self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            if content_type.startswith("application/json"):
                self.send_header("Cache-Control", "no-store")
            self.end_headers()

        def _json(self, payload, status=200):
            body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
            self._headers("application/json; charset=utf-8", len(body), status); self.wfile.write(body)

        def _error(self, status, code, message, request_id=None):
            self._json({"error": {"code": code, "message": message}, "request_id": request_id}, status)

        def _read_json(self):
            content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type != "application/json":
                raise ValidationError("Content-Type phải là application/json.")
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as error:
                raise ValidationError("Content-Length không hợp lệ.") from error
            if length <= 0 or length > MAX_JSON_BYTES:
                raise ValidationError("JSON rỗng hoặc vượt giới hạn 7 MB.")
            try:
                return json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ValidationError("JSON không hợp lệ.") from error

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/health":
                self._json(service.health()); return
            if path == "/api/models":
                self._json({"models": service.public_registry()}); return
            if path.startswith("/api/demo/"):
                use_case = path.rsplit("/", 1)[-1]
                try:
                    self._json(service.demo(use_case))
                except KeyError:
                    self._error(404, "not_found", "Demo không tồn tại.")
                return
            static = {"/": ("index.html", "text/html; charset=utf-8"),
                      "/assets/styles.css": ("styles.css", "text/css; charset=utf-8"),
                      "/assets/app.js": ("app.js", "text/javascript; charset=utf-8")}
            if path in static:
                filename, content_type = static[path]; body = (STATIC_ROOT / filename).read_bytes()
                self._headers(content_type, len(body)); self.wfile.write(body); return
            self._error(404, "not_found", "Đường dẫn không tồn tại.")

        def do_POST(self):
            request_id = "req_" + secrets.token_hex(6)
            if not limiter.allow(self.client_address[0]):
                self._error(429, "rate_limited", "Quá nhiều yêu cầu; vui lòng thử lại sau.", request_id); return
            path = urlparse(self.path).path
            try:
                payload = self._read_json()
                if path == "/api/predict/diabetes":
                    result = service.predict_diabetes(payload)
                elif path == "/api/predict/eurosat":
                    if not isinstance(payload, dict) or set(payload) != {"image_base64"}:
                        raise ValidationError("Payload ảnh phải chỉ có trường image_base64.")
                    result = service.predict_eurosat(payload["image_base64"])
                elif path == "/api/predict/customer":
                    if not isinstance(payload, dict) or set(payload) != {"sequence"}:
                        raise ValidationError("Payload customer phải chỉ có trường sequence.")
                    result = service.predict_customer(payload["sequence"])
                elif path == "/api/predict/aapl":
                    if not isinstance(payload, dict) or set(payload) != {"sequence"}:
                        raise ValidationError("Payload AAPL phải chỉ có trường sequence.")
                    result = service.predict_aapl(payload["sequence"])
                else:
                    self._error(404, "not_found", "Endpoint không tồn tại.", request_id); return
                result["request_id"] = request_id; self._json(result)
            except ValidationError as error:
                self._error(400, "invalid_input", str(error), request_id)
            except Exception:
                LOGGER.exception("Inference failure request_id=%s path=%s", request_id, path)
                self._error(500, "internal_error", "Không thể xử lý yêu cầu lúc này.", request_id)

    return AppHandler


def create_server(host, port, service, rate_limiter=None):
    return ThreadingHTTPServer((host, int(port)), make_handler(service, rate_limiter))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Academic AI/ML/CNN/RNN inference demo")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--workspace", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    server = create_server(args.host, args.port, ModelService(args.workspace))
    print(f"Model Lab running at http://{args.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
