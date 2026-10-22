"""Offline entity/revision browser with exact trusted snapshot provenance."""

import re

from src.ch05_knowledge_rag.preservation import checked
from src.common.contracts import read_json

INDEX = "data/raw/ch5/wikidata/snapshot_index.json"
INDEX_SHA = "1ba148c6369a68963b0da049a58fea722372ba213f57e0d88e402f3d587ac64e"


def inspect_entity(qid):
    if not isinstance(qid, str) or not re.fullmatch(r"Q[1-9][0-9]{0,12}", qid):
        raise ValueError("Require an allowlisted Wikidata QID, not a path or URL")
    index = read_json(checked({"path": INDEX, "sha256": INDEX_SHA}))
    entry = next((r for r in index["entities"] if r["qid"] == qid), None)
    if entry is None:
        raise ValueError("QID not present in the frozen ten-entity snapshot")
    path = checked(
        {"path": "data/raw/ch5/" + entry["entity_relative_path"], "sha256": entry["entity_sha256"]}
    )
    entity = read_json(path)["entities"][qid]
    count = sum(len(items) for items in entity["claims"].values())
    if entity["lastrevid"] != entry["revision_id"] or count != entry["claim_count"]:
        raise ValueError("Entity revision/count mismatch")
    return {
        "qid": qid,
        "label": entity.get("labels", {}).get("en", {}).get("value", qid),
        "description": entity.get("descriptions", {}).get("en", {}).get("value", ""),
        "revision_id": entity["lastrevid"],
        "claim_count": count,
        "property_count": len(entity["claims"]),
        "sample_claims": [
            {"property": key, "statement": entity["claims"][key][0]} for key in sorted(entity["claims"])[:5]
        ],
        "citation": {
            "evidence_id": "wikidata_" + qid.lower(),
            "source_url": entry["entity_endpoint"],
            "locator": f"{qid}@{entry['revision_id']}",
            "source_sha256": entry["entity_sha256"],
        },
        "qa_benchmark": False,
        "training_executed": False,
        "test_evaluation_executed": False,
    }
