# Phase 24 — EDA, chia tập và kiểm tra rò rỉ dữ liệu

Ngày 17/10/2026. Trạng thái: **COMPLETE**.
Phase này không huấn luyện, tuning hay đánh giá mô hình trên TEST. Không tạo DOCX V3 hoặc sửa UI/API.

## Kết quả và đường dẫn

- 18 thẻ dữ liệu: `report/references/dataset_cards/v3_eda/`.
- Catalog cho code, báo cáo và UI: `data/catalog_v3.json`. Registry nguồn Phase23 giữ nguyên.
- EDA, mẫu input/output, profile missing/outlier và index: `artifacts/manifests/phase24/<dataset>/`.
- Bảng CSV được sinh từ EDA: `artifacts/manifests/phase24/<dataset>/tables/`.
- Split/preprocessing: `data/splits/v3/<dataset>/`,
  `artifacts/manifests/phase24/<dataset>/preprocessing.json`.
- Hình PNG 300 dpi/SVG: `artifacts/figures/phase24/`.
- Ước lượng bộ nhớ: `artifacts/manifests/phase24/memory_plan.json`.

Các scope được tách rõ: Ch1 chỉ case study lịch sử; Ch2–4 có dữ liệu/split mới;
Ch5 kế thừa baseline chỉ đọc; ba thẻ Ch6 là view từ parent, **chưa phải benchmark agent**.
Task, gold answer và task-family split Ch6 thuộc Phase31. Không nhân bản raw.

## Ma trận dữ liệu dùng cho mô hình

Các số dưới đây là số ID thực đo, không phải kết quả huấn luyện.
Với chuỗi thời gian, số lượng là window hợp lệ, không phải số dòng raw.

| Dataset | Train đầy đủ | Validation | TEST | Matched train |
|---|---:|---:|---:|---:|
| CDC diabetes | 177.505 | 38.053 | 38.122 | 20.000 |
| Ames Housing | 2.051 | 439 | 440 | 2.051 |
| Bank Marketing | 31.648 | 6.781 | 6.782 | 10.000 |
| IDRiD | 348 | 64 | 103 | 348 |
| EuroSAT | 18.900 | 4.050 | 4.050 | 3.000 |
| CIFAR-10 | 45.000 | 5.000 | 10.000 | 5.000 |
| Gold monthly | 531 | 115 | 116 | 531 |
| BIS nominal indices | 2.504 | 588 | 568 | 2.504 |
| Household power | 23.797 | 5.033 | 4.911 | 12.000 |

IDRiD còn **1 ảnh official train trong quarantine** do trùng pixel với TEST.
348 + 64 + 103 + 1 = 516. Không xóa/chuyển ảnh trong official TEST, không sửa raw.
Giữ full validation/TEST cho cả ba implementation. Subset được chọn bằng SHA-256/seed42
theo strata đã khóa, không chọn theo metric. Seed huấn luyện 17/42/73 không thay split/subset.

## Những phát hiện cần đưa vào tiểu luận

- **CDC:** 25.772 dòng trùng 21 feature, 1.566 nhóm feature có nhãn khác nhau. Gom nhóm trước
  split, giữ nhãn nguồn, không dùng majority vote để sửa ground truth. Majority chỉ dùng chọn stratum
  của nhóm. Không có patient ID xác minh, không tuyên bố độc lập bệnh nhân hay nhân quả.
- **Ames:** loại PID/Order khỏi feature, nhưng dùng PID cùng liên kết duplicate để chia nhóm.
  Decile giá chỉ phục vụ stratification. Giá bán USD, preprocessing/target scaler chỉ fit matched train.
  Missing ở thuộc tính tiện ích có thể là structural absence, không tự coi mọi NA là số 0.
- **Bank:** bỏ `duration` cho bài toán dự đoán trước cuộc gọi; 16 dòng trùng feature được gom nhóm.
  Giữ `unknown` như mức danh mục nguồn. Không có mã khách để chứng minh độc lập theo khách hàng.
- **IDRiD:** 6 dòng ảnh dư do trùng pixel, trong đó 3 nhóm pixel có nhãn khác nhau;
  giữ nhãn nguồn, không tự sửa grade. Quarantine 1 ảnh train trùng TEST. Không có patient key
  xác minh. Track so sánh 128×128 có thể mất chi tiết tổn thương. Không đưa ra chẩn đoán.
- **EuroSAT:** RGB 64×64 gốc, so sánh ở 32×32. Chỉ bảo đảm nhóm pixel, không tuyên bố
  độc lập địa lý khi không có tọa độ/group không gian xác minh.
