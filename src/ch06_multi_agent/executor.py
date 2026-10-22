"""Local CPU worker isolation with hard tool timeout; no arbitrary process commands."""

import multiprocessing as mp
import resource
import threading

from src.common.contracts import canonical_sha256


def _child(connection, function, tool, record, attempt, fault):
    try:
        value = function(tool, record, attempt, fault)
        if isinstance(value, dict) and value.get("status") == "error":
            reply = value
        else:
            receipt = canonical_sha256(value)
            if fault == "numeric":
                value["values"][0] += 1.0
            elif fault == "citation":
                value["citations"] = []
            reply = {"status": "ok", "payload": value, "receipt_sha256": receipt}
        reply["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        connection.send(reply)
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, ArithmeticError, ImportError):
        connection.send({"status": "error", "code": "tool_error", "peak_rss_bytes": 0})
    finally:
        connection.close()


class ProcessExecutor:
    """WSL/Linux single-threaded driver only; not a web-server fork strategy."""

    def __init__(self, function):
        self.function, self.active = function, False

    def execute(self, tool, record_id, attempt, fault, seconds):
        if self.active or threading.active_count() != 1:
            raise ValueError("One single-threaded tool worker at a time")
        if seconds <= 0:
            return {"status": "timeout", "code": "deadline", "peak_rss_bytes": 0}
        context = mp.get_context("fork")
        reader, writer = context.Pipe(duplex=False)
        worker = context.Process(target=_child, args=(writer, self.function, tool, record_id, attempt, fault))
        self.active = True
        try:
            worker.start()
            writer.close()
            if reader.poll(seconds):
                try:
                    return reader.recv()
                except EOFError:
                    return {"status": "error", "code": "worker_exit", "peak_rss_bytes": 0}
            return {"status": "timeout", "code": "deadline", "peak_rss_bytes": 0}
        finally:
            if worker.pid is not None:
                if worker.is_alive():
                    worker.terminate()
                worker.join(timeout=0.2)
                if worker.is_alive():
                    worker.kill()
                    worker.join()
            reader.close()
            writer.close()
            self.active = False
