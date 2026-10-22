"""Capture and verify preserved Chapter5 assets; never invokes an evaluator."""

import json

from src.ch05_knowledge_rag.preservation import create_snapshot

if __name__ == "__main__":
    result = create_snapshot()
    print(
        json.dumps(
            {
                "status": result["status"],
                "preserved_files": len(result["files"]),
                "baseline": result["baseline"],
                "dependencies": result["dependencies"],
            },
            indent=2,
        )
    )
