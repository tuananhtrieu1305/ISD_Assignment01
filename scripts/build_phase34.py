"""Assemble manuscript from locked reports/contracts; never run model code."""

import argparse
import hashlib
import json
import re
from pathlib import Path

from scripts.phase34_editor import (
    bibliography_entries,
    caption_tables,
    convert_citations,
    figure_captions,
    markdown_blocks,
    rebase_images,
    rebase_links,
    safe_path,
    section_replace,
    source_excerpt,
)
from src.common.artifact_core import sha256_file
from src.common.contracts import ROOT, read_json

OUT = ROOT / "report/phase34"
BASE = ROOT / "artifacts/manifests/phase34"
CHAPTERS = {
    1: "report/sections/01_lich_su_ai.md",
    2: "report/sections/v3/ch02_ml.md",
    3: "report/sections/v3/ch03_cnn_r2.md",
    4: "report/sections/v3/ch04_rnn_lstm.md",
    5: "report/sections/v3/ch05_knowledge_rag_r2.md",
    6: "report/sections/v3/ch06_multi_agent_r2.md",
}


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path)}


def save(path, value):
    if (BASE / "experiment_lock.json").exists():
        raise ValueError("Phase34 released; use versioned revision, not overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    path.write_text(value, encoding="utf-8")


def load_text(path):
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def cell(value, limit=420):
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, separators=(", ", ": "))
    value = value.replace("|", "&#124;").replace("\n", " ")
    return value if len(value) <= limit else value[:limit] + " (trích; bản đầy đủ trong nguồn)"


def table(headers, rows):
    return (
        "\n".join(
            [
                "| " + " | ".join(headers) + " |",
                "|" + "|".join(["---"] * len(headers)) + "|",
                *["| " + " | ".join(cell(v) for v in row) + " |" for row in rows],
            ]
        )
        + "\n"
    )


def json_table(value):
    if isinstance(value, list):
        if not value:
            return "Không có bản ghi trong trường này.\n"
        if all(isinstance(v, dict) for v in value):
            keys = list(dict.fromkeys(key for row in value for key in row))
            return table(keys, [[row.get(key, "không áp dụng") for key in keys] for row in value])
        return table(["Giá trị"], [[v] for v in value])
    if isinstance(value, dict):
        return table(["Trường", "Giá trị"], list(value.items()))
    return cell(value) + "\n"


def card_text(path):
    """Readable appendix, preserving values; bulky JSON stays in linked frozen card."""
    text = load_text(path)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"```json\s*\n(.*?)\n```", lambda m: json_table(json.loads(m[1])), text, flags=re.DOTALL)
    text = re.sub(r"^# .*\n", "", text)
    text = re.sub(r"^## (.+)$", r"#### \1", text, flags=re.MULTILINE)
    return text.strip()


def inline_samples(dataset, source):
    eda = read_json(ROOT / dataset["eda"]["path"])
    samples = eda.get("samples", [])
    if not samples:
        return "Mẫu và output có trong hồ sơ dữ liệu Phụ lục A; Ch6 dùng task view đã khóa, không dùng EDA parent-view để thay benchmark.\n"
    rows = []
    for i, sample in enumerate(samples[:3], 1):
        rows.append(
            [
                sample.get("id", i),
                sample.get("input", sample),
                sample.get("known_output", sample.get("output", "nhãn nguồn không có trong mẫu")),
            ]
        )
    note = eda.get("sample_note", "Mẫu từ snapshot đã khóa, không phải dự đoán mới.")
    return (
        note
        + "\n\n"
        + table(["Mã mẫu", "Input minh họa", "Output nguồn"], rows)
        + "\nNguồn đầy đủ: `"
        + source
        + "`; mọi đoạn rút gọn được ghi là trích.\n"
    )


