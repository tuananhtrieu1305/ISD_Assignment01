"""Presentation-only telemetry clarification; preserve original report/figures and all benchmark bytes."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scripts.build_phase31 import arrow, box, text_once
from scripts.phase31_benchmark import BASE
from src.ch05_knowledge_rag.preservation import checked, ref
from src.common.artifact_core import write_once
from src.common.contracts import ROOT, read_json


def main():
    original = read_json(BASE / "report_generation.json")
    manuscript = checked(original["manuscript"]).read_text(encoding="utf-8")
    revision = BASE / "revisions/presentation_r2"
    # Select the same saved TEST example; never execute a tool or evaluator.
    record = read_json(BASE / "results_v2/test/gold_tool_failure_f5_3_a2.json")
    nodes = record["output"]["trace"]["nodes"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "svg.fonttype": "none"})
    fig, ax = plt.subplots(figsize=(10.8, 3.7))
    ax.axis("off")
    ax.set(xlim=(0, 10), ylim=(0, 3))
    for i, node in enumerate(nodes):
        x = 0.3 + i * 2.4
        timing = (
            "không đo riêng" if node["agent"] in {"router", "reporter"} else f"{node['duration_ms']:.2f} ms"
        )
        box(ax, x, 1.2, 1.8, 1.0, f"{node['agent']}\n{node['outcome']}\n{timing}")
        if i:
            arrow(ax, (x - 0.6, 1.7), (x, 1.7))
    ax.text(
        5,
        0.5,
        "gold_tool_failure_f5_3 | saved TEST, numeric tamper\nRouter/reporter: trace0 là mặc định chưa instrument, không phải số đo0 ms.",
        ha="center",
        fontsize=10,
    )
    folder = ROOT / "artifacts/figures/phase31/presentation_r2"
    folder.mkdir(parents=True, exist_ok=True)
    figures = [r for r in original["figures"] if "trace_example." not in r["path"]]
    for suffix in ("png", "svg"):
        path = folder / f"trace_example.{suffix}"
        fig.savefig(
            path,
            dpi=300,
            bbox_inches="tight",
            facecolor="white",
            metadata={"Date": None} if suffix == "svg" else None,
        )
        figures.append(ref(path))
    plt.close(fig)
    manuscript = manuscript.replace(
        "../../../artifacts/figures/phase31/trace_example.png",
        "../../../artifacts/figures/phase31/presentation_r2/trace_example.png",
    )
    manuscript = manuscript.replace(
        "**Hình 6.5. Một trace TEST đã lưu; các mũi tên là thứ tự chuyển message, không chain-of-thought.**",
        "**Hình 6.5. Một trace TEST đã lưu; mũi tên là thứ tự chuyển message, không chain-of-thought.**\n\nRouter/reporter có duration_ms=0 mặc định do chưa đo riêng; không coi đó là thời gian xử lý bằng0. Specialist có timing bao gồm process-tool, verifier có timing kiểm tra; latency tổng của task là wall time đo độc lập. Không cộng các duration node để suy ra tổng latency.",
    )
    manuscript = manuscript.replace(
        "A2 được kỳ vọng có lợi ở kiểm lỗi integrity, không ở việc tạo thêm câu trả lời cho\nca thiếu bằng chứng.",
        "Trong TEST này, mỗi miền A0/A1 đạt18/20 task_success và A2 đạt20/20. Lợi ích của A2 nằm ở kiểm lỗi integrity, không ở việc tạo thêm câu trả lời cho ca thiếu bằng chứng. Answer_completion tương ứng11/20 và9/20: A2 từ chối hai output hỏng thay vì trả chúng.",
    )
    path = ROOT / "report/sections/v3/ch06_multi_agent_r2.md"
    text_once(path, manuscript)
    files = [ref(path), ref(ROOT / "scripts/build_phase31_presentation_r2.py"), *figures]
    document = {
        "phase": 31,
        "revision": "presentation_r2",
        "files": files,
        "figures": figures,
        "manuscript": ref(path),
        "original_generation": ref(BASE / "report_generation.json"),
        "benchmark_modified": False,
        "scope": "Clarify uninstrumented node timings and observed containment result; no metric or output changes",
    }
    write_once(revision / "report_generation.json", document)
    write_once(
        BASE / "active_report_r2.json",
        {
            "manuscript": ref(path),
            "generation": ref(revision / "report_generation.json"),
            "note": "Current presentation overlay; original active_report.json/report_generation.json are preserved historical r1",
        },
    )
    print({"status": "PASS", "active": ref(BASE / "active_report_r2.json"), "new_figures": 1}, flush=True)


if __name__ == "__main__":
    main()
