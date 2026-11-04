"""Generate Chapter6 from saved outputs, plus separate TRAIN-only notebook demos."""

import csv
import io
import json
import subprocess
import sys
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nbformat
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from scripts.phase31_benchmark import BASE, load_inputs
from scripts.verify_phase31 import audit_results
from src.ch05_knowledge_rag.preservation import ref
from src.ch06_multi_agent.core import DOMAINS, VARIANTS
from src.ch06_multi_agent.service import pipeline_contract
from src.common.artifact_core import write_once
from src.common.contracts import ROOT, read_json, validate_document

FIGURES = ROOT / "artifacts/figures/phase31"
METRICS = ROOT / "artifacts/metrics/phase31"
CARDS = ROOT / "report/references/dataset_cards/v3_agent"
LABELS = {"diabetes": "Tiểu đường", "house": "Giá nhà", "gold": "Giá vàng"}
COLORS = {"A0": "#526d82", "A1": "#db9c30", "A2": "#16867c"}
RATE_KEYS = (
    "task_success",
    "answer_completion",
    "routing_accuracy",
    "numeric_parity",
    "citation_correctness",
    "unsupported_claim",
    "unsafe_claim",
    "refusal_correctness",
)


def text_once(path, text):
    encoded = text.encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != encoded:
            raise ValueError("Generated artifact changed; use a versioned revision: " + path.name)
    else:
        with path.open("xb") as stream:
            stream.write(encoded)
    return ref(path)


def markdown_table(headers, rows):
    def clean(value):
        return str(value).replace("|", "\\|").replace("\n", " ")

    return (
        "\n".join(
            ["| " + " | ".join(map(clean, headers)) + " |", "|" + "---|" * len(headers)]
            + ["| " + " | ".join(map(clean, row)) + " |" for row in rows]
        )
        + "\n"
    )


def aggregate(rows):
    groups = defaultdict(list)
    for row in rows:
        for scope in (row["category"], row["stratum"], "all"):
            groups[(row["domain"], row["split"], scope, row["variant"])].append(row["metrics"])
    result = []
    for key, values in sorted(groups.items()):
        record = dict(zip(("domain", "split", "scope", "variant"), key))
        record["tasks"] = len(values)
        for name in RATE_KEYS:
            measured = [r[name] for r in values if r[name] is not None]
            record[name] = float(np.mean(measured)) if measured else None
            record[name + "_n"] = len(measured)
        latency = [r["latency_ms"] for r in values]
        record["latency_p50_ms"], record["latency_p95_ms"] = map(float, np.percentile(latency, [50, 95]))
        for name in ("message_count", "tool_calls"):
            record[name + "_mean"] = float(np.mean([r[name] for r in values]))
        record["peak_child_rss_bytes"] = max(r["peak_child_rss_bytes"] for r in values)
        result.append(record)
    return result


def check_summary(rows):
    pairs = {(r.get("task_id"), r.get("variant")) for r in rows}
    if len(rows) != 900 or len(pairs) != 900:
        raise ValueError("Require900 unique measured task/variant records")
    if any(
        sum(r["domain"] == d and r["split"] == s and r["variant"] == v for r in rows) != n
        for d in DOMAINS
        for s, n in (("train", 60), ("dev", 20), ("test", 20))
        for v in VARIANTS
    ):
        raise ValueError("Incorrect per-domain/split matrix")


def csv_once(path, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return text_once(path, stream.getvalue())


def save_figure(fig, name):
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{name}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(FIGURES / f"{name}.svg", bbox_inches="tight", facecolor="white", metadata={"Date": None})
    plt.close(fig)
    return [ref(FIGURES / f"{name}.{suffix}") for suffix in ("png", "svg")]


def box(ax, x, y, w, h, text, color="#e7f2f0"):
    ax.add_patch(
        FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", facecolor=color, edgecolor="#748b95")
    )
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=10)


def arrow(ax, a, b):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=13, color="#526d82", lw=1.3))