def history(text):
    text = re.sub(r"<!--.*?-->\s*", "", text, flags=re.DOTALL)
    text = text.replace(r"\(h_t=f(x_t,h_{t-1})\)", "bằng một hàm của input hiện tại và trạng thái trước")
    text = text.replace(
        r"Với đầu vào \(x\), trọng số \(w\), bias \(b\) và hàm ngưỡng, mô hình tạo dự đoán từ dấu của \(w^Tx+b\); quy tắc cập nhật điều chỉnh trọng số khi phân loại sai.",
        "Mô hình kết hợp các đặc trưng theo trọng số, thêm độ lệch rồi so với ngưỡng để tạo nhãn; khi phân loại sai, quy tắc học điều chỉnh trọng số từ ví dụ đó.",
    )
    text = text.replace(
        "Gradient được nhân lặp qua nhiều Jacobian nên có thể giảm về gần 0 hoặc tăng mất kiểm soát",
        "Khi truyền ngược qua nhiều bước, tín hiệu học có thể giảm rất nhỏ hoặc tăng mất kiểm soát",
    )
    text = text.replace(
        "Trong Chương 4, Vanilla RNN được chọn để ba implementation có thể đối chiếu đến phương trình và gradient. LSTM, attention và Transformer đóng vai trò mốc mở rộng: chúng cho biết vì sao kiến trúc cơ bản có giới hạn và những cơ chế nào đã được phát triển để xử lý giới hạn đó.",
        "Chương4 hiện thực cả Vanilla RNN và LSTM bằng scratch, Keras và PyTorch trên cùng ba chuỗi. Attention và Transformer chỉ đặt bối cảnh lịch sử, không thuộc ma trận thực nghiệm của đề tài.",
    )
    text = text.replace(
        "trên ảnh và trên một phép chuyển đổi Conv1D có giới hạn",
        "trên ba miền ảnh IDRiD, EuroSAT và CIFAR-10",
    )
    text = text.replace(
        "Chương 4 khảo sát RNN, BPTT và dữ liệu tuần tự", "Chương4 so sánh RNN–LSTM, BPTT và dữ liệu tuần tự"
    )
    text = text.replace(
        "Dữ liệu giá cổ phiếu có autocorrelation", "Dữ liệu giá vàng và chỉ số nhà có tự tương quan"
    )
    text += "\n\n" + load_text(OUT / "inputs/history_updates.md")
    return text


def integrate_chapter(number, text, dataset_rows, deployments):
    if number == 1:
        return history(text)
    # Keep scientific tables/figures unchanged; replace obsolete integration-only sections.
    if number in (2, 3):
        old_deploy, old_summary = ("2.6.", "2.7.") if number == 2 else ("3.6.", "3.7.")
        blocks = markdown_blocks(text)
        start = next(
            b["start"] for b in blocks if b["kind"] == "heading" and b["text"].startswith("## " + old_summary)
        )
        summary = text[start:].split("\n", 1)[1].strip()
        text = section_replace(text, old_deploy, f"## {number}.6. Tiểu kết\n\n" + summary)
        text = text[
            : next(
                b["start"]
                for b in markdown_blocks(text)
                if b["kind"] == "heading" and b["text"].startswith("## " + old_summary)
            )
        ]
        data_number, deploy_number = f"{number}.7.", f"{number}.8."
    elif number == 4:
        start = next(
            b["start"]
            for b in markdown_blocks(text)
            if b["kind"] == "heading" and b["text"].startswith("## 4.9.")
        )
        text = text[:start]
        data_number, deploy_number = "4.9.", "4.10."
    elif number == 5:
        start = next(
            b["start"]
            for b in markdown_blocks(text)
            if b["kind"] == "heading" and b["text"].startswith("## 5.8.")
        )
        summary = text.split("## 5.9. Tiểu kết", 1)[1].strip()
        text = text[:start] + "\n## 5.8. Tiểu kết\n\n" + summary + "\n"
        text = text.replace("Chương6 sẽ so", "Chương6 so").replace(
            "các lợi ích đó phải được đo riêng ở Phase31", "các lợi ích đó được đo riêng ở Chương6"
        )
        data_number, deploy_number = "5.9.", "5.10."
    else:
        start = next(
            b["start"]
            for b in markdown_blocks(text)
            if b["kind"] == "heading" and b["text"].startswith("## 6.7.")
        )
        text = text[:start]
        text = text.replace(
            "Khi tích hợp API phải có worker/budget riêng ở Phase32.",
            "API đã dùng worker/budget riêng; benchmark single-threaded local không được hiểu là số đo HTTP hoặc Render.",
        )
        text = text.replace("dành cho report và UI Phase33", "được report và UI dùng chung")
        text = text.replace(
            "Trên ca bình thường, task_success quan sát từ 100.0% đến 100.0% cho các ô miền/variant.",
            "Trên ca bình thường, mọi ô miền/variant đều có task_success100,0% trong bộ task đã khóa.",
        )
        data_number, deploy_number = "6.7.", "6.8."
    text += f"\n\n## {data_number} Mẫu dữ liệu và đường dẫn hồ sơ\n\n"
    for row in dataset_rows:
        text += "### " + row["dataset_id"] + "\n\n"
        if number == 6:
            card = load_text(ROOT / row["data_card"]["path"])
            sample = re.search(r"(\| Task \|.*?)(?:\n\n)", card, re.DOTALL)
            if not sample:
                raise ValueError("Missing agent samples")
            text += (
                "Câu hỏi theo template tổng hợp; giá trị output lấy tool đã khóa, không phải nhãn thị trường hay bệnh án.\n\n"
                + sample[1]
                + "\n\n"
            )
        else:
            text += inline_samples(row, row["data_card"]["path"]) + "\n"
        text += (
            "Hồ sơ nguồn, dung lượng, schema, phân bố và giới hạn đầy đủ ở Phụ lục A, mục `"
            + row["dataset_id"]
            + "`.\n\n"
        )
    text += f"## {deploy_number} Triển khai ngắn\n\n" + deployments[str(number)] + "\n\n"
    text += "Python API và React UI đã được kiểm thử local; không có endpoint train/TEST. Job có kiểm schema/hash/quyền đọc, timeout và giới hạn tài nguyên. Demo không là chẩn đoán, định giá hiện tại hay khuyến nghị đầu tư. Blueprint CPU dành Render và Static Site đã chuẩn bị, nhưng chưa cloud deploy; cần API HTTPS và CORS chính xác khi build. Hướng dẫn dài ở Phụ lục C.\n"
    return text


