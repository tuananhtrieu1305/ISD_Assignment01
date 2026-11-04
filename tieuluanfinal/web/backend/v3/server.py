"""Public catalog + private-capability async inference API. Never trains models."""

import json
import os
import re
import secrets
import threading
import time

from flask import Flask, g, jsonify, request, send_file
from werkzeug.exceptions import HTTPException

from apps.api.v3.jobs import JobError, JobStore
from apps.api.v3.registry import ArtifactError, Registry
from src.common.contracts import validate_document


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def depth_guard(value, depth=0):
    if depth > 10:
        raise ValueError("JSON nesting budget")
    if isinstance(value, dict):
        for child in value.values():
            depth_guard(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            depth_guard(child, depth + 1)


def create_app(*, registry_path=None, database=None, start_worker=True, mode=None):
    app = Flask(__name__)
    app.config.update(
        MAX_CONTENT_LENGTH=6_400_000,
        JSON_SORT_KEYS=False,
        TRUSTED_HOSTS=os.environ.get("AI_TRUSTED_HOSTS", "localhost,127.0.0.1,.onrender.com").split(","),
    )
    app.json.ensure_ascii = False
    mode = mode or os.environ.get("AI_SERVING_MODE", "cpu")
    if mode not in {"cpu", "local_gpu"} or (os.environ.get("RENDER") and mode != "cpu"):
        raise ValueError("Invalid serving mode; Render is CPU only")
    try:
        registry = Registry(registry_path)
    except ArtifactError:
        registry = None
    store = JobStore(database or os.environ.get("AI_JOB_DB", "/tmp/ai-paper-v3/jobs.db"))
    app.extensions.update(registry=registry, job_store=store, serving_mode=mode)
    origins = {
        s.strip()
        for s in os.environ.get("AI_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if s.strip()
    }
    if "*" in origins:
        raise ValueError("Wildcard CORS is not allowed")
    rates, rate_lock = {}, threading.Lock()
    ready_cache = {"time": 0, "rows": []}
    ready_lock = threading.Lock()

    def components():
        with ready_lock:
            if time.monotonic() - ready_cache["time"] > 30:
                ready_cache.update(time=time.monotonic(), rows=registry.components())
            return list(ready_cache["rows"])

    def fail(code, status, message="Request cannot be processed"):
        raise JobError(code, status)

    def owner():
        token = request.headers.get("X-Client-Token", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", token):
            fail("client_token_required", 400)
        return token

    def require_registry():
        if registry is None:
            fail("registry_unavailable", 503)
        return registry

    def body():
        if request.mimetype != "application/json":
            fail("unsupported_media_type", 415)
        try:
            document = json.loads(
                request.get_data(),
                object_pairs_hook=strict_object,
                parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON")),
            )
            depth_guard(document)
            if not isinstance(document, dict):
                raise TypeError("Object required")
            return document
        except (ValueError, TypeError, RecursionError, UnicodeError):
            fail("invalid_json", 400)

    def wrapped(data):
        return {"schema_version": "3.0.0", "request_id": g.request_id, "data": data}

    def paged(rows, filters=()):
        allowed = {"page", "page_size", *filters}
        if set(request.args) - allowed or any(len(request.args.getlist(k)) != 1 for k in request.args):
            fail("invalid_query", 400)
        try:
            page, size = int(request.args.get("page", "1")), int(request.args.get("page_size", "20"))
            if not 1 <= page <= 100000 or not 1 <= size <= 100:
                raise ValueError()
            if "chapter" in request.args:
                chapter = int(request.args["chapter"])
                if chapter not in range(1, 7):
                    raise ValueError()
                rows = [r for r in rows if r["chapter"] == chapter]
            if "dataset_id" in request.args:
                rows = [r for r in rows if r["dataset_id"] == request.args["dataset_id"]]
        except ValueError:
            fail("invalid_query", 400)
        return {
            **wrapped(rows[(page - 1) * size : page * size]),
            "page": page,
            "page_size": size,
            "total": len(rows),
        }

    @app.before_request
    def before():
        g.request_id = "request_" + secrets.token_hex(12)
        origin = request.headers.get("Origin")
        if origin and origin not in origins:
            fail("origin_not_allowed", 403)
        if request.method == "OPTIONS":
            return "", 204
        # No proxy header trust: a forged X-Forwarded-For cannot bypass this limiter.
        # On a shared reverse proxy this is intentionally conservative/global.
        if request.path not in {"/health", "/ready"}:
            now = time.monotonic()
            bucket = request.remote_addr or "unknown"
            with rate_lock:
                for key in list(rates):
                    if rates[key][0] + 60 < now:
                        del rates[key]
                if bucket not in rates and len(rates) >= 1024:
                    fail("rate_limited", 429)
                start, count = rates.get(bucket, (now, 0))
                if count >= 240:
                    fail("rate_limited", 429)
                rates[bucket] = (start, count + 1)

    @app.after_request
    def after(response):
        response.headers.update(
            {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "no-referrer",
                "Cache-Control": "no-store",
                "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
                "X-Request-ID": getattr(g, "request_id", "request_unknown"),
            }
        )
        origin = request.headers.get("Origin")
        if origin in origins:
            response.headers.update(
                {
                    "Access-Control-Allow-Origin": origin,
                    "Vary": "Origin",
                    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key,X-Client-Token",
                    "Access-Control-Expose-Headers": "Location,Retry-After,X-Request-ID",
                }
            )
        if response.status_code in {429, 503}:
            response.headers["Retry-After"] = "5"
        return response

    @app.errorhandler(Exception)
    def error(exception):
        status, code = 500, "internal_error"
        if isinstance(exception, JobError):
            status, code = exception.status, exception.code
        elif isinstance(exception, ArtifactError):
            status, code = 503, "artifact_unavailable"
        elif isinstance(exception, HTTPException):
            status, code = (
                exception.code,
                {
                    400: "invalid_request",
                    404: "not_found",
                    405: "method_not_allowed",
                    413: "input_too_large",
                }.get(exception.code, "http_error"),
            )
        document = {
            "schema_version": "3.0.0",
            "request_id": getattr(g, "request_id", "request_unknown"),
            "error": {
                "code": code,
                "message": "Request cannot be processed",
                "retryable": status in {429, 503},
                "details": [],
            },
        }
        validate_document("api#error", document)
        return jsonify(document), status

    @app.get("/health")
    def health():
        return {"schema_version": "3.0.0", "status": "alive", "components": []}

    @app.get("/ready")
    def ready():
        if registry is None:
            return {"schema_version": "3.0.0", "status": "not_ready", "components": []}, 503
        rows = components()
        all_ready = all(r["status"] == "ready" for r in rows)
        any_ready = any(r["status"] == "ready" for r in rows)
        worker_ready = not start_worker or app.extensions["supervisor"].thread.is_alive()
        if start_worker:
            rows.append(
                {
                    "id": "serving_worker",
                    "status": "ready" if worker_ready else "unavailable",
                    "reason": None if worker_ready else "worker_unavailable",
                }
            )
        return {
            "schema_version": "3.0.0",
            "status": "not_ready"
            if not worker_ready or not any_ready
            else "ready"
            if all_ready
            else "degraded",
            "components": rows,
        }, 200 if any_ready and worker_ready else 503

    @app.get("/api/v3/chapters")
    def chapters():
        return paged(require_registry().chapters)

    @app.get("/api/v3/chapters/<chapter_id>")
    def chapter(chapter_id):
        result = next((r for r in require_registry().chapters if str(r["chapter"]) == chapter_id), None)
        if result is None:
            fail("not_found", 404)
        return wrapped(result)

    @app.get("/api/v3/datasets")
    def datasets():
        rows = [
            require_registry().json(r["source_manifest"])["contract"]
            for r in require_registry().datasets.values()
        ]
        return paged(rows, ("chapter",))

    @app.get("/api/v3/datasets/<dataset_id>")
    def dataset(dataset_id):
        item = require_registry().datasets.get(dataset_id)
        if item is None:
            fail("not_found", 404)
        return wrapped(registry.json(item["source_manifest"])["contract"])

    @app.get("/api/v3/datasets/<dataset_id>/overview")
    def overview(dataset_id):
        item = require_registry().datasets.get(dataset_id)
        if item is None:
            fail("not_found", 404)
        result = dict(item)
        result["data_card_text"] = registry.checked(item["data_card"]).read_text(encoding="utf-8")
        result["eda_summary"] = registry.json(item["eda"])
        result["sample"] = registry.json(registry.document["samples"]).get(dataset_id)
        return wrapped(result)

    @app.get("/api/v3/datasets/<dataset_id>/results")
    def result_index(dataset_id):
        result = require_registry().document["result_indexes"].get(dataset_id)
        if result is None:
            fail("not_found", 404)
        result = dict(result)
        if dataset_id.startswith("ch5_"):
            result["live_demo_equivalent_to_historical_benchmark"] = False
        if dataset_id == "ch5_wikidata_subgraphs":
            result["artifacts"] = [r for r in result["artifacts"] if "graph_statistics" in r["path"]]
            result["scope"] = (
                "Structural graph snapshot statistics only; no third QA benchmark or QA scorecard."
            )
        for record in result["artifacts"]:
            registry.checked(record)
        return wrapped(result)

    @app.get("/api/v3/models")
    def models():
        rows = []
        for model in require_registry().models.values():
            row = {
                k: model[k]
                for k in (
                    "model_id",
                    "dataset_id",
                    "family",
                    "implementation",
                    "backend",
                    "contract",
                    "status",
                    "reason",
                )
            }
            if model["chapter"] < 5:
                try:
                    for record in model["assets"]:
                        registry.checked(record)
                except ArtifactError:
                    row.update(status="unavailable", reason="artifact_unavailable")
            elif model["status"] == "ready":
                identity = "kg_rag" if model["chapter"] == 5 else "agents"
                component = next(r for r in components() if r["id"] == identity)
                if component["status"] != "ready":
                    row.update(status="unavailable", reason="artifact_unavailable")
            if mode == "local_gpu" and model["chapter"] < 5:
                row["backend"] = {"scratch": "numpy", "keras": "tensorflow", "pytorch": "torch"}[
                    model["implementation"]
                ]
            rows.append({**row, "chapter": model["chapter"]})
        reply = paged(rows, ("chapter", "dataset_id"))
        for row in reply["data"]:
            row.pop("chapter")
        return reply

    @app.get("/api/v3/models/<model_id>/contract")
    def contract(model_id):
        model = require_registry().models.get(model_id)
        if model is None:
            fail("not_found", 404)
        return wrapped(registry.json(model["contract"]))

    @app.get("/api/v3/artifacts/<artifact_id>")
    def artifact(artifact_id):
        record = require_registry().document["public_artifacts"].get(artifact_id)
        if record is None:
            fail("not_found", 404)
        path = registry.checked(record)
        return wrapped(
            {
                "artifact_id": artifact_id,
                **record,
                "size_bytes": path.stat().st_size,
                "content_url": f"/api/v3/artifacts/{artifact_id}/content",
            }
        )

    @app.get("/api/v3/artifacts/<artifact_id>/content")
    def artifact_content(artifact_id):
        record = require_registry().document["public_artifacts"].get(artifact_id)
        if record is None:
            fail("not_found", 404)
        path = registry.checked(record)
        if path.suffix not in {".json", ".csv", ".md", ".png"} or path.stat().st_size > 4 * 1024**2:
            fail("artifact_not_public", 404)
        return send_file(path, as_attachment=True, download_name=path.name)

    @app.get("/api/v3/runs")
    def runs():
        rows = []
        for item in require_registry().document["runs"]:
            rows.append({**item, "split": item["run_id"].rsplit("_", 1)[1]})
        return paged(rows, ("chapter", "dataset_id"))

    @app.get("/api/v3/runs/<run_id>")
    def run(run_id):
        item = next((r for r in require_registry().document["runs"] if r["run_id"] == run_id), None)
        if item is None:
            fail("not_found", 404)
        return wrapped(registry.json(item["record"]))

    def submit(document):
        from apps.api.v3.inference import decode_input

        key = request.headers.get("Idempotency-Key", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", key):
            fail("idempotency_key_required", 400)
        identity = owner()
        if start_worker and not app.extensions["supervisor"].thread.is_alive():
            fail("worker_unavailable", 503)
        try:
            decode_input(require_registry(), document)
        except ArtifactError:
            raise
        except (ValueError, TypeError, KeyError, OverflowError):
            fail("validation_error", 422)
        job = store.create(document, key, identity)
        location = "/api/v3/jobs/" + job["job_id"]
        return (
            {
                "schema_version": "3.0.0",
                "request_id": g.request_id,
                "job_id": job["job_id"],
                "poll_url": location,
            },
            202,
            {"Location": location, "Retry-After": "1"},
        )

    @app.post("/api/v3/comparisons")
    def comparison():
        return submit(body())

    @app.post("/api/v3/agent-tasks")
    def agent_task():
        document = body()
        try:
            validate_document("api#agent_task", document)
            domain = document["dataset_id"].removeprefix("ch6_").removesuffix("_tasks")
            adapted = {
                "schema_version": "3.0.0",
                "chapter": 6,
                "dataset_id": document["dataset_id"],
                "family": "multi_agent",
                "implementations": document["variants"],
                "input": {"kind": "question", "text": document["question"], "domain": domain},
            }
        except (ValueError, KeyError):
            fail("validation_error", 422)
        return submit(adapted)

    @app.get("/api/v3/jobs/<job_id>")
    def job(job_id):
        document = store.get(job_id, owner())
        validate_document("api#job", document)
        return document

    @app.get("/api/v3/jobs/<job_id>/details")
    def details(job_id):
        return wrapped(store.extras(job_id, owner()))

    @app.post("/api/v3/jobs/<job_id>/cancellations")
    def cancel(job_id):
        try:
            validate_document("api#cancel_request", body())
        except ValueError:
            fail("validation_error", 422)
        location = "/api/v3/jobs/" + job_id
        return (
            {
                "schema_version": "3.0.0",
                "request_id": g.request_id,
                "job_id": store.cancel(job_id, owner())["job_id"],
                "poll_url": location,
            },
            202,
            {"Location": location, "Retry-After": "1"},
        )

    @app.get("/api/v3/agent-traces/<trace_id>")
    def trace(trace_id):
        match = re.fullmatch(r"trace_([a-f0-9]{40})_a[0-2]", trace_id)
        if not match:
            fail("not_found", 404)
        extra = store.extras("job_" + match[1], owner())
        result = extra.get("traces", {}).get(trace_id)
        if result is None:
            fail("not_found", 404)
        return wrapped(result)

    @app.get("/api/v3/openapi.json")
    def openapi():
        from apps.api.v3.openapi import specification

        return specification()

    if start_worker and registry is not None:
        from apps.api.v3.supervisor import Supervisor

        supervisor = Supervisor(store, mode)
        supervisor.start()
        app.extensions["supervisor"] = supervisor
    return app
