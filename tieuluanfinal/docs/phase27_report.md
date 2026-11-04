# Phase27 — CNN scratch/Keras/PyTorch

Kết quả nghiệm thu ngày **18/10/2026: PASS**. Ma trận train/validation/TEST đã hoàn tất.
Trạng thái phát hành cuối và hash nằm ở `artifacts/manifests/phase27/checkpoint.json`
và `experiment_lock.json`; không nhầm khai báo trước train `release.json` với khóa nghiệm thu.
Chưa tích hợp DOCX, HTTP API, React hoặc Render.

## Phạm vi đã khóa

- IDRiD: 348 matched train, 64 validation, official TEST103; 1 ảnh train quarantine giữ nguyên.
- EuroSAT: 3.000 matched train, 4.050 validation, 4.050 TEST.
- CIFAR-10: 5.000 matched train, 5.000 validation, official TEST10.000.
- 5 Conv + 2 Dense, lần lượt 10.157 / 10.322 / 10.322 tham số; cùng canonical initial weights.
- 3 implementation × 3 seed × 3 dataset = 27 CNN, thêm 9 baseline majority.
- Batch16, max40 epoch, patience6, lr0,001, Adam canonical epsilon1e-7, global clip1;
  giữ resolution128/32/32, full validation/TEST và matched IDs Phase24.
- **Không augmentation** theo preprocessing matched đã khóa. Augmentation bổ sung cần track mới;
  không tự sửa hợp đồng đã khai báo. Class weights train chỉ dùng cho IDRiD.

Khai báo trước update tại `artifacts/manifests/phase27/release.json`, SHA-256
`c52c74b8f82d3b4d716707b30384c8efc1fc09139387609c1ccc4144735d05fb`.
Fingerprint 42 source file:
`01e3a9025202e8e5f047f10f0d0cb9add4a482642c39db3d4fbb5b96688fc2d6`.
Không sửa source train/prepare/controller/worker hoặc config đã khai báo.

## Đã triển khai và kiểm tra

Cache development uint8 NHWC, nhãn int64 và ID Unicode; không pickle, không lưu float32 nguyên tập.
Kiểm **mọi model pixel hash** theo index Phase24; kiểm reference pixel/ID/layout trên train/validation.
CIFAR chỉ cần một lượt TAR.GZ stream thay vì mở lại archive cho từng ảnh.
Giới hạn 256MiB/cache, host C luôn phải còn reserve5GiB; không dựa free ảo WSL root.
Cache TEST riêng không được dựng trước consumed claim.

Trainer dùng core Phase25 nguyên hash. Scratch tự Conv/pool/loss/backward/Adam bằng NumPy CPU.
Keras dùng TensorFlow GPU độc lập với graph step và Adam slots rõ ràng; PyTorch dùng native GPU.
Resume giữ weights, m/v, iteration, history, best weights, early-stopping, lịch batch theo epoch.
Đặc biệt, moment tích chập được đổi đúng HWIO↔OIHW, không transpose bốn chiều bằng `.T`.

- TDD có RED evidence trước implementation. 16 test Torch và 1 Keras GPU đã PASS trước training.
- 3 test CPU request/API/saliency fixture PASS; thêm 5 audit/gate/fit test PASS khi resume.
  Một số test được chạy lặp để kiểm lỗi; đây không phải số test duy nhất của nghiệm thu cuối.
- Probe cả 3 dataset × 3 implementation đạt. Forward rtol1e-4/atol1e-5;
  gradient symmetric relative L2 từng tensor tối đa khoảng6,4e-6, dưới ngưỡng1e-3.
- Probe scratch batch16: IDRiD khoảng0,91–0,96 giây/update, EuroSAT/CIFAR khoảng0,06–0,07 giây.
  Đây là đo khả thi trước train, không phải benchmark quality/thời gian cuối.
- Keras/Torch probe chạy GPU thật; cảnh báo TensorFlow sm_120/PTX được giữ, không fallback.
- Dependency audit giữ spec Phase22, data Phase24, core Phase25 và 1.032 file Phase26 nguyên hash.

Lần probe Torch đầu gọi thừa đối số sample_weight vào parity API đã dừng trước update.
Giữ `attempts/preflight_torch_api_v1.json`; sửa cách gọi ở script probe chưa khai báo, không sửa core.
Gradient parity dùng loss không trọng số theo API core; weighted CE/update parity có test trainer riêng.