def appendix_data(datasets):
    text = "# PHỤ LỤC A. HỒ SƠ DỮ LIỆU\n\nCác mẫu là nhãn/evidence nguồn hoặc output tool đã lưu, không phải lần inference mới. Với ImageNet chỉ có metadata; không dựng ảnh hoặc đủ ba mẫu giả. Trường dài được trích để đọc, bản gốc liên kết giữ đầy đủ schema/hash.\n\n"
    refs = []
    for i, row in enumerate(datasets, 1):
        path = ROOT / row["data_card"]["path"]
        if sha256_file(path) != row["data_card"]["sha256"]:
            raise ValueError("Data card hash mismatch")
        refs.append(ref(path))
        text += f"## A.{i}. {row['dataset_id']}\n\n" + card_text(path) + "\n\n"
        text += f"Bản đầy đủ đã khóa: [{row['dataset_id']}]({Path('../..').as_posix()}/{path.relative_to(ROOT / 'report').as_posix()}).\n\n"
    return text, refs


def contract_counts(contract):
    parameters = sum(layer["parameter_count"] for layer in contract["layers"])
    if parameters != contract["parameter_count"]:
        raise ValueError("Contract parameter count mismatch")
    return sum(layer["parameter_count"] > 0 for layer in contract["layers"]), parameters