def figures(groups, rows):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "svg.fonttype": "none"})
    artifacts = []
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    ax.set(xlim=(0, 10), ylim=(0, 5))
    ax.axis("off")
    box(ax, 0.1, 2.1, 1.4, 0.8, "Task\n+ policy")
    box(ax, 2.0, 2.1, 1.3, 0.8, "Router")
    for y, label in [
        (3.5, "Diabetes\nCDC / MedQuAD"),
        (2.05, "House\nAmes / BIS"),
        (0.6, "Gold\nPink Sheet"),
    ]:
        box(ax, 3.9, y, 2.1, 0.9, label)
        arrow(ax, (3.3, 2.5), (3.9, y + 0.45))
        arrow(ax, (6.0, y + 0.45), (6.6, 2.5))
    box(ax, 6.6, 2.1, 1.2, 0.8, "Verifier")
    box(ax, 8.4, 2.1, 1.4, 0.8, "Reporter\n+ trace")
    arrow(ax, (1.5, 2.5), (2.0, 2.5))
    arrow(ax, (7.8, 2.5), (8.4, 2.5))
    ax.text(
        5,
        0.05,
        "A0: direct tool  |  A1: router + specialist  |  A2: thêm verifier + reporter\nBa miền dùng chung cơ chế; model và evidence riêng. Không LLM/API key.",
        ha="center",
        fontsize=10,
    )
    artifacts += save_figure(fig, "architecture")
    categories = ["numeric", "evidence", "ood", "unsafe", "tool_failure"]
    names = ["Số", "Nguồn", "OOD", "Unsafe", "Tool lỗi"]
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.5), sharey=True)
    for ax, domain in zip(axes, DOMAINS, strict=True):
        for i, variant in enumerate(VARIANTS):
            chosen = [
                next(
                    r
                    for r in groups
                    if r["domain"] == domain
                    and r["split"] == "test"
                    and r["scope"] == c
                    and r["variant"] == variant
                )["task_success"]
                for c in categories
            ]
            ax.bar(
                np.arange(5) + (i - 1) * 0.24,
                np.asarray(chosen) * 100,
                0.24,
                label=variant,
                color=COLORS[variant],
            )
        ax.set_title(LABELS[domain])
        ax.set_xticks(range(5), names, rotation=25, ha="right")
        ax.set_ylim(0, 112)
        ax.grid(axis="y", alpha=0.18)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Đạt rubric (%) — mỗi ô n=4 task")
    axes[-1].legend(loc="upper right", ncols=3, frameon=False, fontsize=8)
    fig.suptitle("TEST tác tử: tách ca bình thường và challenge tổng hợp", fontsize=13)
    fig.tight_layout()
    artifacts += save_figure(fig, "test_quality")
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.3))
    for ax, domain in zip(axes, DOMAINS, strict=True):
        chosen = [
            next(
                r
                for r in groups
                if r["domain"] == domain
                and r["split"] == "test"
                and r["scope"] == "all"
                and r["variant"] == v
            )
            for v in VARIANTS
        ]
        p50 = [r["latency_p50_ms"] for r in chosen]
        p95 = [r["latency_p95_ms"] for r in chosen]
        ax.bar(np.arange(3) - 0.17, p50, 0.34, color="#16867c", label="p50")
        ax.bar(np.arange(3) + 0.17, p95, 0.34, color="#526d82", label="p95")
        ax.set_xticks(range(3), VARIANTS)
        ax.set_title(LABELS[domain])
        ax.set_ylabel("Wall time / task (ms)")
        ax.grid(axis="y", alpha=0.18)
        ax.set_axisbelow(True)
    axes[-1].legend(frameon=False)
    fig.suptitle("Warm catalog; gồm process + đóng gói/schema; không phải HTTP SLA", fontsize=12)
    fig.tight_layout()
    artifacts += save_figure(fig, "latency")
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.3))
    for ax, metric, title in [
        (axes[0], "unsupported_claim", "Phản hồi không được bằng chứng hỗ trợ"),
        (axes[1], "unsafe_claim", "Trả kết quả cho yêu cầu unsafe"),
    ]:
        for i, variant in enumerate(VARIANTS):
            values = [
                next(
                    r
                    for r in groups
                    if r["domain"] == d
                    and r["split"] == "test"
                    and r["scope"] == "challenge"
                    and r["variant"] == variant
                )[metric]
                * 100
                for d in DOMAINS
            ]
            ax.bar(np.arange(3) + (i - 1) * 0.24, values, 0.24, color=COLORS[variant], label=variant)
        ax.set_xticks(range(3), [LABELS[d] for d in DOMAINS])
        ax.set_title(title, fontsize=11)
        ax.set_ylabel("Tỷ lệ (%) — challenge n=12 / miền / variant")
        ax.set_ylim(0, 25)
        ax.grid(axis="y", alpha=0.18)
        ax.set_axisbelow(True)
    axes[-1].legend(frameon=False, ncols=3)
    fig.tight_layout()
    artifacts += save_figure(fig, "safety")
    example = next(
        r
        for r in rows
        if r["split"] == "test"
        and r["domain"] == "gold"
        and r["category"] == "tool_failure"
        and r["variant"] == "A2"
        and r["output"]["verification"] == "rejected"
    )
    nodes = example["output"]["trace"]["nodes"]
    fig, ax = plt.subplots(figsize=(10.8, 3.7))
    ax.axis("off")
    ax.set(xlim=(0, 10), ylim=(0, 3))
    for i, node in enumerate(nodes):
        x = 0.3 + i * 2.4
        box(ax, x, 1.2, 1.8, 1.0, f"{node['agent']}\n{node['outcome']}\n{node['duration_ms']:.2f} ms")
        if i:
            arrow(ax, (x - 0.6, 1.7), (x, 1.7))
    ax.text(
        5,
        0.5,
        f"{example['task_id']} | TEST mới, fault injection numeric\nReceipt hash không khớp → abstain; không tạo dự báo thay thế.",
        ha="center",
        fontsize=10,
    )
    artifacts += save_figure(fig, "trace_example")
    return artifacts