## Tiến độ huấn luyện / resume

Hàng đợi cũ dừng sau 8/36 selection và scratch IDRiD seed73 epoch7. Đã kiểm PID2242 không còn,
resume đúng optimizer/history từ immutable epoch007. Run đó tiếp tục epoch8–10 và hoàn tất;
không train lại tám run đã chọn. Sau đó toàn bộ 12 lượt IDRiD đã có selection, hàng đợi chuyển EuroSAT.

Ở scratch IDRiD seed73, `train_seconds` cộng thời gian đã lưu và đoạn chạy tiếp, loại khoảng
tạm dừng qua đêm. Timestamp của metric thuộc invocation hoàn tất. Peak RSS ghi nhận high-water
của process resume; không có số đo đã chốt từ process bị ngắt để khẳng định peak gộp cả hai process.
Không điền số ước lượng hoặc gọi đây là benchmark peak toàn bộ lượt liên tục. Metric chất lượng,
thứ tự batch và optimizer được khôi phục từ epoch7; không chọn lại cấu hình hay mở TEST.

Đoạn trên là lịch sử resume. Đến nghiệm thu, đủ **36 selection** đã hoàn tất, controller
`status=finished`, `pid=null`. Tất cả checkpoint đều qua CPU parity; không train lại selection cũ.
TEST được mở sau pretest proof PASS và khóa evaluator, không dùng TEST để chọn seed/cấu hình.

## Bản thảo và tooling bàn giao

- Theory: `report/sections/v3/ch03_cnn_theory.md`, cơ bản/dễ hiểu, shape/layer/hợp hàm/từng hàm,
  3 nguồn ảnh/link/size/mẫu/phân bố/giới hạn; không khẳng định độc lập bệnh nhân/địa lý.
- Vận hành: `docs/phase27_operations.md`.
- Audit: `scripts.verify_phase27`; chỉ recompute từ prediction đã lưu, không TEST forward.
- Demo CPU/API contract: `scripts.demo_phase27`; ghi actual backend NumPy/CPU khác training implementation.
- Export notebook/saliency: `scripts.export_phase27`; chỉ fixed TRAIN input, saliency không phải giải thích lâm sàng.
- Report producer: `scripts.summarize_phase27`; chỉ chạy khi đủ 3 seal TEST evaluated/count1.
- Runner tiếp tục/kiểm tra: `scripts/finish_phase27.ps1`, `scripts/check_phase27.ps1`.
  Finish mặc định dừng ở pretest; `-EvaluateTest` chỉ dùng khi đủ điều kiện mở TEST trong scope Phase27.
- Release: `scripts.release_phase27 --lock` chỉ sau visual QA, test, CPU demo, coverage và report thật.

## Nghiệm thu cuối

- **27 CNN đã train độc lập + 9 majority** trên 3 dataset, 3 seed 17/42/73. CNN có 7 lớp học được.
- Cả 3 seal TEST đều `evaluated`, `evaluation_count=1`, đủ 12 run mỗi dataset.
  Dự đoán mỗi run: IDRiD103, EuroSAT4.050, CIFAR-10 10.000; tổng **169.836 dòng**.
  Full auditor đối chiếu ID/nhãn/metric từ prediction đã lưu, không chạy TEST forward.
- **293 test duy nhất PASS, 0 skip**: 25 CNN Torch-env + 1 Keras GPU + 263 regression +
  1 preservation + 3 report/notebook. Demo XML 4 test là lượt chạy lặp trong 25 CNN test,
  không cộng trùng. Các XML probe/RED lịch sử cũng không cộng vào số nghiệm thu này.
- Coverage nhánh + dòng của 5 module CNN **93,1083%**, trước và sau TEST; statement 96,0894%.
  Giữ nguyên XML/coverage trước TEST đã được pretest proof pin hash.
- 72 run-summary row, 288 aggregate row, 75 per-class-recall row; mean ± sample SD 3 seed.
  Bảng JSON không chứa số synthetic. 7 hình PNG300dpi/SVG hiện hành đã xem trực tiếp.
- 3 notebook CPU chạy được, 9 checkpoint seed42 nạp qua demo và API contract;
  9 saliency chỉ trên fixed TRAIN. Registry trained riêng gồm 36 model, không sửa initialized Phase25.