- **CIFAR:** giữ official 50.000 train/10.000 test; validation là 10% official train.
  Tên lớp lấy từ metadata TAR: 10 tên duy nhất và một dòng trống cuối; chỉ bỏ dòng trắng khi đọc,
  không sửa byte archive hoặc thứ tự lớp. Không dùng pickle.
- **Gold:** 801 tháng từ 1960-01 đến 2026-09; 24 bước context, horizon 1/3/6 tháng.
  Gold tại origin, ba commodity giải thích trễ một tháng. Snapshot hồi tố/revised, không phải
  backtest có vintage thật và không phải khuyến nghị đầu tư.
- **BIS:** chỉ Q/N/628, chỉ số danh nghĩa 2010=100. 49 quốc gia đạt >=80 quan sát,
  loại aggregate và 8 chuỗi thiếu coverage. Lịch sử chung bắt đầu 2002Q1 theo quy tắc độ phủ
  >=80% quốc gia, không theo giá trị hay metric TEST. 4.689 dòng canonical, 3.660 window hợp lệ.
  Không gộp nominal/real/YoY và không nhầm chỉ số này với giá USD của Ames.
- **Power:** 2.075.259 dòng phút thành 34.589 mốc giờ. Giờ phải có >=45 phút quan sát;
  438 nhãn giờ thiếu không được điền. Input ffill tối đa 6 giờ, sau đó dùng imputer train-fit và
  cờ missing. Đích là kW trung bình giờ, không phải kWh. Đồ thị dùng trung bình 7 ngày chỉ để vẽ.
- **Ch5:** giữ split/metric/TEST đã khóa. MedQuAD 247 query khác 47.441 QAPair upstream.
  Ví dụ MedQuAD là ID -> trích đoạn retrieval corpus công khai, không gán train/test vì bundle
  không có split, không phải QA gold mới. FinQA chỉ lấy ví dụ từ official train; không mở
  TEST/private_test. Page-group overlap cũ bằng 0 nhưng report-key overlap khác 0 vẫn được công khai.
  Wikidata 10 entity/2.056 claim chỉ là KG hỗ trợ, không bịa benchmark QA thứ ba.

## Split, preprocessing và thời gian

Tabular/EuroSAT chia 70/15/15 xấp xỉ theo dòng sau khi gom nhóm. IDRiD giữ official TEST;
validation từ official train. Image identity xét cả pixel gốc và sau resize.
Các bảo đảm theo identity/hash không thay cho bảo đảm patient/client/geographic independence.

Tabular fit medians, mean/std, category vocabulary, target scaler và class weight trên
matched train. Unknown category dùng all-zero one-hot; constant/all-missing numeric có fallback
được ghi rõ. Outlier dùng hàng rào IQR từ train, chỉ là cờ mô tả, không tự xóa dòng.
Ảnh dùng Pillow RGB/BILINEAR, float32/255 chung, không augmentation riêng cho từng framework.

Time series chia theo target-time toàn cục. Mọi horizon của window phải ở cùng partition;
context có thể đi trước boundary nhưng không chứa tương lai. Scaler chính fit prefix train,
không phải validation/test. Mỗi nguồn có ba expanding rolling folds; mỗi fold có scaler riêng,
ID train/validation và matched subset riêng, không chạm final TEST. Cùng series qua các tập là
dự báo series đã thấy, không phải holdout quốc gia chưa thấy.

Gold/BIS dùng mốc lịch tháng/quý. Giờ Power giữ civil-clock theo nguồn, chưa tái dựng timezone/DST.
Offset `+00:00` trong split schema là tọa độ lịch chuẩn hóa để so thứ tự, **không khẳng định**
thời điểm đo gốc thật sự theo UTC. Quy ước này có trong audit và thẻ dữ liệu.

`data_holdout.json` chỉ khóa dữ liệu, **không cấp quyền chạy TEST**. Sau này phải khóa thêm
config/code/evaluator/approved runs. RNN và LSTM chỉ mở TEST chung ở Phase29.
Ch5 TEST giữ `run_count=1`, không chạy evaluator để tạo lại báo cáo.

## Bộ nhớ và tái lập

Chỉ lưu index/range, không nhân bản tensor của mọi window. Stream/decode ảnh theo nhu cầu.
`memory_plan.json` ghi byte input float32, canonical frame và chi phí nếu materialize mọi window.
Đây không phải peak VRAM huấn luyện. Probe activation/optimizer/peak RAM–VRAM thuộc Phase25;
không tuyên bố đã đo GPU từ EDA chạy CPU.

