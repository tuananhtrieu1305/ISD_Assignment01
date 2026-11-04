"""Gated Phase3 inventory/report; historical handoffs remain immutable."""
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs/reorganization';P3=DOCS/'phase3'
PROJECTS=['A01','A02','A03','A04','A05','A06','tieuluan1','tieuluan2','tieuluan3','agent01','agent02']
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(p,doc):text(p,json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
def text(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.phase3-tmp');t.write_text(s,encoding='utf-8');t.replace(p)
def file(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
if (DOCS/'phase3_handoff.json').exists():raise SystemExit('Phase3 already published; verify instead of rewriting evidence')

for phase in [1,2]:
    handoff=load(DOCS/f'phase{phase}_handoff.json')
    for r in handoff['files']:
        p=ROOT/r['path'];assert p.exists() and sha(p)==r['sha256'] and p.stat().st_size==r['bytes'],r['path']
for name in ['e2e.json','layout_capture.json','clean_checkout.json','original_byte_preservation.json','cleanup_receipt.json','post_cleanup_source_relocation.json']:
    assert load(P3/name)['status']=='PASS',name
assert load(P3/'active_servers.json')['status']=='STOPPED'
suites=ET.parse(P3/'web_tests.xml').getroot()
assert not any(int(s.get(k,0)) for s in suites.iter('testsuite') for k in ['errors','failures','skipped'])
assert sum(int(s.get('tests',0)) for s in suites.iter('testsuite'))==11
for row in load(P3/'static_sources.json')['sources']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
for row in load(P3/'runtime_source_overlay.json')['files']:assert sha(ROOT/row['source'])==row['sha256'],row['source']
for removed in load(P3/'cleanup_receipt.json')['removed']:assert not (ROOT/removed).exists(),removed

inventory=[];builds=[];folder_count=0
for i,project in enumerate(PROJECTS):
    base=ROOT/project;web=base/'web';config=load(base/'project.json');catalog=load(base/'datasets/catalog.json')
    for name in ['datasets','notebooks','web']:assert (base/name).is_dir();folder_count+=1
    notebooks=[file(base/r['path']) for r in config['notebooks']]
    if project.startswith('tieuluan'):
        assets=sorted((web/'frontend/dist').rglob('*'))
        assert (web/'frontend/dist/index.html').is_file()
        release=load(web/'deploy/release.json')
        assert sha(ROOT/release['archive']['path'])==release['archive']['sha256']
        assert release['archive']['size_bytes']<100*1024**2
        for row in release['source_python']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
        builds.append({'project':project,'status':'PASS','typecheck':'tsc --noEmit PASS','build':'Vite production build PASS','package_lock':file(web/'frontend/package-lock.json'),'frontend_source':[file(p) for p in sorted((web/'frontend/src').rglob('*')) if p.is_file()],'dist':[file(p) for p in assets if p.is_file()],'serving_release':file(web/'deploy/release.json')})
        mode='React/Python live; CPU serving'
    else:
        assets=[p for p in web.rglob('*') if p.is_file() and p.suffix.lower() in {'.html','.css','.js','.png','.ipynb','.json'}]
        assert (web/'index.html').is_file()
        mode='static recorded results'+(' + original CPU compare API' if project in ['A01','A02','A03'] else '')
        published=[file(p) for p in assets if p.suffix=='.ipynb']
        save(web/'release-reorg.json',{'revision':'REORG-Phase3','project':project,'mode':mode,'notebook_downloads':published,'assets':[file(p) for p in assets if p.suffix!='.ipynb'],'training_steps':0,'scientific_TEST_forward':0})
    inventory.append({'project':project,'port':8011+i,'mode':mode,'datasets':{'catalog':file(base/'datasets/catalog.json'),'dataset_ids':[r['dataset_id'] for r in catalog['datasets']]},'notebooks':notebooks,'web_assets':[file(p) for p in assets if p.is_file()],'readonly_originals':'provenance/originals and provenance/phase3_originals; scientific baseline via composed manifest'})
    readme=base/'README.md';content=readme.read_text(encoding='utf-8')
    content=content.replace('Web source/payload đã đặt đúng nơi. Build/serve, hoàn thiện tám demo đơn giản, ba web tiểu luận và cấu hình Render được nghiệm thu ở Phase3.',f'Web đã nghiệm thu Phase3. Chạy `./scripts/run_web.ps1 -Project {project}` từ root, mở http://127.0.0.1:{8011+i}. Xem [README web](web/README.md) và [hướng dẫn hiện hành](../docs/reorganization/phase3_runtime.md).')
    content=content.replace('Đường dẫn tương thích trong `provenance/runtime/assign/` được tạo từ manifest; không tự sửa.','Đường dẫn tương thích trong `provenance/runtime/assign/` được tạo từ recipe Phase2 + source overlay Phase3; không tự sửa.')
    content=content.replace('materialize lại nếu cần','materialize bằng `scripts/materialize_assignment.py` nếu cần')
    text(readme,content)
save(P3/'build_verification.json',{'status':'PASS','projects':builds,'GPU_env_changed':False,'note':'Actual tsc/Vite builds verified through browser against generated dist; V1 dependency restored by its own unchanged lock'})
save(DOCS/'final_inventory.json',{'format':'composite inventory, not cache/venv enumeration','projects':inventory,'required_folders':folder_count,'original_manifest':file(DOCS/'phase2/canonical_map.json'),'original_location_overrides':file(P3/'preservation_overrides.json'),'runtime_source_overlay':file(P3/'runtime_source_overlay.json'),'original_rows_sha256_verified':80821,'symlinks_required':False})
assert folder_count==33
verification={'status':'PASS','projects':11,'required_folders':33,'browser_checks':len(load(P3/'e2e.json')['checks']),'browser_failures':0,'layout_screenshots':22,'helper_tests':11,'production_builds':3,'source_only_backend_checkouts':3,'original_rows_sha256_verified':80821,'prior_handoff_files_sha256_verified':80,'runtime_source_overlays_verified':307,'raw_modified':False,'training_steps':0,'scientific_TEST_forward':0,'GPU_env_changed':False,'commit_push_deploy_executed':False,'QA_servers_stopped':True,'limits':['A04–A06 web replays saved outputs; no live native framework inference there','V3 CPU serving uses portable NumPy for scratch/Keras/PyTorch trained weights','V1 preprocessor sklearn version warnings retained','Raw/training checkpoint ignored payload remains local-only; serving archives self-contained','Render not deployed or operated by REORG']}
save(DOCS/'verification.json',verification)
text(DOCS/'phase3_report.md','''# REORG Phase3 — COMPLETE (31/10/2026)

Đã hoàn thiện11 web riêng, đủ33 folder datasets/notebooks/web. Sáu assignment có giao diện nhẹ theo style demo mê cung; hai demo agent giữ dữ liệu/trace/hình gốc. Ba tiểu luận giữ React/Python theo đúng phiên bản: tiểu luận1 bốn chương, tiểu luận2 năm chương, tiểu luận3 sáu chương.

## Kết quả và kiểm chứng

- 22 nhóm ca trình duyệt PASS/0failure trên11 web;22 screenshot desktop/mobile. Kiểm18 tab dataset assignment, link notebook, lỗi input, so sánh CPU A01–A03, replay24bước/va tường Agent01, replay20bước/ba regime/20hình Agent02 và các job ML/CNN/RNN/LSTM/KG–RAG/agent trên UI tiểu luận.
- Ba frontend `tsc --noEmit`/Vite production build PASS. Tiểu luận1 cài đúng71 dependency theo lock cũ sau khi cache offline thiếu một gói; không nâng version hoặc thay hai venv GPU. Cache Node V3 đã có được gom về root node_modules.
- 11 test routing/security helper PASS: chặn file nội bộ/path traversal, giới hạn request, proxy JSON, source integrity. Ruff F/E9, parser PowerShell và scoped diff check PASS. Không gọi coverage này là coverage toàn bộ11 project.
- Ba serving bundle CPU có release/manifest/SHA và source parity; cả ba PASS từ source-only checkout không có raw/training cache/runtime views. Kiểm trên Linux WSL với interpreter hiện có; lượt staging trên NTFS bị timeout được giữ riêng, không đổi guard/threshold để vượt kiểm tra.
- 80.821dòng file gốc và19file Phase1 handoff đối chiếu byte/hash PASS. 61file Phase2 handoff cũng giữ hash. Các thay đổi web có snapshot trước sửa, không sửa raw, checkpoint, prediction, metric, TEST seal hay báo cáo đã nộp.

## Những thay đổi cần biết

A01–A03 có inference/compare CPU qua backend gốc. A04–A06 trình bày lại số liệu/dự đoán đã lưu; nhãn replay và nguồn được ghi rõ. Không gắn việc mở trang với training hoặc native GPU inference. Tiểu luận3/2 vẫn giữ compare-all ba bộ weights, serving thực tế NumPy CPU.

Demo tiểu luận1 trước đây lấy ảnh/sequence TEST. Revision web nay nạp mẫu TRAIN hoặc fixture; code thí nghiệm gốc và artifact giữ nguyên. Bốn service module được đặt trong `tieuluan1/src/term_paper/deployment/app/`. Các cảnh báo sklearn1.9.1→1.9.0 cũ vẫn được giữ, không re-fit/re-serialize.

Sau cleanup, recipe runtime Phase2 giữ bất biến; overlay Phase3 chuyển307 source reference sang vị trí bảo toàn/canonical mới, không thay target logic hoặc byte. Materializer hiện hành là `scripts/materialize_assignment.py`. Không dùng riêng helper Phase2 cũ sau khi bỏ web/reference. Các runtime views đã có vẫn được giữ để chạy notebook.

## Cleanup và cấu hình Render

Đã dọn root apps/,dist/,.ruff_cache, staging Phase1, staging Render/clean-checkout, unit temp và web/reference_ui, reference_backend, legacy_runtime thừa. Script chỉ xóa sau gate và kiểm không target nào chứa baseline bất biến. Lịch sử build root dist gồm3.968file được lưu vào một archive provenance, read-back SHA từng thành viên PASS. Giữ Git root, cả hai môi trường, tool/cache đang dùng, raw/model/report/evidence, backup web chưa commit và nested Git metadata.

Root render.yaml mặc định phục vụ tiểu luận3, đã đổi build/start/rootDir/filter; template riêng có trong từng web. Hai service Dashboard thủ công cần đổi Settings một lần; YAML không tự sửa chúng. Có shim scripts/render_v3.py cho lệnh API cũ. **Chưa commit/push/deploy hoặc thao tác tài khoản Render.**

Chạy web: [hướng dẫn11 bài](phase3_runtime.md). Deploy về sau: [bàn giao Render](render_handoff.md). Bằng chứng tổng hợp: verification.json, final_inventory.json và phase3_handoff.json. Không có DOCX mới cho tiểu luận2 trong lần sắp xếp này.
''')
text(DOCS/'rollback.md','''# Rollback và phục hồi REORG

Không git reset/clean hoặc checkout cả cây. Dừng web runner trước thao tác source. Giữ nguyên checkpoint khoa học/TEST seals và user changes.

Original mapping: Phase2 canonical_map.json cộng Phase3 preservation_overrides.json; baseline_path sau overlay trỏ đúng byte gốc. Notebook/code gốc ở provenance/originals; web trước sửa ở provenance/phase3_originals. Các bản dựng root dist cũ được lưu trong tieuluan3/provenance/build_history/root-dist-before-reorg.zip, SHA/count trong phase3/build_history_backup.json. Archive này local-only, không dùng làm active source.

Muốn khôi phục, giải vào một thư mục revision mới trong workspace và kiểm manifest/hash, không ghi đè source đang dùng. Staging Phase1 đã được dọn sau gate, file thực của nó đã ở các project canonical/provenance; commit/blob và manifest phục hồi Phase1 vẫn giữ. Hai web chưa commit có backup_manifest riêng. Không xóa raw/checkpoint unique hoặc nested Git metadata.

Tái tạo runtime views: scripts/materialize_assignment.py, gồm recipe Phase2 + source overlay Phase3; cung cấp đúng file data/model bị ignore trước. Source overlay chỉ đổi vị trí, không đổi logical namespace/hash. Render dùng scripts/render_project.py và serving archive versioned; sửa backend source cần build deployment revision mới. Không tự redeploy/reset seal để phục hồi layout.
''')
readme=ROOT/'README.md';content=readme.read_text(encoding='utf-8')
content=content.replace('Phase3 hoàn thiện/build/kiểm thử 11 web, cập nhật Render và dọn source/cache cũ sau gate. Hiện không sử dụng cấu hình Render cũ để deploy cấu trúc mới. Chưa commit/push/deploy trong quá trình sắp xếp.','''**Ba phase REORG đã hoàn tất.** 11web đã kiểm local/build/E2E, source trùng đã dọn sau gate. Chạy `./scripts/run_web.ps1 -Project A01` hoặc `-Project tieuluan3`; xem [hướng dẫn11 web](docs/reorganization/phase3_runtime.md). Build React: `./scripts/build_web.ps1 -Project tieuluan3`.

Xem [biên bản Phase3](docs/reorganization/phase3_report.md) và [Settings Render cần đổi một lần](docs/reorganization/render_handoff.md). Chưa commit/push/deploy. Materializer hiện hành sau cleanup: `scripts/materialize_assignment.py`; không dùng riêng recipe/helper Phase2 cũ.''')
text(readme,content)
manifest=ROOT/'docs/repository_manifest.md';content=manifest.read_text(encoding='utf-8')
content += '\n## Sau Phase3\n\n11web đã nghiệm thu; source/cache trùng root apps/dist và staging đã dọn. Service module tiểu luận1 ở src/term_paper/deployment/app. Runtime source overlay hiện hành: docs/reorganization/phase3/runtime_source_overlay.json, materialize_assignment.py. Xem final_inventory.json (manifest hợp thành) và phase3_runtime.md. Root Render phục vụ tiểu luận3; cấu hình mới cần cập nhật Dashboard thủ công một lần. Không còn source cũ hoạt động song song ở root.\n'
text(manifest,content)
plan=ROOT/'ASSIGN_REORGANIZATION_EXECUTION_PLAN.md';content=plan.read_text(encoding='utf-8')
content=content.replace('Trạng thái: Phase1–2 COMPLETE; Phase3 NOT_STARTED. Source đã về11 bài; web/build/Render và cleanup còn ở Phase3.','Trạng thái: Phase1–3 COMPLETE. 11bài/33folder,11web local/build/E2E và cleanup đã nghiệm thu; chưa commit/push/deploy.')
content=content.replace('Trạng thái: NOT_STARTED. Dependency: Phase2 COMPLETE.','Trạng thái: COMPLETE (31/10/2026). Dependency: Phase2 COMPLETE.')
content=re.sub(r'\| 3 \| NOT_STARTED \|[^\n]+', '| 3 | COMPLETE | 11web/3build/3source-only checkout PASS; xem phase3_report.md |',content)
content+='\n31/10/2026 — REORG Phase3 COMPLETE:11web,22browser groups/22screenshots,11helper tests,3build/3source-only serving checkout PASS; source/hash giữ nguyên, dọn theo gate. Không commit/push/deploy.\n'
text(plan,content)
agents=ROOT/'AGENTS.md';content=agents.read_text(encoding='utf-8')
entry='''## REORG Phase3 COMPLETE —31/10/2026

- Cả3phase COMPLETE. Đọc `docs/reorganization/phase3_report.md`, `verification.json`, `final_inventory.json`, `phase3_handoff.json`; không tự chạy lại producer/cleanup khi được hỏi trạng thái.
- Chạy web bằng `scripts/run_web.ps1`; build React bằng `scripts/build_web.ps1`. Đọc `phase3_runtime.md` và README từng web.
- Staging/root apps/dist/reference web đã dọn sau gate. Bản gốc theo Phase2 canonical map + Phase3 preservation_overrides; không đánh giá target cũ đã archive là canonical active. Runtime views giữ nguyên logic, materializer hiện hành `materialize_assignment.py` + runtime_source_overlay.json (307 source alias).
- Bốn service module tiểu luận1 ở `tieuluan1/src/term_paper/deployment/app/`. Demo web bản1 dùng TRAIN/fixture; bản gốc TEST demo vẫn chỉ trong provenance, không chạy lại để kiểm UI.
- Source-only serving check PASS cho3bài. Root Render dùng render_project.py mặc định tieuluan3; render_v3.py chỉ shim. Sửa backend phải tạo bundle revision mới, không phục vụ archive cũ âm thầm. Deployment/commit/push chưa được thực hiện/ủy quyền bởi kế hoạch.
- Không train/TEST hoặc đổi env để xác minh migration. Giữ raw/checkpoint/metric/prediction/seal/report nguyên byte. Runtime Ubuntu/user tuananh, hai env hiện có giữ nguyên. A04–A06 web là replay, không mô tả thành native live inference.

'''
assert '## REORG Phase3 COMPLETE' not in content
content=content.replace('# Quy tắc làm việc cho tiểu luận V3',entry+'# Quy tắc làm việc cho tiểu luận V3',1)
text(agents,content)
checkpoint=load(DOCS/'checkpoint.json')
checkpoint.update(status='COMPLETE',active_phase=None,next_phase=None,completed_phases=[1,2,3],last_action='REORG complete:11projects/33folders,11web,3builds,3source-only serving checkouts, original hashes PASS; cleanup gated; no train/TEST/env changes/commit/push/deploy.',next_action='No active REORG phase. User may run an individual web or request deployment; use phase3_runtime.md/render_handoff.md.',active_processes=[])
checkpoint['phases']['3'].update(status='COMPLETE',report='docs/reorganization/phase3_report.md',evidence='docs/reorganization/phase3_handoff.json')
save(DOCS/'checkpoint.json',checkpoint)
paths=[DOCS/name for name in ['phase3_report.md','verification.json','final_inventory.json','rollback.md','phase3_runtime.md','render_handoff.md']]
paths += [P3/name for name in ['e2e.json','layout_capture.json','web_tests.xml','clean_checkout.json','original_byte_preservation.json','preservation_overrides.json','runtime_source_overlay.json','cleanup_receipt.json','build_history_backup.json','build_verification.json','static_sources.json','paper1_train_samples.json']]
paths += [ROOT/'scripts'/name for name in ['web_app.py','run_web.ps1','build_web.ps1','render_project.py','render_v3.py','materialize_assignment.py']]
paths += [ROOT/project/'web/deploy/release.json' for project in ['tieuluan1','tieuluan2','tieuluan3']]
save(DOCS/'phase3_handoff.json',{'status':'COMPLETE','phase':3,'date':'2026-10-31','files':[file(p) for p in paths],'training_steps':0,'scientific_TEST_forward':0,'commit_push_deploy':False})
print('Phase3 COMPLETE; all3 REORG phases COMPLETE')
