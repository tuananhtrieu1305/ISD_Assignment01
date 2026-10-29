"""Build and execute a presentation notebook using only sealed, saved artifacts."""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

import nbformat
from jupyter_client import KernelManager
from nbclient import NotebookClient

from .code.publication_v1 import digest
from .phase01 import runtime_inventory

BASE = Path(__file__).resolve().parent


def make(destination):
    runtime = runtime_inventory()
    if destination.exists():
        raise FileExistsError('Keep the executed notebook; use another candidate version')
    source = BASE / 'report/phase08'
    read = lambda name: json.loads((source / name).read_text(encoding='utf-8'))
    notebook = nbformat.v4.new_notebook()
    cells = [nbformat.v4.new_markdown_cell(
        '# Agent02 — Code và kết quả thực nghiệm\n\n'
        'Notebook đọc kết quả đã lưu của mô phỏng thương mại điện tử. Run All chỉ kiểm hash, '
        'trình bày code, bảng và hình; không train, cập nhật Q hoặc chạy đánh giá cuối. '
        '56 market run/61 learner instance và 261 final claim thuộc Phase3–7. '
        'Các đoạn mô hình được hiển thị từ source đã khóa để học và đối chiếu, không thực thi. '
        'Ví dụ số học câu 3 là giả định của đề. Gold là proxy nhu cầu giả lập từ prefix TRAIN, '
        'không phải dữ liệu cầu hoặc kết quả đầu tư.')]
    cells.append(nbformat.v4.new_code_cell('''import hashlib, json, platform
from pathlib import Path
from IPython.display import Code, Image, Markdown, display

here = Path.cwd().resolve()
candidates = [p for ancestor in [here, *here.parents] for p in (ancestor, ancestor / "agent02_assignment")]
BASE = next(p for p in candidates if (p / "report/phase08/manuscript.md").is_file())
def load(relative):
    return json.loads((BASE / relative).read_text(encoding="utf-8"))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
inputs = load("report/phase08/input_index.json")
before = {row["path"]: sha(BASE / row["path"]) for row in inputs}
assert all(before[row["path"]] == row["sha256"] for row in inputs)
print("Python:", platform.python_version())
print("Input hashes PASS:", len(before), "| Device: CPU read-only | Training steps: 0 | Final forwards: 0")'''))
    cells.append(nbformat.v4.new_markdown_cell('## Cấu hình và phạm vi\n\n'
        'Mỗi train run đã thực hiện 5.000 episode × 20 bước; seed CONTROLLED 11/22/33/44/55, '
        'REF42 riêng. Khi đo cuối, Q đóng băng, exploration tắt, 500 episode/vai và đổi vai. '
        'Gộp vai trước khi lấy mean/sample std qua năm seed; std không phải khoảng tin cậy. '
        'Hai learner trong cùng pair không phải hai replicate độc lập.'))
    cells.append(nbformat.v4.new_code_cell('''protocol = load("docs/protocol_v1.json")
display(Markdown("```json\\n" + json.dumps(protocol, ensure_ascii=False, indent=2) + "\\n```"))'''))
    descriptions = [
        'RuleAgent.act chỉ giảm khi demand=1 và competitor_previous=1; không học từ reward.',
        'QAgent.act dùng epsilon-greedy khi train; tie-breaking có RNG riêng. Final tắt exploration.',
        'QAgent.learn sửa một ô Q; terminal chỉ nhận reward, không bootstrap.',
        'TrainSession.run_chunk chọn đồng thời hai action trước step, rồi learner mới cập nhật từ reward.',
        'evaluate_tapes đọc Q cố định, dùng tapes đã khai báo và không gọi learn.',
        'Phần cuối evaluator kiểm hash Q trước/sau để phát hiện cập nhật ngoài ý muốn.',
        'markets thay kernel IID bằng persistent/Gold; reward/action không đổi.',
        'AugmentedAgent.learn thêm lịch sử của mình và thời gian; giảm remaining đúng một, giữ terminal.'
    ]
    for item, explanation in zip(read('code_excerpt_index.json'), descriptions):
        cells.append(nbformat.v4.new_markdown_cell(f'## {item["id"]} — {item["symbol"]}\n\n{explanation}\n\n'
            f'Nguồn `{item["path"]}`, dòng {item["start_line"]}–{item["end_line"]}; hiển thị nguyên đoạn, không thực thi.'))
        cells.append(nbformat.v4.new_code_cell(f'''item = next(e for e in load("report/phase08/code_excerpt_index.json") if e["id"] == {item['id']!r})
assert sha(BASE / item["path"]) == item["source_sha256"]
display(Code(item["text"], language="python"))
print("Source SHA256:", item["source_sha256"], "| Excerpt SHA256:", item["excerpt_sha256"])'''))
    cells.append(nbformat.v4.new_markdown_cell('## Phép tính câu 3 và margin\n\n'
        'Ví dụ giả định: Q cũ 4, alpha 0,1, reward 6, gamma 0,9, maxQ kế 5. '
        'Đây không phải kết quả của run đã train. Giá 10/chi phí 5 cho margin 5; giảm 20% cho margin 3.'))
    cells.append(nbformat.v4.new_code_cell('''from decimal import Decimal as D
target = D(6) + D("0.9") * D(5)
delta = target - D(4)
updated = D(4) + D("0.1") * delta
assert updated == D("4.65")
print("Target =", target, "| Delta =", delta, "| Q mới =", updated)
print("Margin giữ giá =", D(10)-D(5), "| Margin giảm giá =", D(10)*D("0.8")-D(5))'''))
    tables = read('tables.json')
    for name, table in tables.items():
        cells.append(nbformat.v4.new_markdown_cell(f'## Bảng — {name}\n\nNguồn: '
            + '; '.join('`' + p + '`' for p in table['sources'])
            + '. Số liệu hiển thị từ artifact; không chạy lại policy để lấy bảng.'))
        cells.append(nbformat.v4.new_code_cell(f'''table = load("report/phase08/tables.json")[{name!r}]
display(Markdown(table["markdown"]))'''))
    figures = read('figure_catalog.json')
    for figure in figures:
        cells.append(nbformat.v4.new_markdown_cell(f'## Hình {figure["id"]}\n\nNguồn `{figure["path"]}`.'))
        cells.append(nbformat.v4.new_code_cell(f'''figure = next(f for f in load("report/phase08/figure_catalog.json") if f["id"] == {figure['id']!r})
assert sha(BASE / figure["path"]) == figure["sha256"]
display(Image(filename=str(BASE / figure["path"])))'''))
        cells.append(nbformat.v4.new_markdown_cell('**Giải thích:** ' + figure['caption_text']))
    text = (source / 'manuscript.md').read_text(encoding='utf-8')
    answers = text[text.index('## 6.'):text.index('## 7.')]
    cells.append(nbformat.v4.new_markdown_cell(answers))
    cells.append(nbformat.v4.new_code_cell('''after = {row["path"]: sha(BASE / row["path"]) for row in inputs}
assert before == after
print("PASS: all", len(after), "input files unchanged. Training steps=0; final forwards=0.")'''))
    notebook.cells = cells
    notebook.metadata.kernelspec = {'display_name': 'AG02 pinned WSL Python 3.11', 'language': 'python', 'name': 'python3'}
    with tempfile.TemporaryDirectory(prefix='ag02-phase09-') as temporary:
        cache = Path(temporary)
        manager = KernelManager(kernel_name='python3', connection_file=str(cache / 'connection.json'))
        manager.kernel_spec.argv = [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']
        client = NotebookClient(notebook, km=manager, timeout=90, allow_errors=False,
                                resources={'metadata': {'path': str(BASE)}})
        try:
            client.execute(env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'CUDA_VISIBLE_DEVICES': '',
                                'IPYTHONDIR': str(cache / 'ipython'), 'JUPYTER_RUNTIME_DIR': str(cache / 'jupyter')})
        finally:
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, destination)
    receipt = {'status': 'PASS', 'notebook': destination.relative_to(BASE).as_posix(),
               'sha256': digest(destination), 'cells': len(cells),
               'executed_code_cells': len([c for c in cells if c.cell_type == 'code']),
               'figures': len(figures), 'artifact_tables': len(tables), 'code_excerpts': len(descriptions),
               'input_files_unchanged': 70, 'runtime': runtime, 'scientific_forward_added': 0, 'train_runs_added': 0}
    target = BASE / 'evidence/phase09/notebook_execution.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='notebooks/AG02_Code_and_Results.ipynb')
    options = parser.parse_args()
    target = (BASE / options.output).resolve()
    if not target.is_relative_to(BASE):
        raise ValueError('Notebook must stay inside AG02')
    make(target)
