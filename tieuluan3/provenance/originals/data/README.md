# Data registry

Phase 20 giữ snapshot Chương 5 trong `raw/ch5/` và bốn input demo nhỏ trong
`processed/v2/demos/`. Dataset mới cho Chương 1–4 được tải ở Phase 23 sau khi có môi trường
GPU và giao thức V3.

Raw snapshot Ch5 không được sửa. Hash gốc nằm trong
`artifacts/manifests/ch5/raw_manifest.csv` và inventory Phase 20. Những đường dẫn V2 trong
manifest gốc được giữ nguyên để bảo toàn hash; mapping hiện tại là:

`term_paper/knowledge_rag/data/raw/` → `data/raw/ch5/`.

Không chạy lại TEST Phase 15. Các prediction đã khóa ở
`artifacts/predictions/ch5/phase15/`.
