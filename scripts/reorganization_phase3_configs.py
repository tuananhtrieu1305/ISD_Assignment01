"""Write web guides and separate Render templates without operating hosted services."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROJECTS=['A01','A02','A03','A04','A05','A06','tieuluan1','tieuluan2','tieuluan3','agent01','agent02']
for i,project in enumerate(PROJECTS):
    web=ROOT/project/'web';port=8011+i
    if project.startswith('tieuluan'):
        mode='React/Python cùng style và chức năng phiên bản gốc; '+('Chương1–5, không multi-agent.' if project=='tieuluan2' else 'bốn chương của bản1.' if project=='tieuluan1' else 'sáu chương, gồm multi-agent.')
        build='''Build frontend trong folder frontend bằng `npm ci --no-fund --no-audit` rồi `npm run build`. Node22.23.4. Backend local dùng runtime Torch/NumPy WSL hiện có, không cài TensorFlow vào backend Render. Build local đã dùng đúng lock; bản1 có cache dependency riêng.

`.env.example` trong frontend minh họa API origin. Mặc định UI gọi cùng origin với web runner; nếu tách static/backend trên Render, đặt VITE_API_BASE_URL trước khi build. Không dùng chung API URL giữa ba bài.
'''
        (web/'frontend/.env.example').write_text(f'# Optional separate API; omit to use same origin in local web runner.\nVITE_API_BASE_URL=http://127.0.0.1:{port}\n',encoding='utf-8')
        name='isd-'+project
        yaml=f'''# Optional independent services. Set actual public URLs before deploy.
services:
  - type: web
    name: {name}-api
    runtime: python
    plan: free
    region: singapore
    buildCommand: python -B scripts/render_project.py build --project {project}
    startCommand: python -B scripts/render_project.py start --project {project}
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.17
      - key: AI_CORS_ORIGINS
        value: https://{name}-web.onrender.com
      - key: WEB_ORIGIN
        value: https://{name}-web.onrender.com
      - key: AI_SERVING_MODE
        value: cpu
  - type: web
    name: {name}-web
    runtime: static
    rootDir: {project}/web/frontend
    buildCommand: npm ci --no-fund --no-audit && npm run build
    staticPublishPath: dist
    envVars:
      - key: NODE_VERSION
        value: 22.23.4
      - key: VITE_API_BASE_URL
        value: https://{name}-api.onrender.com
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
'''
        (web/'deploy/render.example.yaml').write_text(yaml,encoding='utf-8')
    else:
        mode='HTML/CSS/JS; dữ liệu kết quả/trace/figure thật đã lưu. '+('A01–A03 có thêm inference CPU qua backend gốc khi dùng runner.' if project in {'A01','A02','A03'} else 'Web phát lại kết quả, không gọi model hoặc train mới.')
        build='Không cần npm build. Có thể mở static server chỉ trỏ vào `web/` để xem replay. Để dùng inference A01–A03, dùng web runner bên dưới. Notebook download cần mở trong repository với kernel và dữ liệu theo README bài.\n'
        (web/'render.example.yaml').write_text(f'''# Static replay only; A01–A03 live API uses local Python runner.
services:
  - type: web
    name: isd-{project.lower()}-demo
    runtime: static
    rootDir: {project}/web
    buildCommand: echo "Static assets ready"
    staticPublishPath: .
''',encoding='utf-8')
    # Preserve the pre-REORG README from the Phase3 snapshot; new navigation is a revision.
    text=f'''# {project} / Web

{mode}

Từ repository root trong PowerShell:

```powershell
./scripts/run_web.ps1 -Project {project}
```

Mở **http://127.0.0.1:{port}**. Thêm `-Port 9000` nếu cần port khác. Đóng terminal hoặc Ctrl+C để dừng process của runner. Dùng WSL Ubuntu/user tuananh và Python3.11.17 hiện có. Không bootstrap/doctor hoặc tạo venv GPU mới.

{build}
Mỗi bài có API/port riêng. Không để trang của bài này trỏ backend bài khác. Dữ liệu biểu đồ giữ metric/split/đơn vị từ nguồn; xem caption và bảng. Không diễn giải replay là inference live. Mẫu demo tiểu luận1 dùng TRAIN hoặc fixture; không forward TEST để kiểm UI.

Render: root `render.yaml` mặc định phục vụ tiểu luận3. Template riêng của bài chỉ là cấu hình tham khảo; không tự sửa Dashboard, tạo service hoặc deploy. Xem `docs/reorganization/render_handoff.md` ở repository root. Dependency/data/model lớn local không tự có trong clean checkout; serving bundle có release/hash riêng.
'''
    original=web/'README.md'
    preserved=ROOT/project/'provenance/phase3_originals/web/README.md'
    if original.exists() and not preserved.exists():
        preserved.parent.mkdir(parents=True,exist_ok=True);preserved.write_bytes(original.read_bytes())
    tmp=web/'README.md.phase3-tmp';tmp.write_text(text,encoding='utf-8');tmp.replace(original)
# Repository-relative filters; backend must have the whole repo for scripts and parity sources.
root=ROOT/'render.yaml';content=root.read_text()
content=content.replace('    healthCheckPath: /health','    buildFilter:\n      paths:\n        - scripts/render_project.py\n        - tieuluan3/src/**\n        - tieuluan3/scripts/render_v3.py\n        - tieuluan3/web/backend/**\n        - tieuluan3/web/deploy/**\n        - render.yaml\n    healthCheckPath: /health',1)
content=content.replace('    rootDir: tieuluan3/web/frontend','    buildFilter:\n      paths:\n        - tieuluan3/web/frontend/**\n        - render.yaml\n    rootDir: tieuluan3/web/frontend',1)
root.write_text(content,encoding='utf-8')
print('11web README/config and Render templates written')
