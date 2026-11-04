# Nhật ký tích hợp Render V3 r1

Yêu cầu người dùng: sửa source để deploy **cùng repository** lên hai service Render
hiện có, cả hai gói Free. Không yêu cầu tự commit/push hoặc thao tác tài khoản.

## Phạm vi revision

- Root `render.yaml` chuyển sang entry point/build CPU V3, giữ tên hai service.
- Bản YAML trước được copy ở `deploy/render-v3-r1/render-v2-before.yaml`.
- `scripts/render_v3.py` và test mới độc lập; source/backend/UI đã khóa không sửa.
- Bản sao ZIP Phase32 nguyên SHA nằm ở đường dẫn Git không ignore, không cần upload
  toàn bộ folder checkpoint hoặc raw dataset. Spec `release.json` không thay các khóa cũ.
- `.render-v3/` được ignore, staging riêng, không ghi đè file trong repo phát triển.
- Hướng dẫn thao tác Dashboard/commit: `deploy/render-v3-r1/README.md`.

## Bằng chứng development giữ lại

- `artifacts/manifests/render_v3_r1/red.xml`: test RED trước implementation.
- `development.xml`:33 test PASS lúc đầu.
- `development_r2.xml`:44PASS/1FAIL; fixture nhầm gói không chứa `data/raw` nào.
  Đã kiểm ZIP thực:11 JSON snapshot Wikidata allowlisted cần cho structural browser.
  Sửa assertion theo inventory thật, không sửa gói/source/model hoặc bỏ kiểm hash.
- Production Vite lần đầu bị Windows sandbox chặn ghi `.vite-temp`; retry có quyền
  build worker đã PASS, không đổi config/frontend để vượt lỗi quyền.
- Lượt pip download vào CPU-only QA env riêng được dừng đúng PID do tải tuần tự chậm;
  chưa cài xong. Offline uv xác nhận cache GPU cũ không đủ CPU wheel. Lượt tiếp dùng
  uv với SHA-lock, cache QA riêng, không đổi version/dependency hoặc dùng mirror tùy ý.

## Nguyên tắc giữ lâu dài

Không tắt integrity check khi deploy fail. React chỉnh bình thường và auto-build từ
source commit; source backend khoa học đã khóa cần explicit deployment revision nếu đổi,
để ZIP cũ không âm thầm che thay đổi. Model không cần train lại khi đổi deployment.

Manual Dashboard settings không tự cập nhật chỉ vì commit root YAML. Owner phải đổi
Build/Start/Python/CORS một lần theo README, sau đó push sẽ trigger auto-deploy như cũ.
Không tự tạo thêm service, nâng plan, reset Git hoặc ghi đè khóa Phase22–35.

## Nghiệm thu hoàn tất

- 46 test/0skip ở `final_tests_r2.xml`; coverage `final_coverage_r2.json`:
  combined96,3134%, statement97,3856%, branch93,75%. R1 được giữ lịch sử.
- 8 E2E/0retry/0skip tại `ui.xml`/`ui.json`:4 neural TRAIN comparison (MLP/CNN/RNN/LSTM),
  FinQA compact demo_not_benchmark, Gold agent parent-TRAIN, deep-link refresh và CORS.
  Tổng20 live result slot thành công NumPy CPU. Neural prediction/hash khớp ref Phase32.
  Không train hoặc replay scientific TEST, không gọi tất cả demo là benchmark TRAIN.
- Fresh CPU-only venv `/tmp/ai-paper-render-v3-r1-cpu`:26 CPU dependency cài bằng uv
  `--require-hashes` từ PyPI, cache QA `/tmp/ai-paper-render-v3-r1-uv-cache` riêng.
  Sau đó lệnh build pip trong `scripts/render_v3.py` PASS, `pip check` PASS, package
  inventory không Torch/TensorFlow/Keras. Không sửa hai venv GPU hoặc `uv.lock`.
- Runtime QA trên ext4 `/tmp/ai-paper-render-v3-r1-runtime`; Gunicorn chạy bằng chính
  CPU-only interpreter, một worker/hai thread. Không phải native framework GPU timing.
- TypeScript/Vite production PASS, URL API HTTPS đúng trong output riêng
  `report/build/render-v3-r1/web-production`; build local riêng `web-local` cho E2E.
- Preservation31848 file/12parent lock PASS tại `preservation.json`; public check Phase35
  read-only PASS391 file. Word/PDF release và checkpoint/model/TEST giữ hash.
- Source mới lint/format PASS; root YAML parsed bằng PyYAML, tên service/route/env được
  unit test kiểm. Chưa validate Blueprint bằng account/API Render, chưa cloud deploy.
- Chưa commit/push, chưa sửa Settings trên tài khoản, không nâng gói. Hướng dẫn Dashboard
  đầy đủ trong README; Settings thủ công vẫn trỏ V2 cho đến khi owner cập nhật.

Venv/cache/runtime QA tạm được giữ trong WSL `/tmp` để kiểm tra, không nằm trong commit.
Không coi thư mục tạm này là môi trường GPU chính hoặc runtime Render lâu dài.
