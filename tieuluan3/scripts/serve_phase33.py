"""Start the frozen Phase32 CPU HTTP server for browser QA; TRAIN demo requests only."""

import argparse
import os
import sys
from pathlib import Path

from src.common.contracts import ROOT

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--session", default="development_v1")
    args = parser.parse_args()
    if not args.session.replace("_", "").isalnum() or not 1024 <= args.port <= 65535:
        raise ValueError("Invalid QA session")
    database = Path("/tmp") / ("ai-paper-phase33-" + args.session) / "jobs.db"
    os.chdir(ROOT)
    os.environ.update(
        AI_SERVING_MODE="cpu",
        AI_JOB_DB=str(database),
        AI_CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173",
        OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        PYTHONDONTWRITEBYTECODE="1",
    )
    os.execv(
        sys.executable,
        [
            sys.executable,
            "-m",
            "gunicorn",
            "--bind",
            f"127.0.0.1:{args.port}",
            "--workers",
            "1",
            "--threads",
            "2",
            "--timeout",
            "120",
            "apps.api.v3.server:create_app()",
        ],
    )
