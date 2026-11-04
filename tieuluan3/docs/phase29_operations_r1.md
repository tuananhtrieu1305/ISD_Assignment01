# Vận hành/bàn giao Phase29 sau revision TEST schema r1

Trạng thái thật: `artifacts/manifests/phase29/checkpoint.json` và
`revisions/test_schema_r1/active_controller.json`. Chỉ COMPLETE sau experiment_lock và
verify-lock PASS. Không dùng các mốc tiến độ lịch sử trong AGENTS làm trạng thái hiện tại.

## Runtime

Dùng wrapper với **`-Distribution Ubuntu`**, runtime Linux
`/home/tuananh/.local/share/ai-term-paper-v3/`, hai venv khóa riêng. Python3.11.17,
Torch2.14.1+cu130 và Keras3.15.1/TensorFlow2.21.0, không fallback hoặc Python Windows.
Recovery r1 có4 process GPU/CPU smoke và shared-package parity PASS; metadata cũ giữ hash.
Không gọi bootstrap/doctor cũ để ghi đè environment/probe đã khóa. GPU CLI WSL là
`/usr/lib/wsl/lib/nvidia-smi`. Lệnh raw Python không thay thế runner có CUDA library paths.

## Không train hoặc chạy lại TEST

LSTM108 selection (27main+81rolling) đã hoàn tất; RNN132 selection Phase28 giữ nguyên.
TEST dùng60 main member:27RNN+27LSTM+6baseline, không chọn seed/rolling bằng TEST.

Batch TEST gốc có Gold/BIS evaluated/count1 và Power failed_sealed/count1. Orphan
Power/RNN/PyTorch/s17 đã lưu4.911 output rồi lỗi schema validation-only của Phase28.
Revision r1 do người dùng đồng ý giữ seal lỗi/43 claim gốc/42 result, finalize orphan từ
saved outputs và chỉ tiếp tục17 run chưa claim. Không dựng lại TEST cache, retrain, update
weights hoặc dự đoán lại orphan. Original orphan train/RAM/VRAM vẫn null; costn2/qualityn3.

Declaration revision pin8 FILES,21 unit test và coverage schema/journal93,4959%:
`artifacts/manifests/phase29/revisions/test_schema_r1/declaration.json`.
Không sửa/format các file đã ref, không dùng controller cũ để tiếp tục hoặc reset seal.
Nếu có consumed claim chưa có result, giữ log/output và tìm nguyên nhân, không tự retry.

Khi controller mới finished/PID=null và gate revision evaluated, audit bằng
`scripts.verify_phase29_test_r1`. Nó chỉ đọc cached labels và prediction đã lưu,
không tạo model hoặc TEST forward. Auditor cũ không biết continuation, phải giữ nguyên
như lịch sử; không sửa nó để che seal failed. Unified audit ghi result_refs cho đủ60 member,
111.900 prediction row, mỗi row3horizon. Original seal và effective completion ghi riêng.

## Kiểm sau phát hành — chỉ đọc

```powershell
.\scripts\check_phase29.ps1 -Distribution Ubuntu
```

Wrapper gọi `scripts.release_phase29 --verify-only`, chỉ so hash mọi file trong lock.
Không chạy lại train, native GPU probe, TEST worker, coverage writer hoặc producer vào
artifact đã khóa. Kiểm luận văn đọc manuscript/statistics/active_report và saved predictions.
Đổi trình bày sau phát hành cũng cần revision mới giữ bản cũ.

## Demo CPU và notebook

```powershell
.\scripts\run_experiment.ps1 -Distribution Ubuntu -Framework torch -Module scripts.demo_phase29 -ModuleArguments @('--dataset','ch4_gold_pink_sheet','--family','lstm')
```

Đổi family thành `rnn`, dataset thành BIS/Household Power theo DATASETS đã khai báo.
Ba checkpoint mỗi họ được train độc lập nhưng actual serving là NumPy CPU portable,
không phải native TensorFlow/PyTorch đang chạy GPU. Default seed42 cố định; không chọn seed
tốt nhất theo TEST. Notebook ở `experiments/notebooks/v3/ch04_rnn_lstm/`, cùng engineered
TRAIN input/canonical feature order, không gửi dữ liệu ra ngoài hoặc gọi API trả phí.

Notebook exporter thực thi các code cell do chính generator tạo qua Python/runpy và lưu
log; đó là smoke của nội dung code, không tự gọi là kiểm thử Jupyter UI/kernel picker.
Registry trained/evaluated riêng ở `trained_registry.json`, không thay initialized registry
Phase25. Các helper train có kiểm frozen Git HEAD; loader API tương lai cần dùng registry/
artifact refs, không sửa khóa cũ khi chuyển deployment sang commit mới.

## Report và release

Bảng/hình sinh từ saved metric/prediction; tách family/split/fold/horizon. Mean và sampleSD
qua3seed; baseline n1 không dựng SD0, null cost không thay bằng recovery peak hoặc0.
Chi phí lấy từ validation training record; bản sao trong TEST không phải lượt train thứ hai.
Timing native dùng5warmup/30repeat TRAIN-input, không benchmark TEST hoặc HTTP. Runtime đã
khôi phục giữa đợt và có unit test nhẹ cùng queue, không khẳng định benchmark máy cô lập.

Manuscript mới: `report/sections/v3/ch04_rnn_lstm.md`; RNN Phase28 giữ nguyên byte.
Nguồn mapping/shape/hợp hàm từ contracts; lý thuyết cơ bản, công thức tối thiểu. Deployment
là mục ngắn cuối chương. Phải xem đủ9 PNG trước visual_qa PASS; chưa build/render DOCX ở đây.
API/UI Phase32–33, tích hợp DOCX Phase34–35. Tiếp theo Phase30 chỉ khi người dùng yêu cầu.
