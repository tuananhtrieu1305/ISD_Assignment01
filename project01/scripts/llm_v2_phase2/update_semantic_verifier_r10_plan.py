"""Preserve and annotate the current plan with the explicit user r10 override."""
from pathlib import Path
import hashlib,json,shutil
P=Path(__file__).resolve().parents[2];ROOT=P.parent
source=ROOT/'FINAL_PROJECT01_LLM_V2_EXECUTION_PLAN.md'
target=P/'provenance/before_semantic_verifier_r10/root_files'/source.name
assert not target.exists(),'Plan original already preserved'
shutil.copy2(source,target)
sha=hashlib.sha256(source.read_bytes()).hexdigest();assert hashlib.sha256(target.read_bytes()).hexdigest()==sha
receipt={'path':source.name,'archive':target.relative_to(ROOT).as_posix(),'sha256':sha}
(target.parent/'plan_preservation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
text=source.read_text(encoding='utf-8');first,rest=text.split('\n',1)
note='\n**Override r10 theo yêu cầu người dùng 03/11/2026:** Verifier gọi Gemini một lần để kiểm ngữ nghĩa/số và có thể sửa bản nháp ngay trong call đó, sau đó code kiểm cứng citation/score. Một cặp hợp lệ dùng4generation: direct+Coordinator+Reporter+Verifier; reranker/Risk local, không có repair call riêng. Chế độ demo mặc định gửi hồ sơ TRAIN đủ21field; combined thiếu hồ sơ bị chặn trước API. Budget/UI/backend dùng4slot. Các đoạn r7 về đúng3call và Verifier chỉ-code bên dưới là lịch sử, bị override này thay thế. Đọc `project01/docs/llm_v2/SEMANTIC_VERIFIER_R10.md`; chưa gọi API thật cho r10. Evaluation40cặp dự trù160generation, chưa mở held-out.\n'
text=(first+'\n'+note+rest).replace('Phiên bản 2.4 —','Phiên bản 2.5 —',1)
source.write_text(text,encoding='utf-8')
