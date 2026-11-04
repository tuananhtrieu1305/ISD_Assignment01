"""One isolated validation job; no TEST mode is provided."""

import os

for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "2"
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import argparse
import json
import re
import traceback
from datetime import UTC, datetime

from src.ch04_rnn_lstm.phase29.experiment import train_run
from src.ch04_rnn_lstm.phase29.protocol import BASE
from src.common.artifact_core import write_once


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z][a-z0-9_-]{0,95}", args.run_id):
        parser.error("Invalid run ID")
    try:
        print(json.dumps(train_run(args.run_id)), flush=True)
    except Exception:
        failure = {
            "run_id": args.run_id,
            "at": datetime.now(UTC).isoformat(),
            "traceback": traceback.format_exc(),
            "test_evaluation_executed": False,
        }
        write_once(
            BASE / "attempts" / f"{args.run_id}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}.json",
            failure,
        )
        raise


if __name__ == "__main__":
    main()