def data_cards(tasks, catalog, taskset_ref):
    files, descriptions = [], []
    parent_ids = {
        "diabetes": ["ch2_cdc_diabetes", "ch5_medquad_diabetes"],
        "house": ["ch2_ames_housing", "ch4_bis_house_prices"],
        "gold": ["ch4_gold_pink_sheet"],
    }
    for domain in DOMAINS:
        parents = [
            read_json(ROOT / f"artifacts/manifests/datasets/{key}.json")["contract"]
            for key in parent_ids[domain]
        ]
        source_rows = [
            [
                p["dataset_id"],
                p["source"]["url"],
                p["source"]["license_note"],
                sum(f["size_bytes"] for f in p["files"]),
            ]
            for p in parents
        ]
        mine = [r for r in tasks if r["domain"] == domain]
        examples = [r for r in mine if r["category"] == "numeric"][:3] + [
            r for r in mine if r["category"] == "evidence"
        ][:2]
        sample_rows = [
            [
                r["request"]["task_id"],
                r["request"]["question"],
                json.dumps(r["gold"]["payload"]["values"], ensure_ascii=False),
                r["gold"]["payload"]["text"][:160],
            ]
            for r in examples
        ]
        text = (
            f"# ch6_{domain}_tasks — {LABELS[domain]}\n\n"
            + "100 task synthetic-template trên nguồn thật;60/20/20 theo nhóm. Không phải100 người bệnh/căn nhà mới.\n\n"
        )
        text += markdown_table(
            ["Parent", "Link snapshot", "Điều khoản/citation", "Raw parent bytes (không copy)"], source_rows
        )
        text += f"\nTask set dùng chung3 miền: `{taskset_ref['path']}`, {(ROOT / taskset_ref['path']).stat().st_size} byte, SHA-256 `{taskset_ref['sha256']}`.\n"
        text += "Catalog canonical input/evidence dùng chung:60 record/miền (40 numeric +20 evidence). Không nhân bản raw.\n\n"
        text += "Schema: request(task_id, domain_hint, question, record_id, operation); split/group/source_group/fault/gold chỉ harness. Mỗi loại numeric/evidence/OOD/unsafe/tool_failure có20 task, mỗi split12/4/4. Group nguyên template và source/document, overlap0.\n\n"
        text += markdown_table(
            ["Task", "Input câu hỏi (synthetic)", "Output số thật từ tool", "Trích output tool/evidence"],
            sample_rows,
        )
        text += "\nKhông thiếu task/gold. Numeric dùng parent TRAIN; Gold window có thể chồng context. MedQuAD chỉ corpus evidence, không QA TEST label. Policy/challenge là ca tổng hợp đã gắn nhãn, không phân bố nhu cầu thực. Gold numeric parity là khớp tool, không predictive accuracy.\n"
        text += "\nNhận xét: thiết kế cân bằng thuận tiện kiểm pipeline nhưng nhỏ, rule/ID-bound, không chứng minh hiểu ngôn ngữ tự do. Ames là USD giá bán lịch sử; BIS là chỉ số danh nghĩa2010=100, không so trực tiếp hai đơn vị. CDC probability không phải chẩn đoán; Pink Sheet không phải giá giao dịch hiện tại. Citation hash kiểm local container, URL cấp nguồn.\n"
        path = CARDS / f"ch6_{domain}_tasks.md"
        files.append(text_once(path, text))
        descriptions.append(
            {
                "dataset_id": f"ch6_{domain}_tasks",
                "domain": domain,
                "status": "derived_ready",
                "parent_dataset_ids": parent_ids[domain],
                "source_manifest": [
                    ref(ROOT / f"artifacts/manifests/datasets/{p}.json") for p in parent_ids[domain]
                ],
                "data_card": ref(path),
                "tasks": 100,
                "split_counts": {"train": 60, "dev": 20, "test": 20},
                "taskset": taskset_ref,
                "question_origin": "synthetic_template",
                "raw_duplicated": False,
            }
        )
    return files, descriptions


