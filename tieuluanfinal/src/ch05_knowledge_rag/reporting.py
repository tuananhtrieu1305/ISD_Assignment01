"""Saved-output consistency checks and source-derived Chapter5 manuscript revision."""

import csv
import json
import re

from src.ch05_knowledge_rag.catalog import DESCRIPTIONS
from src.ch05_knowledge_rag.preservation import LOCKED_SHA, ROOT, SEAL, checked, ref
from src.common.contracts import read_json


def historical_metrics():
    csv_path = ROOT / "artifacts/metrics/ch5/phase15_test_metrics.csv"
    json_path = ROOT / "artifacts/metrics/ch5/phase15_test_metrics.json"
    document = read_json(json_path)
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    keys, count = set(), 0
    for row in rows:
        domain, method = row["domain"], row["model_id"]
        if (domain, method) in keys:
            raise ValueError("Duplicate historical metric row")
        keys.add((domain, method))
        original = document["test"][domain][method]
        for name, value in row.items():
            if name not in {"domain", "model_id"} and float(value) != original[name]:
                raise ValueError("Historical CSV/JSON metric mismatch")
        pred = ROOT / f"artifacts/predictions/ch5/phase15/{domain}/{method}_test.jsonl"
        query_ids = set()
        with pred.open(encoding="utf-8") as stream:
            for line in stream:
                item = json.loads(line)
                if (
                    item["split"] != "test"
                    or item["model_id"] != method
                    or item["domain"] != domain
                    or item["config_sha256"] != LOCKED_SHA
                    or item["query_id"] in query_ids
                    or not set(item["citations"]) <= set(item["retrieved_chunk_ids"])
                ):
                    raise ValueError("Saved prediction identity/citation mismatch")
                query_ids.add(item["query_id"])
        if len(query_ids) != int(row["query_count"]):
            raise ValueError("Historical query count mismatch")
        count += len(query_ids)
    if keys != {(domain, f"B{i}") for domain in ("medical", "finance") for i in range(5)} or count != 6045:
        raise ValueError("Incomplete historical B0–B4 prediction set")
    seal = read_json(ROOT / SEAL)
    if seal["run_count"] != 1 or seal["status"] != "COMPLETE":
        raise ValueError("Original TEST seal changed")
    for old in seal["prediction_artifacts"]:
        checked(
            {
                "path": old["path"].replace(
                    "term_paper/knowledge_rag/artifacts/predictions/", "artifacts/predictions/ch5/"
                ),
                "sha256": old["sha256"],
            }
        )
    return {
        "status": "PASS",
        "rows": rows,
        "saved_prediction_rows": count,
        "test_run_count": 1,
        "new_test_evaluation_executed": False,
        "metric_sources": [ref(csv_path), ref(json_path)],
        "seal": ref(ROOT / SEAL),
    }


