"""Run exactly one declared Chapter2 training or TEST job in its locked venv."""

import os

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import argparse
import json
from datetime import UTC, datetime

from src.ch02_ml.experiment import evaluate_run, train_run
from src.ch02_ml.protocol import BASE, run_ids
from src.ch02_ml.test_gate import atomic_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--mode", choices=["train", "test"], default="train")
    args = parser.parse_args()
    if args.run_id not in run_ids():
        raise ValueError("Unknown declared run ID")
    try:
        result = (train_run if args.mode == "train" else evaluate_run)(args.run_id)
    except Exception as error:
        atomic_json(
            BASE / "runs" / args.run_id / f"{args.mode}_failure.json",
            {
                "status": "failed",
                "at": datetime.now(UTC).isoformat(),
                "error": f"{type(error).__name__}: {error}",
                "test_retry_allowed": False,
            },
        )
        raise
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
