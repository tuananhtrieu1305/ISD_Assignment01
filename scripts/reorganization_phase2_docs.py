"""Publish navigation and a gated Phase2 handoff from actual receipts."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs/reorganization'
P2=DOCS/'phase2'
PROJECTS=['A01','A02','A03','A04','A05','A06','tieuluan1','tieuluan2','tieuluan3','agent01','agent02']
TITLES=['ML cơ bản – bản A01','ML cơ bản – bản A02','Ba pipeline DNN','DNN/CNN đa framework','CNN','RNN','Tiểu luận 1 – bốn chương','Tiểu luận 2 – năm chương, dẫn xuất','Tiểu luận 3 – sáu chương','Discovering AI Agent','Agent02']

def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()
def save(path,doc):
    path.parent.mkdir(parents=True,exist_ok=True)
    text(path,json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
def text(path,content):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.migration-tmp')
    tmp.write_text(content,encoding='utf-8')
    tmp.replace(path)

def navigation():
    table=[]
    for project,title in zip(PROJECTS,TITLES):
        config=load(ROOT/project/'project.json')
        catalog=load(ROOT/project/'datasets/catalog.json')
        table.append(f'| [{project}]({project}/README.md) | {title} | {len(config["notebooks"])} | {len(catalog["datasets"])} |')
        notebook_rows=[f'| `{r["path"]}` | {r["framework"]} | {r["role"]} |' for r in config['notebooks']]
        text(ROOT/project/'README.md',f'''# {project} — {title}

Ba thư mục chính: `datasets/`, `notebooks/`, `web/`. Source phụ trợ và kết quả gốc được giữ theo đúng bài.

- Dataset cụ thể, vị trí vật lý, SHA256 và schema: [catalog](datasets/catalog.json).
- Notebook gốc cùng output cũ: `provenance/originals/`; notebook chính là migration revision.
- Kernel Torch/NumPy: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python`.
- Kernel Keras/TensorFlow: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-keras/bin/python`.
- Mở VS Code trong WSL **Ubuntu**, chọn interpreter tương ứng. Không dùng Python Windows/Anaconda.
- Mỗi bài chạy trong kernel mới để tránh lẫn namespace `src` giữa các bài.

Từ root repository trong PowerShell:

```powershell
./scripts/run_assignment.ps1 -Project {project} -Inspect
./scripts/run_assignment.ps1 -Project {project} -ListDatasets
```

Thêm `-Notebook "notebooks/ten_file.ipynb" -Cpu` để chạy notebook xem kết quả/demo được liệt kê. Runner tự chọn framework theo catalog. Notebook train lịch sử chỉ kiểm tĩnh + smoke riêng trong migration; runner không tự Run All chúng. A04 có notebook tách framework trong `notebooks/training/`, mặc định `RUN_TRAINING=False` chỉ xem số liệu cũ. Không train lại để xem báo cáo.

| Notebook | Kernel/framework | Vai trò |
|---|---|---|
'''+ '\n'.join(notebook_rows)+'''

`provenance/runtime/assign/` là layout tương thích được tạo từ manifest, dùng hardlink hoặc copy đã kiểm hash, không cần symlink/junction. Không sửa trực tiếp file trong view. Khi chuyển máy, xem [hướng dẫn chung](../docs/reorganization/phase2_runtime.md) và materialize lại nếu cần; dataset/checkpoint local lớn không tự có trong Git.

Web source/payload đã đặt đúng nơi. Build/serve, hoàn thiện tám demo đơn giản, ba web tiểu luận và cấu hình Render được nghiệm thu ở Phase3.
''')
    text(ROOT/'README.md','''# Assignment và tiểu luận AI

Repository được tổ chức thành 11 bài độc lập. Mỗi bài có `datasets/`, `notebooks/`, `web/`.
Kế hoạch hiện hành: [REORG ba phase](ASSIGN_REORGANIZATION_EXECUTION_PLAN.md); trạng thái thực ở [checkpoint](docs/reorganization/checkpoint.json).

| Folder | Nội dung | Notebook chính | Nhóm dataset/catalog |
|---|---|---:|---:|
'''+ '\n'.join(table)+'''

Hai môi trường WSL Ubuntu hiện có được dùng chung: PyTorch/NumPy và Keras/TensorFlow tách riêng. Không nhân bản venv vào từng bài. Xem [kernel, dataset và lệnh chạy](docs/reorganization/phase2_runtime.md), [bản đồ source](docs/repository_manifest.md) và [biên bản Phase2](docs/reorganization/phase2_report.md).

Ví dụ chạy notebook kết quả bằng PowerShell từ root:

```powershell
./scripts/run_assignment.ps1 -Project A04 -Notebook notebooks/diabetes_pipeline04.ipynb -Cpu
./scripts/run_assignment.ps1 -Project agent02 -Notebook notebooks/AG02_Code_and_Results.ipynb -Cpu
```

File đã chạy được lưu mới trong `<bai>/notebooks/executed/`. Notebook train lịch sử được giữ nguyên nguồn/output trong provenance, có revision đường dẫn; migration không train hoặc mở lại scientific TEST.

`tieuluan2` là bản dẫn xuất Chương1–5 của `tieuluan3`, có RNN–LSTM và Knowledge–RAG, bỏ Chương6. Bản DOCX sáu chương vẫn thuộc `tieuluan3`; không đổi tên thành tiểu luận2.

Phase3 hoàn thiện/build/kiểm thử 11 web, cập nhật Render và dọn source/cache cũ sau gate. Hiện không sử dụng cấu hình Render cũ để deploy cấu trúc mới. Chưa commit/push/deploy trong quá trình sắp xếp.
''')
    text(DOCS/'phase2_runtime.md','''# Chạy code sau REORG Phase2

## Môi trường

Dùng WSL distro `Ubuntu`, user `tuananh`; Python3.11.17. Torch: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python`; Keras: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-keras/bin/python`. Kernel Keras cần wheel-local CUDA library paths đã được cấu hình trong `scripts/run_assignment.sh`; ưu tiên runner. Không cài gộp Torch và TensorFlow, không bootstrap/doctor lịch sử ghi đè evidence cũ.

Mở project trong cửa sổ VS Code WSL. Chọn interpreter đúng framework trong README từng bài. Restart kernel trước khi đổi bài; helper chủ động chặn namespace còn từ bài khác. Tên hiển thị kernel trong notebook là gợi ý; runner dùng trực tiếp interpreter đã khóa, không dựa vào Python Windows.

## Lệnh

Từ PowerShell, dùng `scripts/run_assignment.ps1 -Project A01 -Inspect` hoặc `-ListDatasets`. Thêm `-Notebook notebooks/ten.ipynb -Cpu` để chạy notebook demo/kết quả. Framework mặc định `auto`; có thể chỉ rõ `-Framework keras` cho notebook Keras.

Trong WSL ở root: `bash scripts/run_assignment.sh auto --project A04 --cpu --notebook notebooks/diabetes_pipeline04.ipynb`.

Resolver trong WSL: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python scripts/datasets.py A06 a06_02 --verify`. Catalog dùng đường dẫn tính từ repository root; dữ liệu lớn có thể nằm ở bài khác theo SHA, nhưng split/scaler vẫn riêng.

Các layout `provenance/runtime/assign/` là cache tương thích, không phải source hoạt động thứ hai. Tạo lại bằng Python WSL hiện có: `python scripts/materialize_project.py --project A06`; thêm `--copy-only` nếu filesystem không hỗ trợ hardlink. Manifest ở `docs/reorganization/phase2/runtime_view_map.json`, luôn kiểm hash nguồn và từ chối ghi đè target khác hash. Không cần symlink/junction. Sau clean checkout phải cung cấp đủ raw/checkpoint local đúng hash trước; đây không phải một gói tự tải toàn bộ artifact.

## Bảo toàn và giới hạn

Runtime chuyển các thao tác ghi file legacy phổ biến sang một thư mục mới trong `notebooks/executed/artifacts/`; đây là helper chống ghi đè, không phải sandbox cho mọi syscall. Notebook train không được auto-execute bởi migration. A04 mặc định chỉ xem kết quả; bật huấn luyện mới là một thí nghiệm riêng, không sửa các seal/kết quả gốc. Không chạy các controller/TEST lịch sử để kiểm relocation.

CIFAR A04: archive đang có là binary V3, adapter đọc đúng nhãn và NHWC; không giả thành Python pickle. Parity kiểm trên tám ảnh TRAIN. A06: canonical CSV là Git LF; một bản CRLF có cùng toàn bộ hàng CSV được tạo trong provenance để thỏa hash raw của code cũ. Canonical LF không đổi.

Notebook demo CNN/RNN/LSTM tiểu luận dùng migration adapter `assignment_runtime.paper_demo`, gọi serving registry pin seed42. Bản demo thí nghiệm cũ đòi Git HEAD tại lúc train nên được giữ lịch sử. Không thay guard hoặc lock gốc. Serving dùng NumPy CPU cho ba bộ weights đã train; không diễn giải latency này là benchmark native Keras/PyTorch/GPU.

Các phép thử migration sử dụng fixture/synthetic hoặc mẫu TRAIN đã khai báo. Notebook có thể đọc bảng metric/prediction TEST đã lưu để trình bày; không forward TEST mới. Full huấn luyện chưa được chạy lại. Tương thích đầy đủ web/Render và clean-checkout packaging là gate Phase3.
''')
    text(ROOT/'docs/repository_manifest.md','''# Bản đồ repository sau REORG Phase2

Source chính: `A01`–`A06`, `tieuluan1`–`tieuluan3`, `agent01`, `agent02`. Mỗi folder có datasets/catalog, notebooks, web và README. `_shared/assignment_runtime` cùng `scripts/run_assignment.*` là bộ điều phối dùng chung.

| Trước | Sau |
|---|---|
| `src/`, `artifacts/`, `report/`, `experiments/`, `requirements/`, `deploy/`, `releases/`, `tests/` V3 | `tieuluan3/<tên cũ>/` |
| `data/` V3 | `tieuluan3/datasets/` |
| `apps/api/`, `apps/web/` | `tieuluan3/web/backend/`, `tieuluan3/web/frontend/` |
| `scripts/` thí nghiệm V3, docs và plan lịch sử | `tieuluan3/scripts/`, `tieuluan3/docs/`, `tieuluan3/provenance/plans/` |
| `discovering_ai_agent/` | `agent01/`, Python ở src, data ở datasets, web-demo/dist payload ở web |
| `agent02_assignment/` | `agent02/`, Python ở src, data ở datasets, web-demo ở web |
| Assignment cũ từ commit đã khóa | `A01`–`A06`, bản notebook/source gốc ở provenance |
| Tiểu luận1 Git portable-fix | `tieuluan1/` |
| Tiểu luận2 chưa có commit riêng | `tieuluan2/`, revision Ch1–5, parent scientific assets từ tieuluan3 |

Chi tiết từng file và hash: `docs/reorganization/phase2/canonical_map.json` (`baseline_path` là bản gốc); alias có thể tái dựng: `runtime_view_map.json`. Giữ immutable Phase1 handoff và các lock V3/AG02. Không dùng đường dẫn cũ trong biên bản lịch sử làm source canonical mới.

`apps/web/node_modules`, build/cache cũ và staging/backup tạm vẫn giữ cho Phase3 kiểm/dọn theo gate. Không coi chúng là entry point. Root render.yaml và các deploy command cũ chờ Phase3 cập nhật; không deploy ngay từ cấu hình cũ. Nested Git Agent01 được giữ trong provenance/nested_web_metadata, ngoài web payload.
''')
    # Copy only the five individual chapter texts; no cover/conclusion/appendix from six-chapter paper.
    sections=[]
    for chapter in range(1,6):
        source=ROOT/f'tieuluan3/report/phase34/sections/{chapter:02d}_chapter.md'
        target=ROOT/f'tieuluan2/report/sections/{chapter:02d}_chapter.md'
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists(): assert sha(target)==sha(source)
        else: shutil.copyfile(source,target)
        sections.append({'chapter':chapter,'parent':source.relative_to(ROOT).as_posix(),'path':target.relative_to(ROOT).as_posix(),'sha256':sha(target)})
    save(ROOT/'tieuluan2/report/derivation.json',{'chapters':sections,'status':'source sections only; no new DOCX build','parent':'tieuluan3','six_chapter_docx_copied':False})
    text(ROOT/'tieuluan2/report/README.md','''# Tiểu luận2 — bản dẫn xuất Chương1–5

`sections/` giữ nguyên byte năm phần chương đã tích hợp của tiểu luận3, không có chương6, kết luận/bìa/phụ lục sáu chương. `derivation.json` ghi parent/hash. Các đường dẫn artifact trong văn bản là logical path của bản gốc, được resolve qua runtime view/catalog khi dùng code. Chưa dựng DOCX năm chương; không đổi nhãn DOCX sáu chương thành bản này. Source/web của bài này đã loại bỏ nhánh multi-agent và giữ KG–RAG Chương5.
''')
    print('Navigation and five-chapter source sections published')

def complete():
    preservation=load(P2/'original_byte_preservation.json')
    static=load(P2/'static_verification.json')
    notebooks=load(P2/'notebook_execution_summary.json')
    assert preservation['status']==static['status']=='PASS'
    assert preservation['failures']==[] and static['required_folders']==33
    assert all(row['status'] in {'PASS','STATIC_AND_MODEL_SMOKE_ONLY'} for row in notebooks['notebooks'])
    # All current entry-point revisions, not earlier PASS records.
    for row in notebooks['notebooks']:
        assert sha(ROOT/row['project']/row['path'])==row['input_sha256'],row['path']
    for row in static['notebooks']:
        assert sha(ROOT/row['project']/row['path'])==row['sha256'],row['path']
    smoke=[load(path) for path in sorted((P2/'smoke').glob('*.json'))]
    assert {r['project'] for r in smoke}==set(PROJECTS)
    assert all(r['status']=='PASS' and r['training_steps']==r['scientific_TEST_forward']==0 for r in smoke)
    xml=(P2/'helper_tests_r3.xml').read_text()
    assert 'failures="0"' in xml and 'errors="0"' in xml
    coverage=load(P2/'helper_coverage_r3.json')['totals']['percent_covered']
    assert coverage>=80
    assert load(P2/'cifar_train_adapter_parity.json')['status']=='PASS'
    assert load(P2/'representation_adapters.json')['status']=='PASS'
    assert load(P2/'a06_raw_guard.json')['status']=='PASS'
    assert load(P2/'code_checks.json')['status']=='PASS'
    save(DOCS/'notebook_smoke.json',{'status':'PASS','projects':11,'notebook_count':static['notebook_count'],'run_all_pass':notebooks['run_all_pass'],'static_and_checkpoint_smoke_only':notebooks['static_model_smoke_only'],'helper_tests':14,'helper_coverage_percent':coverage,'receipts':[str(path.relative_to(ROOT)) for path in sorted((P2/'smoke').glob('*.json'))],'full_training_run_all_executed':False,'training_steps':0,'scientific_TEST_forward':0,'scope':'Run All readers/TRAIN demos and A04 default dry-run; historical training notebooks static plus isolated checkpoint fixtures/TRAIN smoke'})
    save(DOCS/'relocation_receipts.json',{'status':'PASS','original_files':preservation['original_file_rows'],'phase1_handoff_files':preservation['phase1_handoff_files'],'canonical_map':'docs/reorganization/phase2/canonical_map.json','runtime_view_map':'docs/reorganization/phase2/runtime_view_map.json','runtime_aliases':load(P2/'runtime_view_map.json')['count'],'required_folders':33,'original_bytes':'PASS','symlinks_required':False,'copy_fallback':True,'cleanup_deferred_to_phase3':True,'nested_web_metadata_preserved':True,'training_steps':0,'scientific_TEST_forward':0})
    text(DOCS/'phase2_report.md',f'''# REORG Phase2 — COMPLETE (31/10/2026)

Đã đưa code vào 11 folder yêu cầu, đủ 33 thư mục datasets/notebooks/web. A01–A06 và tiểu luận1 lấy đúng nguồn Git Phase1; agent01/agent02 giữ source, báo cáo, output và hai web-demo chưa commit. Source V3 nằm trong tieuluan3; tiểu luận2 là revision Ch1–5, không có nhánh/menu/API multi-agent, vẫn giữ RNN–LSTM/KG–RAG. Tiểu luận3 giữ sáu chương.

## Bảo toàn

Đối chiếu SHA256/size **{preservation['original_file_rows']:,} dòng file gốc** và **{preservation['phase1_handoff_files']} file Phase1 handoff** PASS. `canonical_map.json` phân biệt canonical revision với `baseline_path` bất biến. Notebook gốc/output, raw, checkpoint, metric, prediction, DOCX/PDF và seal vẫn giữ byte gốc. Không sửa seal, không train, không scientific TEST forward, không đổi env, không commit/push/deploy. Nested Git metadata Agent01 nằm trong provenance riêng, không thành submodule.

Layout tương thích có 145.483 alias tạo bằng hardlink/copy kiểm hash, không yêu cầu symlink/junction. Nó giữ tên module dùng bởi serialized artifact, gồm `term_paper` và `agent02_assignment`, trong khi entry point công khai dùng tên mới.

## Kiểm chứng

- {static['notebook_count']} notebook chính schema/AST PASS; {static['python_ast_files']} Python AST PASS; {static['catalog_file_references_exist_and_size_match']:,} tham chiếu file dataset tồn tại/đúng kích thước.
- Run All {notebooks['run_all_pass']} notebook kết quả/demo TRAIN/dry-run PASS; {notebooks['static_model_smoke_only']} notebook huấn luyện/EDA lịch sử kiểm tĩnh + checkpoint smoke riêng. Không gọi đây là đã train hoặc full Run All toàn bộ notebook huấn luyện.
- 14 helper test PASS; coverage tổng helper **{coverage:.2f}%**. Không suy rộng coverage này sang toàn bộ 11 bài.
- TypeScript `--noEmit` của React tiểu luận2 PASS với dependency cache đã có; Python lint migration helper, parser PowerShell và scoped `git diff --check` PASS. Build sản phẩm và E2E vẫn thuộc Phase3.
- Smoke riêng đủ 11 bài: A01/A02 năm model diabetes; A03 ba golden pipeline (sai số <1e-6); A04 năm checkpoint mỗi native framework; A05 12 Keras checkpoint; A06 hai RNN mỗi framework trên window TRAIN; tiểu luận1 bốn asset; AG02 70 input sealed; Agent01 maze/BFS; API tiểu luận2/3 readiness và fixture/TRAIN inference.
- CIFAR binary adapter parity pixel/nhãn chính xác trên tám ảnh TRAIN; canonical archive giữ hash. A06 Git LF/Windows CRLF có hàng CSV giống hệt; chỉ view dùng bản CRLF để thỏa guard cũ.
- Notebook CNN/RNN/LSTM tiểu luận dùng serving registry pin seed42 vì demo thí nghiệm cũ đòi Git HEAD lúc train. Đây là revision có khai báo; code/guard/lock cũ giữ nguyên. Backend demo thực tế NumPy CPU, không báo latency như native GPU.

## Các điều chỉnh đã ghi bằng chứng

Schema import tabular A04 cần PROJECT_ROOT ngoài nhánh train; A05 bỏ guard đường dẫn Anaconda ở revision notebook; A04/A06 tách notebook mixed-framework để không cài trộn env. Một archived AG02 notebook được phục hồi nguyên byte khi bootstrap ban đầu chọn nhầm. README dataset V3 gốc được phục hồi exact hash từ Git vào provenance; canonical catalog README là file mới. Lỗi phát triển/attempts giữ trong journal, receipt PASS cuối luôn gắn SHA revision hiện hành.

## Chạy và bàn giao

Xem [hướng dẫn kernel/lệnh chạy](phase2_runtime.md), README từng bài và [bản đồ repository](../repository_manifest.md). Hai env WSL hiện có được tái sử dụng; runner chọn interpreter/kernel và không cài dependency. `datasets/catalog.json` chỉ rõ đường dẫn thật; dữ liệu/checkpoint lớn ignored/local cần giữ khi chuyển máy. Metadata/manifest được version, payload không tự có trong clean checkout.

Source web đã đúng nơi; build/serve/E2E, sửa notebook download, Render entrypoint/bundle và dọn cache/source cũ thuộc **Phase3**. Không khẳng định 11 web đã nghiệm thu. Chưa dựng DOCX tiểu luận2. Legacy node_modules/dist ở apps/web, staging/backup vẫn được giữ đến gate Phase3. Lệnh tiếp theo: `làm phase 3`.
''')
    text(DOCS/'phase2_rollback.md','''# Rollback REORG Phase2

Không git reset/clean/checkout cả cây. Dừng runner do migration sở hữu trước. Đọc canonical_map.json và relocation journal; baseline_path trỏ byte gốc, old_path là đường dẫn logic cũ. Nếu phục hồi layout cũ, copy baseline vào một thư mục revision riêng, kiểm SHA256/bytes rồi mới chọn entry point; không ghi đè source hiện hành hoặc file người dùng.

Staging và backup Phase1 vẫn có; commit/blob/OID trong restoration/supplementary manifests có thể lấy lại code đã commit. Hai web chưa commit và nested metadata phải lấy từ backup_manifest/bản provenance, không thể dựa Git root để khôi phục. Scientific raw/checkpoint unique không xóa. Runtime view tái tạo được từ runtime_view_map, dùng source/hash hiện hành (có CRLF representation adapter A06); không dùng map_base cũ để ghi đè revision.
''')
    paths=[P2/'canonical_map.json',P2/'runtime_view_map.json',P2/'static_verification.json',P2/'original_byte_preservation.json',P2/'notebook_execution_summary.json',P2/'helper_tests_r3.xml',P2/'helper_coverage_r3.json',P2/'representation_adapters.json',P2/'cifar_train_adapter_parity.json',P2/'a06_raw_guard.json',P2/'code_checks.json',P2/'catalog_paths_sizes.json',DOCS/'notebook_smoke.json',DOCS/'relocation_receipts.json',DOCS/'phase2_report.md',DOCS/'phase2_runtime.md',DOCS/'phase2_rollback.md']
    paths += sorted((P2/'smoke').glob('*.json'))
    paths += [ROOT/project/name for project in PROJECTS for name in ['project.json','datasets/catalog.json']]
    paths += sorted((ROOT/'_shared/assignment_runtime').glob('*.py'))
    paths += [ROOT/'scripts'/name for name in ['run_assignment.py','run_assignment.ps1','run_assignment.sh','materialize_project.py','datasets.py']]
    save(DOCS/'phase2_handoff.json',{'status':'COMPLETE','phase':2,'date':'2026-10-31','files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in paths],'next_phase':3,'source_preserved':True,'scientific_TEST_forward':0,'training_steps':0})
    checkpoint=load(DOCS/'checkpoint.json')
    checkpoint.update(active_phase=None,next_phase=3,completed_phases=[1,2],last_action='REORG Phase2 COMPLETE: 11 projects/33folders; original-byte verification and current notebook/model smoke PASS. No train/TEST/env install/commit/push/deploy.',next_action='Wait for user: làm phase 3. Complete 11web/build/Render config and gated cleanup.',active_processes=[])
    checkpoint['phases']['2'].update(status='COMPLETE',report='docs/reorganization/phase2_report.md',evidence='docs/reorganization/phase2_handoff.json')
    save(DOCS/'checkpoint.json',checkpoint)
    plan=ROOT/'ASSIGN_REORGANIZATION_EXECUTION_PLAN.md'
    content=plan.read_text(encoding='utf-8-sig')
    content=content.replace('Trạng thái: Phase1 COMPLETE; Phase2–3 NOT_STARTED. Đã phục hồi vào staging, chưa di chuyển source.','Trạng thái: Phase1–2 COMPLETE; Phase3 NOT_STARTED. Source đã về11 bài; web/build/Render và cleanup còn ở Phase3.')
    content=content.replace('Trạng thái: NOT_STARTED. Dependency: Phase1 COMPLETE.','Trạng thái: COMPLETE (31/10/2026). Dependency: Phase1 COMPLETE.')
    content=content.replace('| 2 | NOT_STARTED | Đọc Phase1 handoff; tổ chức11bài và xử lý path/runtime/dataset-format |','| 2 | COMPLETE | 11bài/33folder, source/hash/nb/runtime smoke PASS; xem phase2_report.md |')
    content += '\n31/10/2026 — REORG Phase2 COMPLETE: xem docs/reorganization/phase2_report.md và phase2_handoff.json. Không train/TEST lại, đổi env, commit/push/deploy. Tiếp Phase3 chỉ khi được yêu cầu.\n'
    text(plan,content)
    agents=ROOT/'AGENTS.md'
    content=agents.read_text(encoding='utf-8-sig')
    marker='## REORG Phase2 COMPLETE —31/10/2026\n'
    if marker not in content:
        entry='''## REORG Phase2 COMPLETE —31/10/2026

- Source đã về11 bài, đủ33folder. Đọc `docs/reorganization/phase2_report.md`, `phase2_handoff.json`, checkpoint và toàn bộ plan trước Phase3.
- Mapping bất biến/active revision: `phase2/canonical_map.json`; alias dùng `runtime_view_map.json` và `scripts/materialize_project.py`. Không chạy lại relocate/setup/derive producer Phase2.
- Runtime vẫn Ubuntu/user tuananh, hai env torch/keras hiện có. Runner `scripts/run_assignment.ps1` chọn đúng framework; đọc README từng bài.
- Original byte/hash và Phase1handoff đã PASS; không train/TEST, sửa lock/seal, đổi env hoặc resume queue lịch sử. Sửa scientific file cần revision giữ bản gốc.
- Paper2 chỉ Ch1–5, paper3 đủ6chương. Notebook demo Ch3/4 dùng `assignment_runtime.paper_demo` serving-registry seed42; guard Git lịch sử giữ nguyên. A06 CRLF adapter chỉ trong view, canonical LF giữ hash.
- Phase3 còn11web/build/E2E/Render packaging và cleanup. `apps/web/node_modules`/dist cũ, staging, backup giữ đến gate. Chưa commit/push/deploy. Không tự bắt đầu Phase3.

'''
        content=content.replace('# Quy tắc làm việc cho tiểu luận V3',entry+'# Quy tắc làm việc cho tiểu luận V3',1)
        text(agents,content)
    print('Phase2 COMPLETE; next phase3 (not started)')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action',choices=['navigation','complete'],required=True)
    args=parser.parse_args()
    globals()[args.action]()
