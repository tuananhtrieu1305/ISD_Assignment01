"""One exec-isolated job. Single Python thread is required by the agent executor."""

import argparse
import json
import os
import platform
import resource
import sys

from threadpoolctl import threadpool_limits

from apps.api.v3.inference import compare, failure_job
from apps.api.v3.jobs import JobStore
from apps.api.v3.registry import Registry


def run(database, job_id, mode):
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_FSIZE, (128 * 1024**2, 128 * 1024**2))
    store = JobStore(database)
    with store.connection() as db:
        row = db.execute("SELECT request FROM jobs WHERE id=? AND status='running'", (job_id,)).fetchone()
    if row is None:
        return
    request = json.loads(row[0])
    try:
        with threadpool_limits(limits=1):
            result, extras = compare(Registry(), request, job_id, mode)
    except Exception:  # noqa: BLE001 -- isolated inference boundary emits sanitized failure for every model slot
        result, extras = failure_job(request, "inference_failed"), {}
    extras["serving_runtime"] = {
        "python": platform.python_version(),
        "numpy": __import__("numpy").__version__,
        "native_frameworks_imported_in_driver": [
            n for n in ["torch", "tensorflow", "keras"] if n in sys.modules
        ],
        "mode": mode,
        "models_retrained": 0,
        "historical_test_evaluation_executed": False,
    }
    # Exactly one result writer; supervisor only finalizes an uncompleted job after exit.
    store.finish(job_id, result, extras)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--mode", choices=["cpu", "local_gpu"], required=True)
    args = parser.parse_args()
    run(args.database, args.job_id, args.mode)


if __name__ == "__main__":
    main()
