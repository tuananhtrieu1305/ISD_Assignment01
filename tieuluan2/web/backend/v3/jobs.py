"""Single-host SQLite jobs: bounded queue, ownership, idempotency and retention."""

import hashlib
import json
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from src.common.contracts import canonical_sha256

TERMINAL = {"succeeded", "partial_failed", "failed", "cancelled", "expired"}


class JobError(ValueError):
    def __init__(self, code, status=404):
        self.code, self.status = code, status
        super().__init__(code)


def owner_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def stamp(seconds):
    return datetime.fromtimestamp(seconds, UTC).isoformat()


class JobStore:
    def __init__(self, path, *, ttl=1800, capacity=32):
        self.path, self.ttl, self.capacity = Path(path), ttl, capacity
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.path.is_symlink() or self.path.parent.is_symlink():
            raise ValueError("Job storage must not be a symlink")
        self.path.touch(mode=0o600, exist_ok=True)
        self.path.chmod(0o600)
        with self.connection() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS jobs (
                 id TEXT PRIMARY KEY, owner TEXT NOT NULL, idem TEXT NOT NULL,
                 digest TEXT NOT NULL, request TEXT NOT NULL, status TEXT NOT NULL,
                 created REAL NOT NULL, expires REAL NOT NULL, result TEXT, extras TEXT,
                 UNIQUE(owner, idem));
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.execute("PRAGMA secure_delete=ON")
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def create(self, request, key, owner):
        digest, now = canonical_sha256(request), time.time()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM jobs WHERE expires < ?", (now,))
            row = db.execute(
                "SELECT * FROM jobs WHERE owner=? AND idem=?", (owner_hash(owner), key)
            ).fetchone()
            if row:
                if row["digest"] != digest:
                    raise JobError("idempotency_conflict", 409)
                return self._view(row)
            if db.execute("SELECT count(*) FROM jobs").fetchone()[0] >= self.capacity:
                raise JobError("queue_full", 503)
            used = db.execute(
                "SELECT coalesce(sum(length(request)+coalesce(length(result),0)+coalesce(length(extras),0)),0) FROM jobs"
            ).fetchone()[0]
            if used + len(json.dumps(request)) > 64 * 1024**2:
                raise JobError("storage_budget", 503)
            identity = "job_" + secrets.token_hex(20)
            db.execute(
                "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    identity,
                    owner_hash(owner),
                    key,
                    digest,
                    json.dumps(request, allow_nan=False),
                    "queued",
                    now,
                    now + self.ttl,
                    None,
                    None,
                ),
            )
            return self._view(db.execute("SELECT * FROM jobs WHERE id=?", (identity,)).fetchone())

    def _view(self, row):
        request = json.loads(row["request"])
        result = json.loads(row["result"]) if row["result"] else {}
        result.update(
            {
                "schema_version": "3.0.0",
                "request_id": "request_" + row["id"][4:],
                "job_id": row["id"],
                "request_sha256": row["digest"],
                "status": row["status"],
                "dataset_id": request["dataset_id"],
                "family": request["family"],
                "created_at": stamp(row["created"]),
                "expires_at": stamp(row["expires"]),
            }
        )
        defaults = {
            "results": [],
            "comparison_valid": False,
            "comparison_blockers": [],
            "trace_ids": [],
            "metric_artifacts": [],
            "input_sha256": canonical_sha256(request.get("input", {})),
        }
        for key, default in defaults.items():
            result.setdefault(key, default)
        return result

    def _owned(self, db, identity, owner):
        row = db.execute(
            "SELECT * FROM jobs WHERE id=? AND owner=?", (identity, owner_hash(owner))
        ).fetchone()
        if not row or row["expires"] < time.time():
            raise JobError("not_found")
        return row

    def get(self, identity, owner):
        with self.connection() as db:
            return self._view(self._owned(db, identity, owner))

    def extras(self, identity, owner):
        with self.connection() as db:
            row = self._owned(db, identity, owner)
            return json.loads(row["extras"]) if row["extras"] else {}

    def cancel(self, identity, owner):
        with self.connection() as db:
            row = self._owned(db, identity, owner)
            if row["status"] not in TERMINAL:
                db.execute("UPDATE jobs SET status='cancelled' WHERE id=?", (identity,))
        return self.get(identity, owner)

    def claim(self):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM jobs WHERE expires < ?", (time.time(),))
            row = db.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY created LIMIT 1").fetchone()
            if row:
                db.execute("UPDATE jobs SET status='running' WHERE id=?", (row["id"],))
                return row["id"], json.loads(row["request"])
        return None

    def status(self, identity):
        with self.connection() as db:
            row = db.execute("SELECT status FROM jobs WHERE id=?", (identity,)).fetchone()
            return row[0] if row else "expired"

    def finish(self, identity, result, extras=None):
        encoded, extra = json.dumps(result, allow_nan=False), json.dumps(extras or {}, allow_nan=False)
        if len(encoded) + len(extra) > 2 * 1024**2:
            raise JobError("output_budget", 503)
        with self.connection() as db:
            db.execute(
                "UPDATE jobs SET status=?,result=?,extras=? WHERE id=? AND status='running'",
                (result["status"], encoded, extra, identity),
            )

    def telemetry(self, identity, document):
        with self.connection() as db:
            row = db.execute("SELECT extras FROM jobs WHERE id=?", (identity,)).fetchone()
            if row:
                extra = json.loads(row[0]) if row[0] else {}
                extra["serving_telemetry"] = document
                db.execute(
                    "UPDATE jobs SET extras=? WHERE id=?", (json.dumps(extra, allow_nan=False), identity)
                )

    def recover(self):
        from apps.api.v3.inference import failure_job

        with self.connection() as db:
            for row in db.execute("SELECT id,request FROM jobs WHERE status='running'").fetchall():
                result = failure_job(json.loads(row["request"]), "worker_restarted")
                db.execute(
                    "UPDATE jobs SET status='failed',result=? WHERE id=?", (json.dumps(result), row["id"])
                )
