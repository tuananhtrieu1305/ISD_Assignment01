"""Exercise migrated inference artifacts with public demo questions, not TEST evaluation."""

import json
from pathlib import Path

from apps.api.app import app


def main():
    results = []
    with app.test_client() as client:
        readiness = client.get("/ready")
        assert readiness.status_code == 200, readiness.get_json()
        for domain, question in (
            ("medical", "What complications can diabetes cause?"),
            ("finance", "How did operating revenue change in the annual report?"),
        ):
            response = client.post("/api/agent/query", json={"domain": domain, "question": question})
            payload = response.get_json()
            assert response.status_code == 200, payload
            results.append({"domain": domain, "http_status": response.status_code, "response": payload})
    path = Path(__file__).resolve().parents[1] / "artifacts/manifests/phase20/runtime-smoke.json"
    path.write_text(json.dumps({"status": "PASS", "results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "domains": len(results)}))


if __name__ == "__main__":
    main()
