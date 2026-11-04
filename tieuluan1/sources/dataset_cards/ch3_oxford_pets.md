# Dataset card — Oxford-IIIT Pet

## Nhận dạng và nguồn

- Dataset ID: `ch3_oxford_pets`.
- Chương/bài toán: Chương 3, fine-grained 37-breed image classification.
- Nguồn chính thức: <https://robots.ox.ac.uk/~vgg/data/pets/>.
- Paper “Cats and Dogs”: <https://www.robots.ox.ac.uk/~vgg/publications/2012/parkhi12a/>, citation key `parkhi2012catsdogs`.
- Truy cập: 2026-10-05.
- License: CC BY-SA 4.0 theo trang Oxford; copyright ảnh vẫn thuộc chủ sở hữu gốc.
- Local: `A05/datasets/oxford_pets/`; 821,045,236 bytes; manifest SHA-256 `1178e8498c2a966e1d7c667e85d41b9caebd478179fb380abaa3da4d1ee6bf88`.

## Kích thước và schema

- 7,349 ảnh có annotation chính thức, 37 giống: 12 giống mèo và 25 giống chó.
- Mỗi ảnh có breed/species label; dataset còn có head ROI và pixel-level trimap.
- Official trainval = 3,680; official TEST = 3,669. A05 chia trainval thành TRAIN 2,944 và VAL 736 bằng stratification seed 42.
- Local tree có 25,864 files vì gồm ảnh, annotation, trimap và metadata; không được hiểu là 25,864 samples.

## Phân bố và mẫu

- Gần cân bằng: đa số lớp có 200 ảnh; min = 184, max = 200. Các lớp thiếu đáng kể gồm label 8 (184), 12 (190), 35 (189).
- Mẫu: `Abyssinian_100.jpg` → breed `Abyssinian`, species cat; annotation tương ứng cung cấp class ID/species ID/breed ID.
- DOCX sẽ dùng một grid ảnh thật đại diện và bảng class count rút gọn; không dùng ảnh trimap như input classification nếu protocol chỉ phân loại RGB.

## Kiểm soát dữ liệu

- Dùng annotation lists làm nguồn sample truth, không quét toàn thư mục ảnh để tự gán split.
- Local có 41 raw image files không được tham chiếu trong official trainval/test; loại khỏi mọi bảng và training.
- Official TEST được giữ nguyên; chỉ trainval được chia TRAIN/VAL.

## Nhận xét và giới hạn

- Fine-grained breeds có khác biệt thị giác nhỏ, trong khi pose, scale và lighting biến thiên lớn; accuracy ngẫu nhiên cho 37 lớp xấp xỉ 2.7%.
- Ảnh được thu từ các website công cộng; background/source artifacts có thể tạo shortcut.
- Vì license share-alike và copyright gốc, khi phát hành report phải ghi attribution; không đóng gói lại toàn bộ ảnh.

## Bằng chứng local

- Notebook: `A05/notebooks/03_Oxford_Pets_CNN.ipynb`.
- Annotation: `A05/datasets/oxford_pets/annotations/{trainval,test,list}.txt`.
- Splits: `A05/results/splits/oxford_pets_{train,val,test}.csv`.
