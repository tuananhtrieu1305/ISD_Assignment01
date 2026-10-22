"""Read-only validation round-trip diagnostic. No fitting or TEST access."""

import gzip
import json

import numpy as np

from scripts.verify_phase26 import recompute
from src.ch02_ml.protocol import BASE
from src.ch02_ml.test_gate import atomic_json
from src.common.contracts import ROOT, read_json


def main():
    failures = []
    for entry in read_json(BASE / "release.json")["runs"]:
        selected = read_json(BASE / "runs" / entry["run_id"] / "selection.json")
        with gzip.open(ROOT / selected["validation_predictions"]["path"], "rt", encoding="utf-8") as stream:
            rows = [json.loads(line) for line in stream]
        result = read_json(ROOT / selected["validation_metrics"]["path"])
        actual = {row["name"]: row["value"] for row in result["metrics"]}
        task = read_json(ROOT / entry["config"]["path"])["task"]
        for row in recompute(rows, task):
            if row["value"] is not None and not np.isclose(
                row["value"], actual[row["name"]], rtol=1e-10, atol=1e-10
            ):
                failures.append(
                    {
                        "run_id": entry["run_id"],
                        "metric": row["name"],
                        "stored": actual[row["name"]],
                        "float64_roundtrip": row["value"],
                        "absolute_difference": abs(row["value"] - actual[row["name"]]),
                    }
                )
    result = {"validation_only": True, "mismatches": failures}
    atomic_json(BASE / "audit_roundtrip_diagnostic.json", result)
    print(
        json.dumps(
            {
                "validation_only": True,
                "mismatch_count": len(failures),
                "metrics": sorted({row["metric"] for row in failures}),
                "max_absolute_difference": max((row["absolute_difference"] for row in failures), default=0),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