Ba cache canonical series ở `data/processed/v3/` được ignore. Nếu có phải đúng hash receipt;
nếu thiếu verifier dựng frame từ raw và stable sort, không fit lại preprocessing. Không cần commit cache.

## Lệnh vận hành

Tại `C:\DATA\assign`, dùng runtime WSL đã khóa, không Python Windows:

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.verify_phase22
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.verify_phase23
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.verify_phase24
```

`scripts.prepare_phase24` sinh artifact trước khóa; khi đã có `data_lock.json`, gọi lại chỉ
kiểm chứng/giữ nguyên. `scripts.export_phase24_tables` cũng bảo vệ phiên bản đã khóa.
Không xóa/ghi đè khóa để chấp nhận số liệu đổi; thay đổi dữ liệu cần revision có biên bản.
`scripts.phase24_reproducibility` chứng minh hash các ID/subset/state/cache trước và sau QA.

## Nghiệm thu đã đạt

- **142 data test + 121 regression test PASS**, tổng **263**, không skip. Bốn warning sklearn
  V2 1.9.1/1.9.0 vẫn công khai, không sửa checkpoint cũ để bỏ warning.
- Coverage unit và pipeline thật: **97,58%** (làm tròn 98%); cả sáu module đều >=95%.
  Lint/format **14 file Python PASS**. Scan pattern secret giới hạn 9 file source không phát hiện
  pattern private key/token phổ biến; không tuyên bố đây là audit toàn Git history.
- **18 card, 9 split contracts, 9 rolling folds, 55 bảng CSV, 19 hình** (38 file PNG/SVG).
  Đã xem lại cả bốn contact sheets sau tái sinh, kiểm nhãn/đơn vị/boundary/ảnh mẫu và clipping.
- Verifier độc lập PASS: đối chiếu source/cache, index/timestamp/horizon, group overlap,
  fit IDs và thống kê preprocessing, class weights, matched subset, CSV so với EDA và catalog.
  Kiểm **38.163 window**; không có target-time overlap giữa train/validation/TEST.
- **81 artifact quyết định dữ liệu** giữ nguyên hash qua tái sinh/QA, gồm ID/subset, fitted state
  và canonical cache. Không đổi split hay chọn lọc lại để làm đẹp kết quả.
- Khóa **294 artifact/code/test file** tại `artifacts/manifests/phase24/data_lock.json`, SHA-256
  `5ae1091892262b0b2e52a570e19963005da6724a736447bd11b4e9be3b60e37e`.
  Đã gọi lại producer/exporter sau khóa: PASS, chỉ kiểm chứng, không ghi đè dữ liệu/khóa.
- Giữ nguyên 31 file spec Phase22, 62 provenance file Phase23 và snapshot metadata cũ 58 file;
  environment lock, raw Ch5, V2 và TEST predictions không đổi. Ch5 `run_count=1`.
- Evidence: `verification.json`, `data-tests.xml`, `regression-tests.xml`, `data_coverage.json`,
  `visual_qa.json`, `reproducibility.json`, `data_lock.json`, `checkpoint.json` trong manifest Phase24.

## Bàn giao kỹ thuật cho Phase25

Phase24 khóa thống kê **theo tên biến**, vocab và schema đầu vào, không lưu tensor dense để train.
Adapter tensor dùng cho mô hình vẫn thuộc Phase25. Phải xuất danh sách `output_feature_names`
có thứ tự rõ ràng và test trước/sau serialize–load JSON. Không dùng thứ tự key của object
`numeric`/`categorical` làm hợp đồng thứ tự feature: JSON được ghi với `sort_keys=True`, còn helper
`transform_tabular` tham chiếu EDA đang duyệt dictionary theo insertion order. Thứ tự tensor khi
fit trong RAM có thể khác khi đọc lại contract nếu dùng trực tiếp helper này.
Các số đếm, named statistics, raw/cache, sample và split Phase24 không bị ảnh hưởng: EDA chỉ dùng
dense transform để kiểm tra finite/window eligibility, chưa train hay lưu model input tensor.
Phase25 phải tạo adapter mới có canonical feature order (và HWC/NCHW/label mapping) trước model;
không sửa/format lại module dữ liệu đã khóa nếu chưa có revision được ghi nhận.

Phase hợp lý tiếp theo là **25 — lõi dùng chung, model contract và hợp hàm**.
Không tự bắt đầu Phase25 hoặc huấn luyện trong Phase24.