def appendix_functions():
    registry = read_json(ROOT / "artifacts/manifests/phase25/initialized_contract_registry.json")
    text = "# PHỤ LỤC B. HỢP ĐỒNG HÀM VÀ MÃ NGUỒN\n\nContract cấu trúc bên dưới lấy từ lõi dùng chung, không coi initialized registry là checkpoint đã train. Checkpoint/kết quả dùng registry thực nghiệm của từng chương. Các hàm chung chỉ giải thích một lần ở thân chương; tại đây giữ shape/parameter cụ thể cho từng dataset. Các mapping chỉ tên API, không ngụ ý ba framework được import trong cùng process.\n\n"
    refs, formulas, summary = [], [], []
    for model in registry["models"]:
        path = ROOT / model["contract"]["path"]
        if sha256_file(path) != model["contract"]["sha256"]:
            raise ValueError("Contract hash mismatch")
        contract = read_json(path)
        refs.append(ref(path))
        layers, parameters = contract_counts(contract)
        summary.append([model["model_id"], layers, parameters, contract["implementation"]])
        if model["implementation"] != "scratch":
            continue
        text += (
            "## B."
            + str(
                sum(
                    r["implementation"] == "scratch"
                    for r in registry["models"][: registry["models"].index(model) + 1]
                )
            )
            + ". "
            + model["dataset_id"]
            + " / "
            + model["family"]
            + "\n\n"
        )
        text += contract["composition_plain"] + "\n\n"
        text += (
            table(
                ["Hàm/signature", "Vai trò", "Input → output", "Tham số", "Trường hợp biên"],
                [
                    [
                        f["id"] + " / " + f["signature"],
                        f["role"],
                        str(f["input_shape"]) + " → " + str(f["output_shape"]),
                        f["parameters"],
                        f["corner_case"],
                    ]
                    for f in contract["functions"]
                ],
            )
            + "\n"
        )
        text += (
            table(
                ["Function ID", "Scratch", "Keras", "PyTorch"],
                [
                    [f["id"], *[f["mapping"][key] for key in ["scratch", "keras", "pytorch"]]]
                    for f in contract["functions"]
                ],
            )
            + "\n"
        )
        for function in contract["functions"]:
            if function.get("formula"):
                formula = function["formula"]
                formulas.append(
                    {
                        "model_id": model["model_id"],
                        "function_id": function["id"],
                        **formula,
                        "source": ref(path),
                        "presentation": "Core expression explained in chapter; full formal contract remains technical source, not repeated equation per layer",
                    }
                )
    text += "## B.13. Đối chiếu tất cả implementation\n\n" + table(
        ["Model ID", "Lớp học được", "Tham số", "Implementation"], summary
    )
    text += "\nKB–KG–RAG và tác tử không có số lớp/tham số neural để đếm. Bảng từng hàm và luồng nhánh/từ chối của chúng nằm ở mục5.6 và6.4, lấy đúng contract của API/UI.\n"
    return text, refs, formulas


def bibliography_text(entries, used):
    text = "# TÀI LIỆU THAM KHẢO\n\n"
    for key, number in used.items():
        entry = entries[key]
        fields = {}
        # Balanced field values preserve titles with nested braces.
        for match in re.finditer(r"\b(author|title|year|journal|booktitle|doi|url)\s*=\s*\{", entry):
            start, end, depth = match.end(), match.end(), 1
            while end < len(entry) and depth:
                if entry[end] in "{}":
                    depth += 1 if entry[end] == "{" else -1
                end += 1
            fields[match[1]] = entry[start : end - 1].replace("{", "").replace("}", "")
        if not all(key in fields for key in ["title", "year"]):
            raise ValueError("Incomplete bibliography entry " + key)
        text += (
            f"[{number}] " + fields.get("author", "") + " (" + fields["year"] + "). " + fields["title"] + ". "
        )
        venue = fields.get("journal", fields.get("booktitle", ""))
        if venue:
            text += venue + ". "
        if fields.get("doi"):
            text += "DOI: [" + fields["doi"] + "](https://doi.org/" + fields["doi"] + "). "
        if fields.get("url"):
            text += "[Nguồn](" + fields["url"] + ")."
        text += "\n\n"
    return text


