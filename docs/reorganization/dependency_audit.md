# Quyết định nguồn và phụ thuộc cần giữ

## A01/A02

A01 có hai bản107cell: bản `be8442eff` có46codecell/output; bản nộp lại ở `0c27b1d2f`
có48codecell/output, bổ sung phân tích lựa chọn đặc trưng. Giữ bản sau làm notebook chính,
bản trước làm lịch sử. So diff thư mục artifacts giữa hai mốc cho thấy chỉ thêm nhóm customer;
các model diabetes/house của A01 không đổi. A01 dùng backend/web tại mốc riêng, A02 dùng bản
thêm customer. Giữ cả Neo4j scripts và source mobile làm tham chiếu, không ép chạy Expo.

Pima của A01/A02 khác CDC balanced của A03 và CDC3 lớp A05. Tên `diabetes.csv` giống nhau
không cho phép gộp dữ liệu. Customer behavior A02/A03 cũng không được gọi nhầm là Olist A04.

## A03/A04

Commit `d68985ea4` chỉ sửa3header trong web/mobile, không thay model/notebook so với
`8b3ba0254`; dùng commit sau để bảo toàn tên/nhãn đúng bài. `pipeline/` có3notebook và
model NumPy/preprocessor/metadata/comparison/demo sample đi kèm.

A04 `pipeline04/` có5notebook. Ba notebook tabular đọc notebook/metadata/comparison của
A03 để đối chiếu, nên staging A04 kèm27file `pipeline/` từ đúng mốc A04. Sau migration,
chúng là dependency reference được resolve rõ, không được lỡ chạy notebook A03 để tạo lại số.
Các tập tabular A04 là CDC2021, King County và Olist prepared, khác snapshot A03.

MNIST có archive Git. CIFAR10 Python archive không có trong cây được phục hồi và cũng
không thấy trong index tài nguyên local hoặc snapshotV2 (đối chiếu inventory). V3 có binary
archive, do đó Phase2 phải tải đúng Python archive từ URL notebook hoặc tạo adapter đọc binary
với parity pixel/nhãn/ID xác nhận. Không đổi đuôi/tên file để làm loader tưởng là pickle.

## A05/A06

Cây A05 tổng53.080file; phần lớn là dataset, không phải venv. Payload được chọn giữ27.000ảnh
EuroSAT và toàn bộ7.390rawPet images; annotation text quy định7.349official sample. Các mask
segmentation/XML bounding boxes và AppleDouble được kê loại trừ khỏi payload phân loại;
nguồn Git còn nguyên. Giữ đủ12checkpoint Keras, model source, split và44row hyperparameter
theo README gốc. Không chạy lại tuning. Dataset tabular dùng Conv1D với giới hạn đã giải thích.

A06 có README ghi trạng thái khởi tạo cũ, nhưng `CURRENT_STATE.md` cuối và artifact thực
xác nhận8notebook,4checkpoint framework/task,6processedNPZ,scalers,metrics/predictions và
báo cáo đã xong. Inventory ưu tiên bằng chứng thực, không suy ra chưa train từ README cũ.
Source config và notebook có root discovery/Anaconda path cần migration revision.

## Tiểu luận1–3

Tiểu luận1 lấy `e7cf49bce` (bản sau `tieu-luan-1`) để giữ sửa CRLF artifact hash.
Đây là bản4chương + phần triển khai lịch sử, không phải DOCX5chương baselineV2.
Giữ `term_paper/` models/preprocessors/manifests/metrics/predictions/source/report và backend/web.
Ba notebook chính của tiểu luận1 đọc kết quả; source training nằm riêng.

Raw references của tiểu luận1 trỏ các assignment cũ; dataset cards có kích cỡ/SHA đã ghi trên
Windows. Git có thể lưu CSV dưới LF, khác CRLF của snapshot khi đo. Catalog lưu cả SHA Git blob
và SHA của CRLF-equivalent CSV để đối chiếu. Chỉ khi khớp hash kỳ vọng mới cho phép materialize
đúng representation ở Phase2; không tùy tiện sửa seal/hash trong tài liệu cũ.

Tiểu luận3 là baseline hiện tại; mapping mới chỉ là đề xuất. Giữ alias namespace `term_paper`
cho index/joblib và tách serving bundle khỏi môi trường GPU. Việc chuyển `apps/web`,
`apps/api`, data/model/registry và render script phải cùng revision; chỉ đổi Root Directory
trên Render là không đủ nếu payload ZIP/source fingerprint chưa đồng bộ.

Tiểu luận2 không có commit riêng, sẽ dẫn xuất từ tiểu luận3: giữ Ch1–5, bỏ Ch6 gồm route/menu,
catalog/family, registry/payload serving, notebook và taskset. Ch5 KG–RAG không bị bỏ. Shared
utilities chỉ giữ phần cần Ch1–5; không xóa nội dung agent của tiểu luận3/agent01/agent02.

## Hai bài agent

Hai web-demo chưa commit đã được sao lưu toàn bộ, gồm file ignored và metadata Git lồng của
Agent01. Payload hoạt động phải bỏ lớp `dist/` và metadata lồng, nhưng backup vẫn giữ nguyên.
Notebook tải riêng của AG02 không phải bundle tự chứa; cần data/input/source đi kèm.

`agent02_assignment` vừa là tên folder vừa là namespace được import; đổi folder thành agent02
cần shim/versioned adapter. Các khóa AG02 dùng đường dẫn tương đối và tham chiếu parent assets
V3; phải giữ resolver old-logical-path→new-physical-path trước khi dọn tên cũ.

## Chính sách bảo toàn sau migration

`migration_map.json` là bản đồ đề xuất cho file thực, chưa được áp dụng. File giữ nguyên byte
có thể di chuyển nhưng code đổi đường dẫn phải có bản gốc trong provenance và revision mới.
Không sửa code/auditor/lock đã pin để xóa lỗi load. Scientific TEST đã seal chỉ đọc prediction;
runtime smoke dùng fixture/TRAIN/demo input và không được cộng thành kết quả nghiên cứu mới.
