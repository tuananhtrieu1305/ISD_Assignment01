"""Presentation-only r2 separates TEST errors from challenge; no metric rewrite."""

import csv
from collections import Counter

from src.ch05_knowledge_rag.preservation import ROOT, ref
from src.ch05_knowledge_rag.reporting import render_manuscript
from src.common.contracts import read_json


def error_scope():
    path = ROOT / "artifacts/metrics/ch5/phase15_error_analysis.csv"
    data = {
        split: {domain: Counter() for domain in ("medical", "finance")} for split in ("test", "challenge")
    }
    counts = {domain: Counter() for domain in ("medical", "finance")}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["split"] not in data or row["domain"] not in counts:
                raise ValueError("Unexpected error-analysis scope")
            data[row["split"]][row["domain"]].update(row["categories"].split("|"))
            counts[row["domain"]][row["split"]] += 1
    aggregate = {domain: dict(data["test"][domain] + data["challenge"][domain]) for domain in counts}
    original = read_json(ROOT / "artifacts/metrics/ch5/phase15_test_metrics.json")["error_category_counts"]
    if aggregate != original or counts != {
        "medical": {"test": 62, "challenge": 8},
        "finance": {"test": 1147, "challenge": 8},
    }:
        raise ValueError("Saved TEST/challenge aggregates disagree; do not alter metrics to pass")
    return {
        **{split: {domain: dict(c) for domain, c in domains.items()} for split, domains in data.items()},
        "aggregate": aggregate,
        "counts": {k: dict(v) for k, v in counts.items()},
        "sources": [ref(path), ref(ROOT / "artifacts/metrics/ch5/phase15_test_metrics.json")],
        "new_test_evaluation_executed": False,
    }


def render_manuscript_r2(old):
    text = render_manuscript(old)
    folder = "../../../artifacts/figures/phase30/r2/"
    for old_path, new_name in (
        ("../../assets/ch5_knowledge_rag/ch5_dataset_overview.png", "dataset_overview.png"),
        ("../../assets/ch5_knowledge_rag/ch5_graph_schema.svg", "graph_paths.png"),
        ("../../assets/ch5_knowledge_rag/ch5_validation_ablation.svg", "validation_ablation.png"),
        ("../../assets/ch5_knowledge_rag/ch5_error_distribution.svg", "test_errors.png"),
    ):
        text = text.replace(old_path, folder + new_name)
    text = text.replace(
        "8 lỗi liên quan entity linking", "0 nhãn entity linking trên TEST (8 nhãn này thuộc challenge)"
    )
    text = text.replace(
        "1.061 entity-linking observation",
        "1.053 entity-linking observation trên TEST;8 nhãn bổ sung thuộc challenge",
    )
    text = text.replace(
        "Các con số lớn không được cộng",
        "JSON aggregate gốc cộng TEST+challenge nên giữ1.061/8 nhãn entity linking finance/medical; hình và đoạn phân tích TEST ở đây chỉ dùng1.053/0. Không đổi CSV/JSON gốc. Các con số lớn không được cộng",
    )
    text = text.replace(
        "**Hình 5.2. Schema property graph và các quan hệ được phép trong pipeline KG-RAG.**",
        "**Hình 5.2. Tập con các cạnh phục vụ truy hồi trong schema property graph; không phải toàn bộ topology.**",
    )
    text = text.replace(
        "*Nguồn: `graph_schema.md` và `phase13_graph_manifest.json`; hình sinh bởi `build_phase13_graphs.py`.*",
        "*Nguồn: `docs/ch5/graph_schema.md`, extractor `build_phase13_graphs.py` và `phase13_graph_manifest.json`; hình vẽ lại ở presentation r2. Bảng mô tả cũ còn một dòng nói kế thừa gold document; extractor và mục chống rò rỉ thực tế dùng longest exact phrase từ câu hỏi để tạo ASKS_ABOUT, không dùng gold để chọn anchor.*",
    )
    text = text.replace(
        "Demo câu hỏi tự do dùng graph anchor compact, khác graph/query-ID lịch sử của TEST.",
        "Demo tìm trong toàn corpus compact không còn split metadata; protocol benchmark lịch sử giới hạn candidate theo split. Demo câu hỏi tự do dùng graph anchor compact, khác graph/query-ID lịch sử của TEST.",
    )
    return text