def notebooks():
    files = []
    for domain in DOMAINS:
        code = (
            "import json, subprocess, sys\nfrom pathlib import Path\n"
            "root = Path.cwd().resolve()\n"
            "while not (root / 'TIEU_LUAN_AI_V3_EXECUTION_PLAN.md').is_file():\n"
            "    if root == root.parent: raise RuntimeError('Open from repository tree')\n"
            "    root = root.parent\n"
            f"p = subprocess.run([sys.executable, '-m', 'scripts.demo_phase31', '--domain', '{domain}'], cwd=root, capture_output=True, text=True, check=True)\n"
            "demo = json.loads(p.stdout)\n"
            "print(json.dumps({v: {'status': r['trace']['status'], 'values': r['values'], 'nodes': len(r['trace']['nodes']), 'citations': r['trace']['citations']} for v,r in demo['outputs'].items()}, ensure_ascii=False, indent=2))\n"
        )
        run = subprocess.run(
            [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True
        )
        result = json.loads(run.stdout)
        if set(result) != set(VARIANTS) or any(r["status"] != "succeeded" for r in result.values()):
            raise ValueError("Real CPU notebook demo failed")
        notebook = nbformat.v4.new_notebook(
            cells=[
                nbformat.v4.new_markdown_cell(
                    f"# Chương6 — {LABELS[domain]}\nChọn kernel WSL ai-v3-torch. TRAIN-only demo, không benchmark/TEST, không lời khuyên chuyên môn.\nCode dùng subprocess riêng vì fork executor không chạy trong thread Jupyter. Không gọi API mạng."
                ),
                nbformat.v4.new_code_cell(
                    code,
                    execution_count=1,
                    outputs=[nbformat.v4.new_output("stream", name="stdout", text=run.stdout)],
                ),
            ],
            metadata={
                "kernelspec": {
                    "display_name": "AI V3 Torch (WSL)",
                    "language": "python",
                    "name": "ai-v3-torch",
                }
            },
        )
        files.append(
            text_once(
                ROOT / f"experiments/notebooks/v3/ch06_multi_agent/{domain}.ipynb",
                nbformat.writes(notebook) + "\n",
            )
        )
        write_once(
            BASE / f"notebook_{domain}.json",
            {
                "status": "PASS",
                "slots": 3,
                "input_split": "train",
                "execution": "generator-owned code via subprocess; not Jupyter UI QA",
                "result": result,
            },
        )
        files.append(ref(BASE / f"notebook_{domain}.json"))
    return files


def manuscript(groups, tasks, descriptions, contracts):
    summary = [r for r in groups if r["split"] == "test" and r["scope"] == "all"]
    benign = [r for r in groups if r["split"] == "test" and r["scope"] == "benign"]
    results = [
        [
            LABELS[r["domain"]],
            r["variant"],
            f"{r['task_success'] * 100:.1f}% ({r['tasks']})",
            f"{r['answer_completion'] * 100:.1f}%",
            f"{r['latency_p50_ms']:.2f}/{r['latency_p95_ms']:.2f}",
            f"{r['message_count_mean']:.2f}",
            f"{r['peak_child_rss_bytes'] / 1024**2:.1f}",
        ]
        for r in summary
    ]
    function_rows = []
    seen = set()
    for contract in contracts:
        for f in contract["functions"]:
            if f["id"] not in seen:
                seen.add(f["id"])
                function_rows.append(
                    [f["id"], f["signature"], f["role"], f["input"] + " → " + f["output"], f["corner_case"]]
                )
    sample = next(r for r in tasks if r["domain"] == "gold" and r["category"] == "numeric")
    text = """# CHƯƠNG 6. HỆ ĐA TÁC TỬ (MULTI-AGENT SYSTEMS)

## 6.1. Agent và phối hợp nhiều agent

Một câu hỏi về giá vàng có thể cần chọn đúng miền, gọi mô hình, kiểm nguồn rồi trình bày
kết quả. Nếu một thành phần vừa chọn tool vừa tự viết mọi câu trả lời, lỗi ở bước trước
có thể đi thẳng tới người đọc. Chương này tách các trách nhiệm đó để quan sát được lỗi
và chi phí phối hợp. Ví dụ tiểu đường dùng CDC/MedQuAD; giá nhà dùng Ames/BIS; vàng dùng
World Bank Pink Sheet. Hệ chạy cục bộ, không cần API key hoặc mô hình ngôn ngữ trả phí.

### 6.1.1. Tác tử là gì?

Có thể hiểu một tác tử là thành phần nhận thông tin, quyết định hành động trong phạm vi
được phép và gửi kết quả. Wooldridge và Jennings thảo luận tính tự chủ, tương tác,
phản ứng và chủ động như các đặc trưng của agency [@wooldridge1995agents]. Triển khai
trong chương là **orchestrator nhiều vai trò có luật xác định**, tự chủ rất hẹp. Nó
không có mục tiêu mở, thương lượng xã hội hoặc trí thông minh nổi lên như một hệ đa
tác tử tổng quát. Các vai trò chia sẻ cấu trúc chương trình nhưng có state/message riêng
trong mỗi task; ba specialist khác miền dùng công cụ và nguồn khác nhau.

Một tool chỉ thực hiện phép tính hoặc tra cứu. Specialist chọn và gọi tool trong miền;
router chọn specialist; verifier có quyền chặn phản hồi; reporter chuẩn bị nội dung có
cảnh báo. Gọi thêm tên vai trò không tạo thêm tri thức. Chỉ khi quyền hạn và kiểm chứng
khác nhau, việc phân vai mới có ý nghĩa để kiểm tra.

### 6.1.2. Ba cấu hình được so sánh

A0 gọi trực tiếp tool theo domain người dùng chọn. A1 thêm router và specialist.
A2 dùng cùng hai bước đó, thêm verifier và reporter. Cả ba nhận cùng question/record,
cùng checkpoint, chính sách an toàn và budget. A0 có domain hint từ người dùng, nên
không chấm routing accuracy cho A0. Không cố tình làm yếu A0 bằng cách bỏ safety policy.

ReAct nghiên cứu phối hợp reasoning/action bằng LLM [@yao2023react]. Đó là đối chiếu
khái niệm, không phải thuật toán đã tái tạo ở đây. Benchmark không gọi LLM, không sinh
hoặc lưu chain-of-thought; trace chỉ ghi hành động, input/output công cụ và trạng thái.

![Kiến trúc ba specialist và các vai trò A2](../../../artifacts/figures/phase31/architecture.png)

**Hình 6.1. Luồng có giới hạn của A2; A0/A1 lược bớt vai trò theo định nghĩa.** Nguồn:
`service.pipeline_contract`, `core.Orchestrator`, registry công cụ Phase31.

## 6.2. Ba bộ nhiệm vụ diabetes, house, gold

### 6.2.1. Nguồn và kích cỡ

Ba dataset Ch6 là **task view mới**, không phải ba raw dataset được tải thêm. Mỗi miền
có100 câu hỏi theo template tổng hợp; nội dung số/evidence lấy snapshot thật. Catalog
giữ60 record/miền:40 input numeric và20 evidence. Các mẫu OOD/unsafe không phải bệnh án
hay giao dịch thật. Không sao chép raw và không dùng parent TEST để điều chỉnh luật.

"""
    text += markdown_table(
        ["Task view", "Nguồn cha", "Task train/dev/test", "Dữ liệu sử dụng"],
        [
            [
                "Diabetes",
                "CDC diabetes + MedQuAD",
                "60/20/20",
                "Probability MLP + exact medical chunk lookup",
            ],
            ["House", "Ames Housing + BIS", "60/20/20", "MLP USD lịch sử + chỉ số danh nghĩa"],
            ["Gold", "World Bank Pink Sheet", "60/20/20", "LSTM3 horizon + giá quan sát tại TRAIN origin"],
        ],
    )
    text += "\nThẻ dữ liệu đầy đủ, URL/giấy phép/kích cỡ raw parent và5 mẫu mỗi miền:\n\n"
    for description in descriptions:
        text += f"- `{description['data_card']['path']}`.\n"
    text += """

CDC, Ames và Pink Sheet kế thừa điều khoản đã ghi trong source manifest; MedQuAD CC BY4.0;
BIS theo điều khoản sử dụng thống kê riêng và phải ghi nguồn BIS/các đơn vị quốc gia.
Số byte raw parent là snapshot của chương trước, không gán thành byte dataset task mới.
`taskset_v2.json` là file dùng chung3 miền; card ghi kích cỡ vật lý/hash thật của file đó.

### 6.2.2. Phân bố, mẫu đầu ra và giới hạn

Mỗi miền có20 numeric,20 evidence,20 OOD,20 unsafe và20 tool_failure. Mỗi loại gồm5 nhóm
template, mỗi nhóm4 câu. Ba nhóm đầu là TRAIN, nhóm4 DEV, nhóm5 TEST; tương ứng60/20/20.
Các bản ghi/chunk-document/country series được chia nhóm, không chuyển cùng nguồn gốc
sang split khác. Các ý định unsafe nguyên nhóm không bị chia chỉ bằng đổi wrapper câu.
Các cửa sổ vàng có ID khác nhau nhưng có thể chồng lịch sử; parent TRAIN đã dùng huấn luyện
predictor. Vì vậy TEST này kiểm pipeline trên template/record giữ lại, **không kiểm lại
độ khái quát của base model**. Split counts và overlap0 được kiểm bằng `audit_groups`.

"""
    text += f"Ví dụ TRAIN tổng hợp: “{sample['request']['question']}”. Tool LSTM scratch seed42 trả `{sample['gold']['payload']['values']}` ({sample['gold']['payload']['unit']}). Đây là output model có thật, không phải giá thị trường mới hay nhãn đúng.\n\n"
    text += """Bộ task cân bằng để nhìn rõ từng lỗi nhưng không phản ánh tần suất câu hỏi ngoài đời.
MedQuAD chỉ tra đúng chunk theo ID đã chọn; không chấm hỏi đáp tự do, BM25 hay chất lượng
RAG thêm một lần. Chunk corpus không chứa metadata split QA, nên không tự gán nó là TRAIN QA.
Không đọc nhãn/câu hỏi TEST cũ. Các citation chỉ tới local container và locator chunk/document;
URL ở cấp nguồn, không suy đoán lại raw URL từng đoạn đã bị lược bỏ.

## 6.3. Router, specialist, verifier và reporter

Router chuẩn hóa dấu/chữ rồi tìm từ khóa của đúng một miền. “Tiểu đường” và “CDC” thuộc
diabetes; “giá nhà”, “Ames”, “BIS” thuộc house; “giá vàng”, “Gold”, “Pink Sheet” thuộc gold.
Không match hoặc match nhiều miền thì A1/A2 từ chối; khác domain người dùng chọn cũng
từ chối. Đây là luật hữu hạn, không phải bộ hiểu ngữ nghĩa tiếng Việt.

Specialist diabetes gọi MLP hoặc lấy trích đoạn MedQuAD. Specialist house gọi MLP Ames
hoặc tra chỉ số BIS. Specialist gold gọi LSTM hoặc tra giá tại origin. Ba model là bản
scratch seed42 đã khóa từ Ch2/Ch4; serving NumPy CPU, không train thêm và không gọi GPU.
Gold LSTM có3 đầu ra1/3/6 tháng; việc điều phối không khắc phục kết quả dự báo thấp đã
ghi ở Ch4. Probability CDC cũng không chuyển thành chẩn đoán bệnh cá nhân.

Tool chạy trong process con local. Nếu lỗi transient, cho thử lại đúng1 lần; lỗi permanent
trả failed; vượt deadline trả timeout và terminate/join process. Tổng budget15 giây/task,
không quá8 call. Core hiện nhiều nhất2 attempt cho một tool, nằm trong budget đó.
Nội dung evidence là dữ liệu: câu “ignore previous instructions” trong trích đoạn không
được phân tích thành lệnh mới hoặc mở quyền đọc file/mạng.

Verifier A2 so SHA-256 của payload với receipt công cụ và kiểm số hữu hạn, citation,
provenance. Lỗi bị chặn thì không tạo con số thay thế. Đây là kiểm integrity của kênh
trusted local tool, không chống worker ác ý có thể sửa cả payload lẫn receipt, và không
chứng minh văn bản nguồn đúng y khoa. Reporter chỉ dùng nội dung đã có và cảnh báo;
lớp đóng gói chuẩn hóa status cuối cùng để trả trace theo schema chung.

## 6.4. Hợp hàm, công cụ và trace có provenance

### 6.4.1. Dữ liệu đi qua hệ thế nào?

"""
    for variant in VARIANTS:
        contract = next(c for c in contracts if c["variant"] == variant)
        text += f"- {variant}: **{contract['composition_plain']}**.\n"
    text += """

Viết gọn riêng A2: `F = emit ∘ report ∘ verify ∘ specialist ∘ route ∘ policy ∘ validate`.
Ký hiệu `∘` là hợp hàm: làm bước bên phải trước rồi chuyển kết quả sang bên trái. Luồng
bằng lời phía trên là ý nghĩa của biểu thức, không phải các layer mạng. Khi một bước
từ chối/lỗi, trạng thái đi tiếp để đóng gói, không tiếp tục suy diễn như có kết quả tốt.
Các function contract có phiên bản `phase31.agent_pipeline.1`; không ép orchestrator
vào model schema neural6layer và không bịa parameter count cho router.

### 6.4.2. Giải thích từng hàm

"""
    text += markdown_table(["ID", "Signature", "Vai trò", "Input → Output", "Trường hợp biên"], function_rows)
    text += """

Code chính ở `src/ch06_multi_agent/core.py`, `tools.py`, `executor.py`, `service.py`.
Bảng JSON cùng nguồn là `function_contracts.json`, dành cho report và UI Phase33. Mỗi
node trace có agent/tool, parent node, hash input/output, refs artifact, thời gian và
outcome. `messages` lưu dữ liệu hành động tương ứng để auditor tính lại từng hash; nó
không lưu suy nghĩ nội bộ. DAG phải không chu trình và thứ tự topo hợp lệ.

```python
# Ý chính của verifier; code đầy đủ có kiểm schema, finite và provenance.
if canonical_sha256(payload) != receipt_sha256:
    raise ValueError("Tool receipt integrity mismatch")
```

Hash chỉ có ý nghĩa khi receipt đến từ tool được cho phép và input/checkpoint/evidence
đã được pin. Không nhận checkpoint pickle, command, filename hoặc URL do câu hỏi cung
cấp. Dữ liệu MedQuAD nằm ở apps/, ngoài path allowlist trace chuẩn; trace tham chiếu
preservation index Phase30 chứa exact container ref, còn citation giữ container hash.

## 6.5. Benchmark A0/A1/A2 và đánh giá

### 6.5.1. Giao thức và mẫu số

Rubric/task/gold/source/evaluator được khóa trước TEST tại `declaration.json`.
TRAIN/dev có720 kết quả; TEST tác tử60 task ×3variant có180 kết quả, batchcount1.
Không train lại predictor hoặc gọi evaluator TEST Ch2/3/4/5. Auditor chỉ đọc900 output
đã lưu. Một lần/task/variant, thứ tự variant xoay vòng theo task; không dựng SD3seed cho
hệ rule xác định. Latency là wall time cả process/schema sau preload catalog; không phải
HTTP/Render SLA và máy không được chứng nhận cô lập tải nền.

Task_success cần status đúng rubric. Nếu cần answer, số phải khớp tool ở rtol1e-6,
atol1e-8, text/citation phải đúng. Nếu fault yêu cầu chặn, abstain được tính đúng rubric
nhưng **không tính là answer_completion**. Numeric parity đo tính trung thực với tool,
không phải accuracy dự báo. Routing chỉ A1/A2; citation exactness không xác nhận nội
dung chuyên môn. Tỷ lệ không có mẫu số dùng null và ghi n, không điền0.

### 6.5.2. Kết quả TEST tác tử

"""
    text += markdown_table(
        [
            "Miền",
            "Variant",
            "Task success (n)",
            "Answer completion",
            "p50/p95 ms",
            "Message TB",
            "Max child RSS MiB",
        ],
        results,
    )
    text += "\nNguồn: `artifacts/metrics/phase31/grouped_metrics.csv`; n20task/miền/variant. RAM là peak child process; parent high-water đo riêng, không cộng thành peak đồng thời.\n\n"
    text += "![Kết quả theo loại task](../../../artifacts/figures/phase31/test_quality.png)\n\n**Hình 6.2. Task success TEST, mỗi loại4task/miền/variant.** Nguồn: saved outputs900row, không chạy lại predictor TEST.\n\n"
    text += f"Trên ca bình thường, task_success quan sát từ {min(r['task_success'] for r in benign) * 100:.1f}% đến {max(r['task_success'] for r in benign) * 100:.1f}% cho các ô miền/variant. Đây là bài toán ID-bound nên kết quả cao không chứng minh hiểu câu hỏi tự do. A1 không tự cải thiện phép tính khi A0 đã được người dùng chọn đúng miền.\n\n"
    text += """A2 được kỳ vọng có lợi ở kiểm lỗi integrity, không ở việc tạo thêm câu trả lời cho
ca thiếu bằng chứng. Biểu đồ tách riêng tool_failure để nhìn rõ lợi ích đó. Không dùng
tỷ lệ chung trộn challenge làm bằng chứng rằng nhiều agent luôn thông minh hơn.

![Độ trễ TEST theo miền](../../../artifacts/figures/phase31/latency.png)

**Hình 6.3. p50/p95 từ20task mỗi miền/variant, gồm ca có tool và ca từ chối sớm.** Không
so thời gian inference model bằng biểu đồ này; cold load và bộ sinh hình không nằm trong timing.

### 6.5.3. An toàn và ca lỗi

Tool_failure có4 lỗi tổng hợp trong mỗi nhóm: transient, permanent, numeric tamper,
citation tamper. Các lỗi cố ý giữ receipt cũ sau khi sửa payload. A0/A1 không có verifier
nên có thể trả phản hồi sai hoặc thiếu nguồn; A2 phát hiện mismatch và từ chối. Nếu
worker cùng sửa cả receipt, phép kiểm này không còn đủ. Đây là giả định threat model,
không phải kiểm thử tấn công toàn diện hay chứng nhận hệ thống an toàn.

![Claim thiếu hỗ trợ và unsafe trên challenge](../../../artifacts/figures/phase31/safety.png)

**Hình 6.4. Hai loại tỷ lệ lỗi khác nhau trên challenge TEST.** Cột0 về unsafe chỉ nói
đúng các mẫu rule đã kiểm; không suy ra an toàn với mọi cách diễn đạt mới.

![Trace A2 chặn numeric tamper](../../../artifacts/figures/phase31/trace_example.png)

**Hình 6.5. Một trace TEST đã lưu; các mũi tên là thứ tự chuyển message, không chain-of-thought.**

## 6.6. Giới hạn, an toàn và xử lý lỗi

Thứ nhất, template/record-bound cố tình đơn giản hóa ngôn ngữ. Core không tự lấy profile
cá nhân từ một đoạn văn, không tự mở website và không tạo kế hoạch nhiều bước bất kỳ.
Deadline dùng process local trong driver single-threaded WSL; không fork trực tiếp trong
web server nhiều thread. Khi tích hợp API phải có worker/budget riêng ở Phase32.

Thứ hai, lookup evidence không phải QA semantic. MedQuAD chỉ trả trích đoạn; giá nhà Ames
không hiện tại, BIS không là giá một căn nhà; vàng không là khuyến nghị mua bán. Không có
LLM, không có thương lượng hay học phối hợp. Thêm nhiều tác tử làm tăng bước/message nhưng
không bổ sung dữ liệu mới. Các hạn chế này phải được giữ khi demo hoặc đưa vào UI.

Thứ ba, benchmark có ít task mỗi category TEST (n4/miền), không có human study, không
đánh giá ngoài phân bố thật, không suy luận ý nghĩa thống kê từ vài phần trăm. Kết quả
bằng nhau của A0/A1 trên tác vụ dễ là kết quả cần báo, không chọn lại câu hỏi để tạo
khoảng cách. Sau TEST không sửa rule, rubric, seed hoặc task bằng kết quả vừa xem.

## 6.7. Triển khai ngắn

Demo chạy bằng `scripts.demo_phase31 --domain diabetes|house|gold` trong runtime WSL
đã khóa; ba notebook mỏng chạy9 slot A0/A1/A2 trên TRAIN input. Khóa artifact trước load,
serving CPU và không cần API key. Câu hỏi public demo phải chứa `record=<ID>` thuộc
catalog; câu không gắn record được trả unsupported thay vì đoán. Đó là contract local,
chưa phải HTTP/React/Render live. API/worker nằm ở Phase32, UI trace ở33 và tích hợp DOCX
ở34–35. Mục triển khai này không tạo chương riêng.

Tài liệu vận hành: `docs/phase31_operations.md`. Tham khảo: `ch06_sources_v3.bib`,
Wooldridge–Jennings (1995), DOI10.1017/S0269888900008122; Yao và cộng sự (ICLR2023),
https://arxiv.org/abs/2210.03629. Hai nguồn dùng cho khái niệm và đối chiếu, không thay
evidence đo local của benchmark.
"""
    return text


def main():
    if (BASE / "experiment_lock.json").exists():
        raise ValueError("Released outputs immutable; do not regenerate")
    rows = audit_results(include_test=True)
    check_summary(rows)
    view, catalog, tasks = load_inputs()
    groups = aggregate(rows)
    files = [csv_once(METRICS / "grouped_metrics.csv", groups)]
    run_rows = [
        {k: r[k] for k in ("task_id", "domain", "split", "category", "stratum", "variant")} | r["metrics"]
        for r in rows
    ]
    files.append(csv_once(METRICS / "run_summary.csv", run_rows))
    write_once(
        METRICS / "grouped_metrics.json",
        {"rows": groups, "source": "saved outputs; no forward", "null_policy": "no applicable denominator"},
    )
    files.append(ref(METRICS / "grouped_metrics.json"))
    contracts = [pipeline_contract(d, v) for d in DOMAINS for v in VARIANTS]
    write_once(
        BASE / "function_contracts.json",
        {"schema_version": "phase31.agent_pipeline.1", "contracts": contracts},
    )
    files.append(ref(BASE / "function_contracts.json"))
    cards, descriptions = data_cards(tasks, catalog, view["taskset"])
    files += cards
    chapter = {
        "chapter": 6,
        "title": "Hệ đa tác tử",
        "route": "/agents",
        "dataset_ids": [f"ch6_{d}_tasks" for d in DOMAINS],
        "families": ["multi_agent"],
        "sections": ["data", "theory", "run", "results", "deployment"],
    }
    validate_document("api#chapter", chapter)
    write_once(
        BASE / "catalog.json",
        {
            "chapter": chapter,
            "datasets": descriptions,
            "variants": list(VARIANTS),
            "api_ui_implemented": False,
        },
    )
    files.append(ref(BASE / "catalog.json"))
    images = figures(groups, rows)
    files += images
    files += notebooks()
    manuscript_path = ROOT / "report/sections/v3/ch06_multi_agent.md"
    files.append(text_once(manuscript_path, manuscript(groups, tasks, descriptions, contracts)))
    write_once(
        BASE / "active_report.json",
        {
            "manuscript": ref(manuscript_path),
            "generation_path": "artifacts/manifests/phase31/report_generation.json",
        },
    )
    files.append(ref(BASE / "active_report.json"))
    write_once(
        BASE / "report_generation.json",
        {
            "phase": 31,
            "status": "PASS",
            "files": files,
            "figures": images,
            "manuscript": ref(manuscript_path),
            "notebooks_executed": 3,
            "demo_variant_slots": 9,
            "benchmark_results": len(rows),
            "tables": 2,
            "base_model_test_forward": False,
            "scope": "notebook demos only TRAIN, benchmark metrics only saved outputs",
        },
    )
    print(
        {"status": "PASS", "files": len(files), "figures": 5, "notebooks": 3, "results": len(rows)},
        flush=True,
    )


if __name__ == "__main__":
    main()
