# Serving environment v2

`uv.lock` resolve trên WSL Python **3.11.17** ngày 02/11/2026. Chưa install/sync, chưa smoke SDK. `pyproject.toml` là đầu vào; dùng `uv sync --frozen` ở Phase 2 với env riêng, không `pip install` vào torch/keras env đã khóa. Không chạy unpinned requirements nhóm.

Chỉ giữ dependency thực sự cần cho schema/LangChain strategy+splitter, Gemini SDK, BM25, NumPy, Flask/Gunicorn và PyVis. Không GPU package hoặc provider khác. LangChain Gemini wrapper gốc được nối bridge SDK Interactions để dùng endpoint đã probe; thay đổi này phải thể hiện trong reuse map và notebook, không fallback OpenAI.

Lock chứa72 package và hash wheel/sdist; đây là **resolve PASS**, chưa là môi trường chạy PASS. Sau port nếu cần đổi dependency phải tạo lock revision có lý do, không nâng ngầm GPU env.
