"""Three dataset tabs and versioned non-neural function contracts for report/API/UI."""

from jsonschema import Draft202012Validator

from src.ch05_knowledge_rag.preservation import ROOT, checked, ref
from src.ch05_knowledge_rag.service import DATASETS, DOMAINS, METHODS, SCOPE
from src.common.contracts import read_json, validate_document

DESCRIPTIONS = {
    "validate": (
        "validate_request(request)",
        "Kiểm tra dataset, miền, độ dài và schema",
        "request JSON",
        "question string",
        "Input lạ hoặc rỗng bị từ chối",
        "src/ch05_knowledge_rag/service.py",
        None,
    ),
    "bm25": (
        "BM25Index.search(query, top_k)",
        "Tìm đoạn chia sẻ từ khóa và điều chỉnh độ dài",
        "string + sparse index",
        "ranked (chunk_id, score)",
        "Không có token trong từ điển: danh sách rỗng",
        "src/term_paper/tools/phase14_rag.py",
        None,
    ),
    "lsa": (
        "DenseLSAIndex.search(query, top_k)",
        "TF–IDF/SVD rồi so vector LSA",
        "string + fitted LSA",
        "ranked (chunk_id, score)",
        "Không có từ trong vocabulary: danh sách rỗng",
        "src/term_paper/tools/phase14_rag.py",
        None,
    ),
    "graph": (
        "graph_candidates(question, graph)",
        "Khớp tối đa bốn nhãn anchor và lấy chunk reachable",
        "question + compact anchor map",
        "candidate IDs + anchor→chunk paths",
        "Không match anchor: không đoán entity",
        "src/ch05_knowledge_rag/runtime.py",
        None,
    ),
    "rrf": (
        "weighted_rrf(rankings, weights, top_k, rrf_k)",
        "Hợp thứ hạng, không cộng trực tiếp BM25 với cosine",
        "ranked lists + weights",
        "ranked IDs",
        "Nhánh rỗng không có đóng góp; trọng số hợp lệ cộng bằng1",
        "src/term_paper/tools/phase15_kgrag.py",
        "score(d) = sum_j w_j / (60 + rank_j(d)); chỉ cộng nhánh chứa d",
    ),
    "answer": (
        "grounded_answer(query, ranking, chunk_lookup, ...)",
        "Chọn trích đoạn đạt overlap, không tạo nội dung mới",
        "question + retrieved chunk texts",
        "answer/citations/abstention",
        "Thiếu bằng chứng hoặc guardrail: từ chối không citation",
        "src/term_paper/tools/phase14_rag.py",
        None,
    ),
    "cite": (
        "KgRagService.compare(request)",
        "Đóng gói V3 job với citation tới container được bảo toàn",
        "answer + chunk/document IDs",
        "five-slot job + evidence",
        "URL cấp dataset; không giả locator raw đã bị lược khỏi bundle",
        "src/ch05_knowledge_rag/service.py",
        None,
    ),
    "browse": (
        "inspect_entity(qid)",
        "Đọc entity JSON và kiểm revision/hash",
        "one of ten allowlisted QIDs",
        "claims/revision/citation",
        "Không có QID: không tải mạng hoặc tạo QA score",
        "src/ch05_knowledge_rag/structural.py",
        None,
    ),
}
COMPOSITIONS = {
    "B0": ["validate", "bm25", "answer", "cite"],
    "B1": ["validate", "lsa", "answer", "cite"],
    "B2": ["validate", "bm25", "lsa", "rrf", "answer", "cite"],
    "B3": ["validate", "bm25", "graph", "answer", "cite"],
    "B4": ["validate", "bm25", "lsa", "graph", "rrf", "answer", "cite"],
}


def pipeline_contract(dataset, method):
    if dataset not in DATASETS or method not in METHODS:
        raise ValueError("Unknown dataset/method")
    available = dataset in DOMAINS
    composition = COMPOSITIONS[method] if available else ["browse"]
    configs = (
        "experiments/configs/ch5/phase14_locked.json",
        "experiments/configs/ch5/phase15_locked.json",
        "apps/api/models/kg_manifest.json",
    )
    return {
        "schema_version": "phase30.retrieval_pipeline.1",
        "dataset_id": dataset,
        "method": method,
        "model_id": f"{dataset}_{method.lower()}_compact_demo",
        "available": available,
        "lifecycle": "reused_legacy_index_demo" if available else "structural_only_unavailable_for_qa",
        "parameter_count": None,
        "learnable_layers": None,
        "functions": [
            {
                "id": key,
                **dict(
                    zip(
                        ("signature", "role", "input", "output", "corner_case", "source", "formula"),
                        DESCRIPTIONS[key],
                    )
                ),
            }
            for key in composition
        ],
        "composition": composition,
        "composition_plain": " → ".join(DESCRIPTIONS[key][1] for key in composition),
        "config_refs": [ref(ROOT / name) for name in configs],
        "demo_scope": SCOPE
        + "; compact label matching is not historic query-ID graph evaluation; LSA is not a pretrained transformer",
        "historical_test_rerun": False,
    }


def validate_pipeline(contract):
    schema = read_json(ROOT / "src/ch05_knowledge_rag/pipeline_contract.schema.json")
    errors = list(Draft202012Validator(schema).iter_errors(contract))
    if errors:
        raise ValueError("Invalid retrieval pipeline contract: " + errors[0].json_path)
    available = contract["dataset_id"] in DOMAINS
    ids = [row["id"] for row in contract["functions"]]
    expected = COMPOSITIONS[contract["method"]] if available else ["browse"]
    if contract["available"] != available or contract["composition"] != expected or ids != expected:
        raise ValueError("Dataset mode/function composition mismatch")
    for record in contract["config_refs"]:
        checked(record)


def catalog():
    parent = read_json(ROOT / "data/catalog_v3.json")
    tabs = []
    for dataset in DATASETS:
        row = next(r for r in parent["datasets"] if r["dataset_id"] == dataset)
        for name in ("source_manifest", "data_card", "eda"):
            checked(row[name])
        tabs.append(
            {
                "dataset_id": dataset,
                "route": "/rag/" + dataset,
                "mode": "qa_demo" if dataset in DOMAINS else "structural_browser",
                "data_card": row["data_card"],
                "source_manifest": row["source_manifest"],
                "eda": row["eda"],
                "domain": DOMAINS.get(dataset),
                "methods": list(METHODS) if dataset in DOMAINS else [],
                "historical_metrics": [ref(ROOT / "artifacts/metrics/ch5/phase15_test_metrics.json")]
                if dataset in DOMAINS
                else [],
                "ui_implementation_phase": 33,
            }
        )
    chapter = {
        "chapter": 5,
        "title": "Knowledge Base, Knowledge Graph và RAG",
        "route": "/rag",
        "dataset_ids": list(DATASETS),
        "families": ["kg_rag"],
        "sections": ["data", "theory", "run", "results", "deployment"],
    }
    validate_document("api#chapter", chapter)
    return {
        "phase": 30,
        "chapter": chapter,
        "tabs": tabs,
        "public_test_rerun": False,
        "scope": "Dataset-tab descriptors for Phase33; not a live React implementation",
    }
