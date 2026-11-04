"""Mechanical JSX version/label update; r8 originals were preserved first."""
from pathlib import Path
P=Path(__file__).resolve().parents[2]
path=P/'web/frontend/src/main.jsx';source=path.read_text(encoding='utf-8')
changes=[("ready.runtime_revision!=='full-demo-r8'","ready.runtime_revision!=='source-verification-r9'"),
 ('để nạp pipeline r8 có Risk → Reporter (vẫn 3 generation).','để nạp pipeline r9 có quy tắc kiểm chứng nguồn dùng chung (vẫn 3 generation).'),
 ('Mỗi lượt dùng đúng3 generation request. Embedding truy vấn','Cả hai nhánh dùng cùng tiêu chuẩn kiểm chứng nguồn. Mỗi lượt dùng đúng3 generation request. Embedding truy vấn')]
for old,new in changes:
    assert source.count(old)==1,old
    source=source.replace(old,new)
path.write_text(source,encoding='utf-8')
