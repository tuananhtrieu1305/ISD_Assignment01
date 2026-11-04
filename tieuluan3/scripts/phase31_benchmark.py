"""Prospective local task benchmark. Only --stage test consumes the NEW agent-task holdout."""

import argparse
import platform
import resource
import sys
import time
from datetime import UTC, datetime

from threadpoolctl import threadpool_limits

from scripts.prepare_phase31 import BASE
from src.ch05_knowledge_rag.preservation import checked, ref
from src.ch06_multi_agent.benchmark import audit_groups, claim, score
from src.ch06_multi_agent.core import VARIANTS, Orchestrator
from src.ch06_multi_agent.executor import ProcessExecutor
from src.ch06_multi_agent.tools import ToolCatalog
from src.common.artifact_core import write_once
from src.common.contracts import ROOT, read_json

SOURCE_FILES = (
    [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / "src/ch06_multi_agent").glob("*.py"))]
    + [
        "scripts/prepare_phase31.py",
        "scripts/phase31_benchmark.py",
        "scripts/verify_phase31.py",
        "experiments/configs/v3/phase31_coverage.ini",
        "docs/phase31_protocol.md",
    ]
    + [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / "tests/agents31").glob("*.py"))]
)


def load_inputs():
    view = read_json(BASE / "input_views_v2.json")
    catalog = read_json(checked(view["catalog"]))
    document = read_json(checked(view["taskset"]))
    audit_groups(document["tasks"])
    return view, catalog, document["tasks"]


def verify_declaration():
    declaration = read_json(BASE / "declaration.json")
    for record in declaration["source_files"] + declaration["inputs"] + declaration["evidence"]:
        checked(record)
    return declaration


def declare():
    view, _, tasks = load_inputs()
    snapshot = read_json(BASE / "protected_snapshot.json")
    if snapshot["status"] != "PASS" or len(snapshot["files"]) < 20000:
        raise ValueError("Dependency preservation incomplete")
    tests = BASE / "pretest-tests.xml"
    import xml.etree.ElementTree as ET

    suites = ET.parse(tests).getroot()
    if any(int(s.get(k, 0)) for s in suites.iter("testsuite") for k in ("failures", "errors", "skipped")):
        raise ValueError("Pretest must pass without skip")
    coverage = read_json(BASE / "pretest_coverage.json")["totals"]
    if coverage["percent_covered"] < 80 or coverage["num_statements"] < 100:
        raise ValueError("Coverage gate incomplete")
    development = read_json(BASE / "development_v2_complete.json")
    if development["results"] != 720 or development["parent_test_forward"]:
        raise ValueError("Development benchmark incomplete")
    evidence = [
        ref(p)
        for p in (
            tests,
            BASE / "pretest_coverage.json",
            BASE / "development_v2_complete.json",
            BASE / "protected_snapshot.json",
            BASE / "lint.json",
        )
    ]
    document = {
        "phase": 31,
        "version": "phase31.declaration.1",
        "created_at": datetime.now(UTC).isoformat(),
        "task_count": len(tasks),
        "source_files": [ref(ROOT / p) for p in SOURCE_FILES],
        "inputs": [
            view["catalog"],
            view["taskset"],
            ref(ROOT / "uv.lock"),
            ref(ROOT / "experiments/configs/v3/protocol_v3.json"),
        ],
        "evidence": evidence,
        "rubric": {
            "numeric_rtol": 1e-6,
            "numeric_atol": 1e-8,
            "citation": "exact ordered citation list",
            "task_success": "locked status and, for answers, numeric/text/citation tool parity",
            "answer_completion": "succeeded regardless of rubric; separately report correctness",
            "challenge": "explicit synthetic OOD/unsafe/fault injection; never pooled as benign benefit",
        },
        "budgets": {"deadline_seconds": 15, "max_tool_calls": 8, "max_retries_per_tool": 1},
        "runtime": {
            "python": platform.python_version(),
            "execution": "numpy_cpu_local_process",
            "llm": "none",
            "api_keys": False,
        },
        "old_model_test_forward_allowed": False,
    }
    write_once(BASE / "declaration.json", document)
    print({"declaration": ref(BASE / "declaration.json"), "agent_test_started": False}, flush=True)


def run(stage):
    if stage == "test":
        verify_declaration()
    view, catalog, rows = load_inputs()
    wanted = {"test"} if stage == "test" else {"train", "dev"}
    rows = [r for r in rows if r["split"] in wanted]
    if stage == "test":
        claim(
            BASE / "agent_test.claimed.json",
            {
                "declaration": ref(BASE / "declaration.json"),
                "taskset": view["taskset"],
                "started_at": datetime.now(UTC).isoformat(),
                "approved_pairs": [[r["request"]["task_id"], v] for r in rows for v in VARIANTS],
                "evaluation_count": 1,
                "historical_model_test_batches": 0,
            },
        )
    started = time.perf_counter()
    tools = ToolCatalog(catalog)
    cold_ms = (time.perf_counter() - started) * 1000
    executor = ProcessExecutor(tools.call)
    engine = Orchestrator(executor)
    refs = []
    with threadpool_limits(limits=1):
        for i, row in enumerate(rows):
            order = VARIANTS[i % 3 :] + VARIANTS[: i % 3]
            for variant in order:
                name = f"{row['request']['task_id']}_{variant.lower()}.json"
                path = BASE / "results_v2" / row["split"] / name
                if path.exists():
                    if stage == "test":
                        raise ValueError("Consumed agent TEST pair may not be replayed")
                    refs.append(ref(path))
                    continue
                before = time.perf_counter()
                result = engine.run(row["request"], variant, view["taskset"]["sha256"], fault=row["fault"])
                result["wall_latency_ms"] = (time.perf_counter() - before) * 1000
                measured = score(row, result)
                measured["latency_ms"] = result["wall_latency_ms"]
                document = {
                    "task_id": row["request"]["task_id"],
                    "variant": variant,
                    "domain": row["domain"],
                    "split": row["split"],
                    "category": row["category"],
                    "stratum": row["benchmark_stratum"],
                    "output": result,
                    "metrics": measured,
                    "parent_model_test_forward": False,
                }
                write_once(path, document)
                refs.append(ref(path))
            if i % 10 == 0:
                print(f"Phase31 {stage}: {i + 1}/{len(rows)} tasks, {len(refs)} results", flush=True)
    if any(k in sys.modules for k in ("torch", "tensorflow", "keras")):
        raise ValueError("Unexpected native GPU framework import")
    write_once(
        BASE / ("test_complete.json" if stage == "test" else "development_v2_complete.json"),
        {
            "phase": 31,
            "stage": stage,
            "status": "PASS",
            "results": len(refs),
            "result_refs": refs,
            "cold_catalog_ms": cold_ms,
            "parent_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "memory_scope": "Parent process high-water includes preload; child peak is separate, not additive simultaneous peak",
            "parent_test_forward": False,
            "base_models_retrained": 0,
            "api_keys_used": False,
        },
    )
    print({"stage": stage, "results": len(refs), "finished": True}, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("development", "declare", "test"), required=True)
    args = parser.parse_args()
    if args.stage == "declare":
        declare()
    else:
        run(args.stage)


if __name__ == "__main__":
    main()