def render_manuscript(old):
    text = old.split("## 5.6.")[0]
    text = re.sub(r"<!--.*?-->\s*", "", text, flags=re.DOTALL)
    start = text.index("\\[\n\\operatorname{BM25}")
    end = text.index("\\]", start) + 2
    text = text[:start] + text[end:]
    text = text.replace(
        "Với truy vấn (q) và tài liệu (d), điểm được tính theo dạng:",
        "Từ khóa hiếm có giá trị hơn từ phổ biến; lặp một từ rất nhiều lần không làm điểm tăng vô hạn. Đoạn dài được điều chỉnh để không tự chiếm ưu thế.",
    )
    text = text.replace(
        "trong đó (k_1=1,5) và (b=0,75).",
        "Hai mức điều chỉnh đã khóa là k1=1,5 (bão hòa tần suất) và b=0,75 (chuẩn hóa độ dài).",
    )
    text = text.replace(
        "mở rộng tối đa hai hop và xếp đoạn theo khoảng cách graph",
        "mở rộng tối đa hai hop để lấy tập ứng viên; `graph_filter_ranking` ưu tiên thứ tự BM25 trong tập đó, rồi bổ sung ID còn lại theo thứ tự cố định",
    )
    text = text.replace(
        "Các mẫu đầy đủ nằm trong dataset card và processed JSONL, tránh đưa dữ liệu dài vào thân bài.",
        "Các mẫu hiện hành nằm trong ba EDA card Phase24; đây là ví dụ dữ liệu, không phải output mô hình được chấm lại. Các processed JSONL lớn lịch sử không cần được dựng lại để demo bundle compact.",
    )
    text = text.replace("3/62 TEST entity link", "3/62 focus/entity local link")
    text = text.replace("../assets/ch5_knowledge_rag/", "../../assets/ch5_knowledge_rag/")
    text = text.replace(
        "../../assets/ch5_knowledge_rag/ch5_test_recall_at_5.svg",
        "../../../artifacts/figures/phase30/historical_recall.png",
    )
    # Keep every original literature citation; only presentation/runtime scope changes.
    text = text.replace(
        "## 5.1. Mở đầu",
        "**Ghi nhận V3:** số liệu/citation là baseline đã khóa; Phase30 chỉ kiểm saved outputs và tích hợp, không mở public TEST. Wikidata không phải benchmark QA thứ ba.\n\n## 5.1. Mở đầu",
    )
    text = text.replace(
        "Trọng số sparse 0,75 được chọn",
        "Ở công thức trên, d là chunk, j là nhánh retriever, w_j là trọng số, r_j(d) là hạng của chunk; 60 là hằng làm trơn đã khóa, không phải xác suất. Nhánh không chứa chunk đóng góp0. Ví dụ synthetic: chunk đứng hạng1/2 ở hai nhánh cho điểm 0,75/61 +0,25/62 ≈0,01633. Trọng số sparse 0,75 được chọn",
    )
    functions = []
    for key, values in DESCRIPTIONS.items():
        signature, role, input_type, output_type, corner, source, _ = values
        functions.append(
            f"| `{key}` / `{signature}` | {role} | {input_type} → {output_type}; {corner}. Source: `{source}` |"
        )
    tail = (
        """
## 5.6. Hợp các hàm và contract dùng chung

Ví dụ demo y khoa nhận một câu hỏi, trả năm slot B0–B4 trên cùng input; mỗi slot có thể
trả lời trích xuất hoặc từ chối. Đây là retrieval CPU dùng index cũ, không phải mô hình
scratch/Keras/PyTorch mới hay mạng sáu tầng. Quy tắc độ sâu thuộc Chương2–4; số tham số
neural/layer ở contract Chương5 là null vì không áp dụng, không dùng0 thay cho số chưa đo.

Hợp hàm tổng thể được hiểu là `F = cite ∘ answer ∘ retrieve ∘ validate`:
**request → kiểm tra → các nhánh truy hồi → fusion nếu có → chọn trích đoạn → citation/job**.
BM25/LSA/graph là các nhánh song song; ký hiệu hợp hàm không có nghĩa bắt mọi slot chạy
tuần tự qua cả ba. B3 chỉ nhận candidate từ graph nhưng vẫn dùng lexical order để xếp
ứng viên; “graph-only” không có nghĩa không sử dụng BM25 cho thứ tự trong candidate set.

| Function/signature | Vai trò | Input/output và trường hợp biên |
|---|---|---|
"""
        + "\n".join(functions)
        + """

Bảng này được sinh từ `DESCRIPTIONS` trong `src/ch05_knowledge_rag/catalog.py`, cùng nguồn
với15 pipeline contract ở `artifacts/manifests/phase30/contracts/`. Các API request/job/
citation vẫn kiểm bằng schema V3 gốc; extension `phase30.retrieval_pipeline.1` không sửa
schema neural hoặc protocol đã khóa. Năm contract Wikidata ghi unavailable cho QA,
không tạo thêm năm kết quả benchmark. Công cụ riêng `inspect_entity('Q12206')` trả revision,
186 claim và hash snapshot; không tải mạng hay sinh câu trả lời dựa trên một QA gold giả.

Đoạn code kết nối chính, với chữ ký/giá trị đầy đủ nằm trong source:

```python
candidates, paths = graph_candidates(question, bundle.graph[domain])
rankings = compare_rankings(sparse, dense, candidates, 0.75,
                           {"sparse": 0.6, "dense": 0.1, "graph": 0.3}, 10, 60)
# Mỗi ranking đi qua grounded_answer, rồi đóng gói job/citation.
```

Demo câu hỏi tự do dùng graph anchor compact, khác graph/query-ID lịch sử của TEST.
Không xem output demo là lần chấm lại hoặc tái hiện hệt ranking TEST. Corpus bundle không
còn metadata split/URL raw từng chunk; MedQuAD demo là câu hỏi minh họa tự soạn,
không gán TRAIN/TEST. FinQA demo dùng câu hỏi TRAIN trong EDA card. Citation V3 có
`source_sha256` của container `kg_chunks.jsonl.gz`, locator chunk/document ID và URL
nguồn cấp dataset. Hash xác minh container local nêu ở locator, không phải bytes của
URL landing page; không giả rằng đã phục hồi raw URL/locator từng đoạn bị lược khỏi bundle.

![p95 TEST lịch sử, không phải latency demo WSL mới](../../../artifacts/figures/phase30/historical_latency.png)

**Hình 5.6. p95 latency đọc nguyên artifact Phase15; không đo lại trên runtime mới.**
Số đo demo chỉ cộng component dùng chung và answer, loại cold load/serialize; không phải
năm benchmark độc lập hoặc HTTP latency và không gộp với số TEST trong hình.

![Citation hợp lệ không có nghĩa là gold evidence](../../../artifacts/figures/phase30/historical_citations.png)

**Hình 5.7. Citation validity và gold precision lịch sử cho hai miền.**
Validity1,000 trong khi gold precision thấp là bằng chứng cụ thể rằng nguồn có thể tồn tại
nhưng không đúng evidence cần thiết. Giữ hai phép đo riêng giúp tránh trình bày quá mức.

## 5.7. Cầu nối sang hệ đa tác tử

Prototype trước đây có một router chọn medical/finance rồi gọi retriever. Đây chưa phải
benchmark hệ nhiều agent độc lập. Chương5 dừng ở bằng chứng và truy hồi; Chương6 sẽ so
A0/A1/A2 với router, specialist, verifier và reporter, dùng tool/evidence đã khóa của chương
này. Hệ nhiều agent không mặc nhiên sửa được nhược điểm reasoning số FinQA hoặc coverage
graph; các lợi ích đó phải được đo riêng ở Phase31.

## 5.8. Triển khai ngắn gọn

Runtime CPU kế thừa sáu artifact68.393.687 byte,87.183 chunk và203 graph anchor;
không cần GPU, Neo4j server, API key hoặc gọi LLM bên ngoài. V3 lazy loader kiểm manifest,
role/path/size/hash/budget trước khi nạp bốn index joblib local được allowlist. Không nhận
uploaded pickle hoặc đường dẫn từ request. Namespace `term_paper` giữ để load class cũ;
không fit/rebuild/re-serialize artifact vì migration. Lỗi bundle trả đủ slot unavailable
với lỗi có cấu trúc. Guardrail từ chối câu nguy hiểm trước khi nạp model, nhưng chỉ là rule
hữu hạn, không bảo đảm an toàn tổng quát.

Ba notebook và CLI `scripts.demo_phase30` cho local demo; catalog đã có descriptor cho ba
dataset tab. API contract đã kiểm local, còn tích hợp HTTP/React V3 ở Phase32–33 và deploy
Render phải được kiểm riêng. Không dùng ảnh giao diện Agent cũ như bằng chứng cloud hiện
tại. Hướng dẫn vận hành dài đặt `docs/phase30_operations.md`; deploy không thành chương riêng.

## 5.9. Tiểu kết

KG hỗ trợ truy hồi rõ ở medical, nhưng B4 không vượt BM25 trên finance. Chất lượng retrieval
và tính hợp lệ citation không giải quyết thay reasoning số, chẩn đoán hoặc tư vấn tài chính.
Phase30 giữ nguyên metric, citation lịch sử, raw/config và TEST run_count1; bản V3 chỉ thêm
contract/provenance và demo có phạm vi rõ. Ba nguồn thật gồm hai miền QA và một snapshot
cấu trúc, không phải ba phép đánh giá QA tương đương.
"""
    )
    return text.rstrip() + "\n" + tail.lstrip()