def appendix_code():
    text = "# PHỤ LỤC D. TRÍCH MÃ NGUỒN ĐÃ THỰC THI\n\nCác đoạn dưới trích nguyên method từ source đã khóa, không viết một mô hình minh họa khác rồi gán metric cũ cho nó. Method nằm trong class, dùng import/state của module gốc; không phải script độc lập để copy chạy. Computational plan và canonical weights quyết định đủ6 hoặc7 lớp như các bảng Chương2–4. RNN/LSTM còn có các đoạn kiến trúc ba cách viết trực tiếp ở Chương4.\n\n"
    sources = [
        ("Scratch: forward cho MLP/CNN/RNN/LSTM", "src/common/numpy_engine.py", "NumpyNetwork", "forward"),
        (
            "Scratch: nối loss, backward và gradient",
            "src/common/numpy_engine.py",
            "NumpyNetwork",
            "loss_gradients",
        ),
        ("Scratch: clipping và optimizer update", "src/ch02_ml/training.py", "ScratchTrainer", "step"),
        (
            "Keras/TensorFlow: tạo các lớp từ cùng plan",
            "src/common/backend_models.py",
            "KerasBackend",
            "__init__",
        ),
        ("PyTorch: tạo các lớp từ cùng plan", "src/common/backend_models.py", "TorchBackend", "__init__"),
    ]
    ledger = []
    for i, (title, relative, cls, method) in enumerate(sources, 1):
        path = ROOT / relative
        code, first, last = source_excerpt(path, cls, method)
        ledger.append(
            {
                "source": ref(path),
                "class": cls,
                "method": method,
                "first_line": first,
                "last_line": last,
                "code_sha256": hashlib.sha256(code.encode()).hexdigest(),
            }
        )
        text += (
            f"## D.{i}. {title}\n\nNguồn: `{relative}`, `{cls}.{method}`, dòng{first}–{last}.\n\n```python\n"
            + code
            + "\n```\n\n"
        )
    text += "Backward/BPTT đầy đủ ở NumpyNetwork.backward; optimizer moment/update ở src/common/training_core.py và native_training.py; vòng train/checkpoint riêng từng chương ở các module training. Không dùng loss_gradients parity không trọng số thay cho weighted training step. Kiểm numerical gradient, native parity và update/resume đã có bằng chứng trước TEST; đoạn trích này không chạy lại chúng để tạo metric mới.\n"
    return text, ledger


