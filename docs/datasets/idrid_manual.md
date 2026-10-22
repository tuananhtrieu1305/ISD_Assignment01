# IDRiD — ZIP gốc và biên bản nhập thủ công

Trạng thái ngày 17/10/2026: **READY cho nguồn dữ liệu Phase 23**. Chưa EDA, chia validation
hay huấn luyện. Bạn đã tải đúng **B. Disease Grading.zip**; gói này có đủ ảnh, CSV nhãn và
giấy phép, không cần tải CSV riêng, A. Segmentation hay C. Localization.

## File đang giữ

`C:\DATA\assign\data\raw\ch3\idrid\manual\B_Disease_Grading.zip`

- 212.405.123 byte; SHA-256:
  `8a9f4752b35d74cc35ff48b21ad44f295a6f800110ec218fc2d1c264803e4d8c`.
- Tên ngoài ban đầu `B. Disease Grading.zip` được chuẩn hóa để phù hợp quy tắc đường dẫn
  Phase 22 đã khóa. Byte ZIP và mọi tên/nội dung bên trong giữ nguyên; không giải nén trùng.
- 516 ảnh RGB, kích thước gốc 4288×2848: 413 train, 103 test theo official split.
- Hai CSV nhãn nằm trong `B. Disease Grading/2. Groundtruths/`; DR grade hợp lệ 0–4,
  khớp một-một với toàn bộ ảnh. Không sửa các cột trống cuối CSV nguồn.
- Train và test có basename trùng nhau. ID nội bộ dùng `train/IDRiD_001` và
  `test/IDRiD_001`, không gộp theo basename và không đổi tên ảnh trong ZIP.
- `LICENSE.txt` xác nhận **CC BY 4.0**, đi cùng toàn văn `CC-BY-4.0.txt`.
  Giữ attribution/citation/license và nêu các bước biến đổi khi dùng trong báo cáo;
  demo không có tuyên bố dùng chẩn đoán lâm sàng.

Nguồn gốc: [IEEE DataPort IDRiD](https://ieee-dataport.org/open-access/indian-diabetic-retinopathy-image-dataset-idrid),
DOI: `10.21227/H25W98`. SHA-256 trên là hash của file local đã nhận, không phải tuyên bố
đã đối chiếu checksum do nhà xuất bản công bố.

## Bằng chứng cập nhật

- Manifest: `artifacts/manifests/datasets/ch3_idrid.json`.
- Thẻ nguồn: `report/references/dataset_cards/v3/ch3_idrid.md`.
- Thư mục phiên bản: `artifacts/manifests/phase23/updates/idrid_20261017_8a9f4752b35d/`.
  Có receipt tên gốc, receipt chuẩn hóa tên ngoài, chỉ mục ảnh/nhãn và khóa provenance mới.
- Danh sách hash mọi thành viên ZIP: `artifacts/manifests/datasets/ch3_idrid/archive_members.jsonl`.
- Giữ nguyên khóa Phase 23 ban đầu và snapshot metadata cũ; không sao chép raw vào snapshot.

Kiểm tra lại từ PowerShell ở `C:\DATA\assign` bằng runtime WSL đã khóa:

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.verify_idrid_manual --require-ready
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.verify_phase23 --deep
```

`scripts.update_phase23_idrid` là bước nhập có phiên bản, đã chạy; gọi lại chỉ kiểm tra và
giữ nguyên phiên bản hiện hành. Builder cũng chỉ kiểm tra/giữ registry khi có khóa phiên bản.
Raw được ignore, không đưa lên Git/Render. Không cần tải hay giải nén thêm file nào cho IDRiD.

Phase 24 sẽ làm mẫu input/output, phân bố, audit trùng lặp/leakage và validation split trên
official train. Official test giữ riêng; không dùng để chọn mô hình/tuning. Phase 27 mới
nghiệm thu ma trận CNN Scratch/Keras/PyTorch trên IDRiD, EuroSAT và CIFAR-10.
