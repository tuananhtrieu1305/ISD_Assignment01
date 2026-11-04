"""Exclusive bounded process supervisor; never fork a threaded HTTP handler."""

import atexit
import fcntl
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from apps.api.v3.inference import failure_job
from src.common.contracts import ROOT


def rss_bytes(pid):
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    except (OSError, ValueError):
        pass
    return 0


def terminate_tree(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
        if process.poll() is None:
            process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=2)
    except ProcessLookupError:
        pass


def pss_bytes(pid):
    try:
        for line in Path(f"/proc/{pid}/smaps_rollup").read_text().splitlines():
            if line.startswith("Pss:"):
                return int(line.split()[1]) * 1024
    except (OSError, ValueError):
        pass
    return None


def group_memory(pgid):
    total, used_fallback = 0, False
    for folder in Path("/proc").iterdir():
        if not folder.name.isdigit():
            continue
        try:
            fields = (folder / "stat").read_text().rsplit(")", 1)[1].split()
            if int(fields[2]) != pgid:  # field5 = process group ID
                continue
            value = pss_bytes(int(folder.name))
            if value is None:
                used_fallback = True
                value = rss_bytes(int(folder.name))
            total += value
        except (OSError, ValueError, IndexError):
            continue
    return total, used_fallback


class Supervisor:
    def __init__(self, store, mode="cpu", *, deadline=None, memory_bytes=None):
        self.store, self.mode = store, mode
        self.deadline = deadline or (300 if mode == "local_gpu" else 60)
        self.memory_bytes = memory_bytes or (4 * 1024**3 if mode == "local_gpu" else 448 * 1024**2)
        self.stop_event, self.process = threading.Event(), None
        self.thread = threading.Thread(target=self.loop, name="inference-supervisor", daemon=True)
        self.guard = None

    def start(self):
        self.guard = open(str(self.store.path) + ".supervisor.lock", "a+")  # noqa: SIM115 -- lease spans start/close
        try:
            fcntl.flock(self.guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.guard.close()
            raise RuntimeError("Only one API worker/supervisor is supported") from None
        self.store.recover()
        self.thread.start()
        atexit.register(self.close)

    def close(self):
        self.stop_event.set()
        if self.process is not None:
            terminate_tree(self.process)
        if self.thread.is_alive() and threading.current_thread() is not self.thread:
            self.thread.join(timeout=3)
        if self.guard and not self.guard.closed:
            self.guard.close()

    def execute(self, identity, request):
        env = {
            **os.environ,
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        if self.mode == "cpu":
            env["CUDA_VISIBLE_DEVICES"] = "-1"
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "apps.api.v3.worker",
                "--database",
                str(self.store.path),
                "--job-id",
                identity,
                "--mode",
                self.mode,
            ],
            cwd=ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        start, peak, peak_group, peak_service, fallback = time.monotonic(), 0, 0, 0, False
        reason = None
        while self.process.poll() is None:
            peak = max(peak, rss_bytes(self.process.pid))
            group, was_fallback = group_memory(self.process.pid)
            parent = pss_bytes(os.getpid())
            fallback = fallback or was_fallback or parent is None
            service = group + (parent if parent is not None else rss_bytes(os.getpid()))
            peak_group, peak_service = max(peak_group, group), max(peak_service, service)
            if self.stop_event.is_set() or self.store.status(identity) in {"cancelled", "expired"}:
                reason = "cancelled"
            elif time.monotonic() - start > self.deadline:
                reason = "deadline_exceeded"
            elif service > self.memory_bytes:
                reason = "memory_budget"
            if reason:
                terminate_tree(self.process)
                break
            self.stop_event.wait(0.1)
        terminate_tree(self.process)  # also reap any descendant left after an abnormal parent exit
        if self.store.status(identity) == "running":
            self.store.finish(identity, failure_job(request, reason or "worker_failed"), {})
        self.store.telemetry(
            identity,
            {
                "worker_peak_sampled_rss_bytes": peak,
                "group_peak_sampled_pss_or_rss_bytes": peak_group,
                "web_plus_job_peak_sampled_pss_or_rss_bytes": peak_service,
                "used_rss_fallback": fallback,
                "worker_wall_ms": (time.monotonic() - start) * 1000,
                "budget_bytes": self.memory_bytes,
                "definition": "Sampled web worker + all job process-group PSS; RSS conservative fallback; excludes gunicorn master/OS/CUDA VRAM; not a cloud SLA",
            },
        )
        self.process = None

    def loop(self):
        while not self.stop_event.is_set():
            claim = self.store.claim()
            if claim:
                try:
                    self.execute(*claim)
                except Exception:  # noqa: BLE001 -- supervisor boundary preserves queue liveness without leaking payloads
                    if self.process is not None:
                        terminate_tree(self.process)
                    self.store.finish(claim[0], failure_job(claim[1], "worker_launch_failed"))
                    self.process = None
            else:
                self.stop_event.wait(0.2)