def build():
    if not (BASE / "preserve_before.json").exists():
        raise ValueError("Parent audit must finish before publication assembly")
    registry = read_json(ROOT / "artifacts/manifests/phase32/registry_v3.json")
    datasets = registry["datasets"]
    deployments = read_json(OUT / "inputs/deployment.json")
    entries = {}
    for path in [
        ROOT / "report/references/bibliography.bib",
        ROOT / "report/references/ch06_sources_v3.bib",
        OUT / "inputs/sources.bib",
    ]:
        for key, entry in bibliography_entries(load_text(path)).items():
            if key in entries:
                raise ValueError("Conflicting bibliography key")
            entries[key] = entry
    used, parts, chapters, images, all_tables = {}, [], [], [], []
    intro = convert_citations(load_text(OUT / "inputs/00_mo_dau.md"), entries, used)
    save(OUT / "sections/00_mo_dau.md", intro)
    parts.append(intro)
    for number, relative in CHAPTERS.items():
        source = safe_path(ROOT, relative)
        original = load_text(source)
        text = integrate_chapter(
            number, original, [row for row in datasets if row["chapter"] == number], deployments
        )
        if number == 1:
            for row in datasets[:3]:
                text += (
                    "\n### Hồ sơ "
                    + row["dataset_id"]
                    + "\n\n"
                    + card_text(ROOT / row["data_card"]["path"])
                    + "\n"
                )
            text += "\n## 1.8. Tiểu kết\n\nDữ liệu, mô hình và cách đánh giá cùng quyết định ý nghĩa một thành công AI. Các chương sau kiểm chứng từng phạm vi cụ thể, không dùng một benchmark để suy ra trí tuệ tổng quát.\n"
        # Existing table captions are replaced once; their in-text references retain order.
        text = re.sub(r"^\*\*Bảng \d+\.\d+\.[^\n]*\*\*\s*\n", "", text, flags=re.MULTILINE)
        text, tables = caption_tables(text, number)
        output = OUT / f"sections/{number:02d}_chapter.md"
        text, figure_paths = rebase_images(text, source, output, ROOT)
        text = convert_citations(text, entries, used)
        save(output, text)
        parts.append(text)
        original_tables = caption_tables(original, number)[1]
        if not all(any(t["markdown"] == old["markdown"] for t in tables) for old in original_tables):
            raise ValueError("Scientific table changed " + relative)
        for row in tables:
            row.update(
                {
                    "chapter": number,
                    "output": output.relative_to(ROOT).as_posix(),
                    "sha256": hashlib.sha256(row["markdown"].encode()).hexdigest(),
                    "source": ref(source),
                }
            )
        all_tables.extend(tables)
        images.extend(ref(path) for path in figure_paths)
        chapters.append(
            {
                "chapter": number,
                "source": ref(source),
                "output": ref(output),
                "dataset_ids": [r["dataset_id"] for r in datasets if r["chapter"] == number],
                "original_tables_preserved": len(original_tables),
                "tables": len(tables),
                "figures": len(figure_paths),
            }
        )
    conclusion = convert_citations(load_text(OUT / "inputs/07_ket_luan.md"), entries, used)
    save(OUT / "sections/07_ket_luan.md", conclusion)
    parts.append(conclusion)
    appendices, card_refs = appendix_data(datasets)
    functions, contract_refs, formulas = appendix_functions()
    code, code_refs = appendix_code()
    operation = load_text(OUT / "inputs/appendix_operations.md")
    references = bibliography_text(entries, used)
    for name, value in [
        ("08_references.md", references),
        ("09_appendix_a.md", appendices),
        ("10_appendix_b.md", functions),
        ("11_appendix_c.md", operation),
        ("12_appendix_d.md", code),
    ]:
        if "appendix_" in name:
            label = {"09": "A", "10": "B", "11": "C", "12": "D"}[name[:2]]
            value, appendix_tables = caption_tables(value, label)
            all_tables.extend(
                {
                    **row,
                    "chapter": label,
                    "output": (OUT / "sections" / name).relative_to(ROOT).as_posix(),
                    "sha256": hashlib.sha256(row["markdown"].encode()).hexdigest(),
                    "source": "Frozen data-card/contract references in manuscript manifest",
                }
                for row in appendix_tables
            )
        save(OUT / "sections" / name, value)
        parts.append(value)
    # For the single-file handoff, image paths must be rebased again from sections/ to root.
    manuscript = "\n\n".join(
        rebase_links(
            rebase_images(t, OUT / "sections/content.md", OUT / "manuscript.md", ROOT)[0],
            OUT / "sections/content.md",
            OUT / "manuscript.md",
            ROOT,
        )
        for t in parts
    )
    save(OUT / "manuscript.md", manuscript)
    headings = [b["text"] for b in markdown_blocks(manuscript) if b["kind"] == "heading"]
    toc = (
        "# MỤC LỤC NỘI DUNG\n\nSố trang được tạo từ bản DOCX đã phân trang; danh mục này không gán số dự kiến thành số thật.\n\n"
        + "\n".join("  " * (h.count("#", 0, 6) - 1) + "- " + h.lstrip("# ") for h in headings)
    )
    save(OUT / "contents.md", toc + "\n")
    captions = figure_captions(manuscript)
    save(
        OUT / "figures_and_tables.md",
        "# DANH MỤC HÌNH VÀ BẢNG\n\nSố trang được tạo sau phân trang DOCX, không ước đoán tại bước tích hợp.\n\n## Hình\n\n"
        + "\n".join(row["label"] + " " + row["caption"] for row in captions)
        + "\n\n## Bảng\n\n"
        + "\n".join(row["label"] + " " + row["heading"] for row in all_tables)
        + "\n",
    )
    save(OUT / "references.bib", "\n\n".join(entries[k] for k in used) + "\n")
    save(BASE / "table_ledger.json", all_tables)
    save(BASE / "figure_ledger.json", captions)
    save(BASE / "code_excerpt_ledger.json", code_refs)
    save(BASE / "formula_ledger.json", formulas)
    manifest = {
        "phase": 34,
        "chapters": chapters,
        "data_cards": card_refs,
        "eda_sources": [row["eda"] for row in datasets],
        "source_manifests": [row["source_manifest"] for row in datasets],
        "model_contracts": contract_refs,
        "figures": images,
        "citation_order": used,
        "headings": headings,
        "manuscript": ref(OUT / "manuscript.md"),
        "publication_order": [
            "report/phase34/front_matter.md",
            "report/phase34/contents.md",
            "report/phase34/figures_and_tables.md",
            *[p.relative_to(ROOT).as_posix() for p in sorted((OUT / "sections").glob("*.md"))],
        ],
        "historical_test_evaluation_executed": False,
        "models_retrained": 0,
        "docx_authored": False,
        "page_count": None,
        "page_qa": "deferred_phase35",
        "scope": "Integrated content and provenance; not final DOCX or cloud deployment",
    }
    save(BASE / "manuscript_manifest.json", manifest)
    print(
        json.dumps(
            {
                "status": "ASSEMBLED",
                "chapters": len(chapters),
                "cards": len(card_refs),
                "contracts": len(contract_refs),
                "tables": len(all_tables),
                "figures": len(images),
                "citations": len(used),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    build()