- CPU demo ghi rõ actual backend NumPy/CPU dù checkpoint được train bằng scratch/Keras/PyTorch.
  Smoke tiền xử lý: 5 warmup/30 lần, ảnh PNG ở kích thước model; không phải ảnh IDRiD gốc.
- Ruff PASS; scan pattern secret giới hạn source/test không thấy pattern thông dụng.
  Không coi đây là kiểm toán toàn Git history hoặc dependency vulnerability.

### Kết quả TEST chính

| Dataset | Scratch macro-F1 | Keras macro-F1 | PyTorch macro-F1 | Majority |
|---|---:|---:|---:|---:|
| IDRiD | 0,1804 ± 0,0878 | 0,1579 ± 0,0570 | 0,1454 ± 0,0457 | 0,0948 |
| EuroSAT | 0,6738 ± 0,0157 | 0,6902 ± 0,0215 | 0,6983 ± 0,0472 | 0,0200 |
| CIFAR-10 | 0,5199 ± 0,0137 | 0,5086 ± 0,0448 | 0,5201 ± 0,0111 | 0,0182 |

IDRiD chất lượng thấp, nhiều lớp recall bằng 0 và biến động seed lớn. Không dùng chẩn đoán;
không bỏ hạn chế giảm ảnh xuống128×128, méo tỉ lệ, thiếu patient key và dữ liệu nhỏ/mất cân bằng.
EuroSAT thiếu spatial key đã xác minh; không khẳng định độc lập địa lý. Các mô hình dùng matched
train nhỏ, không pretrained/augmentation, nên không đại diện chất lượng tối đa của dataset.
Chênh lệch CPU/GPU, graph/eager và số epoch khiến timing không thể dùng để kết luận framework
nào luôn tốt hơn. Ba seed không đủ để khẳng định ý nghĩa thống kê.

### Revision trình bày r2 — không đổi kết quả

Visual QA phát hiện số đếm bị chồng ở confusion matrix 10 lớp của bản đầu. Giữ nguyên
`report_generation.json`, bản thảo `ch03_cnn.md` và 7 hình gốc, tạo revision hậu xử lý mới:

- Bản thảo **hiện hành**: `report/sections/v3/ch03_cnn_r2.md`.
- Pointer: `artifacts/manifests/phase27/active_report.json`; metadata:
  `revisions/r2/report_generation.json`. Chỉ sửa 3 bố cục hình, thang màu đếm chung và lời chú thích.
- Với 10 lớp, không in từng số vào ô; ma trận số đầy đủ vẫn trong `runs/<run_id>/test_details.json`.
  Bảng recall và metric/checkpoint/prediction giữ nguyên hash. 4 hình khác dùng nguyên bản.
- TDD RED `attempts/report_r2_red.xml`; GREEN 3 test tại `revisions/r2/report-tests.xml`.
  `visual_qa.json` ghi đúng 7 PNG hiện hành. Không sửa source train/evaluator/auditor đã khóa.

Bằng chứng: `pretest_verification.json`, `verification.json`, `acceptance_verification.json`,
`final_coverage.json`, các XML nghiệm thu, `trained_contract_registry.json`, `demo/export.json`,
`cpu_smoke.json`, `visual_qa.json` và `experiment_lock.json` trong manifest Phase27.
Public wrapper `scripts/check_phase27.ps1` chỉ kiểm hash/audit sau release, không chạy lại TEST.

Giữ bốn warning sklearn V2 đã biết và TF sm_120/PTX; không đổi backend hay dependency.
Spec31 Phase22, data294 Phase24, core219 Phase25 và 1.032 file Phase26 vẫn nguyên hash.
Preservation test giữ 11.357 raw file, V2 DOCX và Ch5 config/metric/10 TEST prediction nguyên byte;
Ch5 run_count=1. Điều chỉnh augmentation trong câu mô tả plan không được vượt preprocessing
Phase24 đã khóa: track matched hiện hành **augmentation=none**, không tự bổ sung sau khai báo.

Ch2/Ch5 TEST không mở lại. Raw, V2 và môi trường không bị sửa, không commit/reset/cleanup.
Giai đoạn tiếp theo sau khi Phase27 COMPLETE mới là Phase28, RNN validation-only.
