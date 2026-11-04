# Báo cáo Assignment 05: So sánh các kiến trúc CNN

Báo cáo này tổng hợp các kết quả đã được thực thi và lưu trong `A05/results/`. Không có mô hình nào được retrain khi tạo báo cáo. Các số liệu đến từ metrics CSV, hyperparameter CSV, audit files, và các notebook đã chạy.

## I. Các khái niệm cơ bản của CNN

CNN có thể được nhìn như một composition của nhiều hàm biến đổi dữ liệu. Với một pipeline phân loại ảnh đơn giản, luồng khái niệm có thể viết là:

`Softmax ∘ Dense ∘ Pool ∘ ReLU ∘ Conv`

Trong đó `Conv` dùng một kernel/filter nhỏ trượt qua input để tạo feature map. Mỗi kernel học một kiểu mẫu cục bộ, ví dụ cạnh, texture, vùng sáng/tối hoặc cấu trúc nhỏ. `ReLU` đưa phi tuyến vào mạng qua công thức `ReLU(z) = max(0, z)`, giúp nhiều tầng convolution không chỉ tương đương một biến đổi tuyến tính lớn.

`Pooling` giảm kích thước không gian của feature map và làm biểu diễn bớt nhạy với dịch chuyển nhỏ. Sau phần trích xuất đặc trưng, `Flatten` hoặc `Global Average Pooling` chuyển feature map thành biểu diễn phù hợp cho phân loại. `Dense` kết hợp các đặc trưng đã học, còn `Softmax` biến logits thành phân phối xác suất trên các lớp. Khi dùng nhãn nguyên, loss phù hợp là Sparse Categorical Cross-Entropy; về ý tưởng, Cross-Entropy phạt mạnh dự đoán xác suất thấp cho lớp đúng.

## II. Sự phát triển của các mô hình CNN

| Family | Ý tưởng chính | Độ sâu convolution | Residual | Ý nghĩa thay đổi |
| --- | --- | --- | --- | --- |
| Basic CNN | baseline convolution đơn giản | 2 Conv2D hoặc 2 Conv1D | không | mốc so sánh gọn nhất |
| AlexNet-inspired | tăng capacity bằng nhiều convolution stage hơn | 4 convolution layer | không | thêm độ sâu nhưng không dùng dense head lịch sử quá lớn |
| VGG-inspired | lặp block kernel nhỏ | 6 convolution layer | không | kiểm tra lợi ích của block có cấu trúc hệ thống |
| ResNet-inspired | residual learning với y = F(x) + shortcut(x) | stem + residual blocks | có | giúp gradient đi qua shortcut, dùng projection khi channel khác |

Basic CNN đóng vai trò baseline nhỏ để kiểm tra liệu convolution đơn giản đã học được tín hiệu hay chưa. AlexNet-inspired tăng số tầng convolution và capacity nhưng được scale nhỏ cho CPU, không tái tạo các dense layer rất lớn của AlexNet lịch sử. VGG-inspired giữ ý tưởng lặp các block kernel nhỏ để tạo cấu trúc có hệ thống. ResNet-inspired thêm residual block, trong đó:

`y = F(x) + x`

Nếu số channel khác nhau, shortcut dùng projection `1x1` convolution để phép cộng hợp lệ. Thay đổi này có ý nghĩa kiến trúc, nhưng kết quả thực nghiệm vẫn phải quyết định hiệu quả; báo cáo không giả định mô hình sâu hơn luôn tốt hơn.

## III. Datasets

| Dataset | Số mẫu dùng | Lớp | Dạng dữ liệu | Split |
| --- | --- | --- | --- | --- |
| EuroSAT | 27,000 | 10 | ảnh RGB 64x64 | 18,900 train / 4,050 validation / 4,050 test |
| Oxford-IIIT Pet | 7,349 official samples | 37 | ảnh RGB biến kích thước, resize 96x96 | 2,944 train / 736 validation / 3,669 official test |
| CDC Diabetes Health Indicators | 253,680 | 3 | 21 predictors dạng Conv1D (21, 1) | 177,576 train / 38,052 validation / 38,052 test |

EuroSAT có 27,000 ảnh RGB `64x64` thuộc 10 lớp land-use/land-cover. Vì mọi ảnh đều cùng kích thước, input resolution `64x64` là data-determined.

Oxford-IIIT Pet chỉ dùng các sample được tham chiếu bởi `annotations/trainval.txt` và `annotations/test.txt`. Audit xác nhận `trainval = 3,680`, `test = 3,669`, tổng official samples là `7,349`, có `37` lớp và trainval/test overlap bằng `0`. Có 41 raw images trong thư mục ảnh nhưng không nằm trong annotation chính thức; chúng bị loại khỏi thí nghiệm và không bị xóa. Bốn file có tên `.jpg` nhưng nội dung PNG (`Abyssinian_5.jpg`, `Egyptian_Mau_14.jpg`, `Egyptian_Mau_156.jpg`, `Egyptian_Mau_186.jpg`) vẫn được include vì decode theo nội dung ảnh và convert RGB trong bộ nhớ.

CDC Diabetes Health Indicators có 253,680 dòng, target `Diabetes_012`, 21 predictor, và 3 lớp. Phân bố target bị lệch mạnh: class 0 No diabetes có 213,703 dòng, class 1 Prediabetes có 4,631 dòng, và class 2 Diabetes có 35,346 dòng. Audit ghi nhận 23,899 duplicate rows; chúng không bị drop vì dữ liệu gồm nhiều biến survey rời rạc/binary và không có respondent ID để khẳng định duplicate là lỗi.

## IV. Thiết kế thực nghiệm

Train set dùng để fit model weights và mọi preprocessing có fit, ví dụ scaler của Diabetes. Validation set dùng để chọn hyperparameter và protocol. Test set chỉ dùng sau khi protocol và checkpoint đã được chọn, nên test metrics không quay lại ảnh hưởng learning rate, batch size, dropout, resolution hoặc kiến trúc.

Reproducibility dùng seed 42 cho Python, NumPy và TensorFlow/Keras. Môi trường chạy là CPU-only TensorFlow 2.21.0 trong `C:/Users/anhca/anaconda3/envs/tf312/python.exe`; thiếu GPU không phải lỗi. Fair comparison yêu cầu bốn kiến trúc trong cùng dataset dùng cùng split, preprocessing, augmentation policy, optimizer family, learning rate, batch size, EarlyStopping, seed, class-weight policy khi có, và metric definitions. Architecture là biến chính được thay đổi.

Các quyết định tham số được phân loại thành bốn nhóm: `data-determined` khi suy ra trực tiếp từ dữ liệu; `architecture-determined` khi bắt buộc bởi shape hoặc cấu trúc model; `experimentally selected` khi chọn bằng validation evidence; và `operational bound` khi là giới hạn CPU/thời gian như `max_epochs` hoặc patience.

## V. Khảo sát siêu tham số

| Dataset | Tham số | Giá trị thử | Validation evidence | Chọn |
| --- | --- | --- | --- | --- |
| EuroSAT | learning rate | 1e-5, 3e-5, 0.0001, 0.0003, 0.001, 0.003, 0.01; xác nhận 0.01 và 0.001 | Stage B: 0.01 đạt val macro F1 0.7061, cao hơn 0.001 với 0.6537 | 0.01 |
| EuroSAT | batch size | 16, 32, 64, 128 | batch size 16 đạt val macro F1 0.7090; 64 đạt 0.7061; 32 và 128 thấp hơn | 16 |
| EuroSAT | augmentation | none và conservative_flip_rotation | augmentation đạt val macro F1 0.6348, thấp hơn no augmentation 0.7090 | none |
| Oxford-IIIT Pet | image resolution | 96, 128, 160 | Stage B: 96 đạt val macro F1 0.0191; 160 đạt 0.0157 và tốn 254.21s so với 123.06s | 96x96 RGB |
| Oxford-IIIT Pet | learning rate | 0.0001, 0.0003, 0.001, 0.003, 0.01; xác nhận 0.001 và 0.003 | Stage B: 0.001 đạt val macro F1 0.0287; 0.003 đạt 0.0014 | 0.001 |
| Oxford-IIIT Pet | batch size | 16, 32, 64 | batch size 32 đạt val macro F1 0.0191; 64 đạt 0.0179; 16 đạt 0.0074 | 32 |
| Oxford-IIIT Pet | augmentation | none và horizontal_flip_small_rotation_zoom_translation | augmentation đạt val macro F1 0.0045, thấp hơn no augmentation 0.0191 | none |
| CDC Diabetes | preprocessing | none, standard | standard đạt val macro F1 0.3630, cao hơn none 0.3487 | standard scaling fit trên train |
| CDC Diabetes | learning rate | 0.0001, 0.0003, 0.001, 0.003, 0.01, 0.03 | 0.01 đạt val macro F1 0.3969; 0.03 giảm còn 0.3709 nên dừng mở rộng biên | 0.01 |
| CDC Diabetes | batch size | 256, 512, 1024, 2048 | 512 đạt val macro F1 0.3975; 2048 giảm còn 0.3541; 512 giữ trade-off metric/runtime tốt | 512 |
| CDC Diabetes | class weighting | none, balanced_inverse_frequency | balanced tăng val macro F1 từ 0.3975 lên 0.4399, class 1 recall từ 0.0000 lên 0.2579, class 2 recall từ 0.1856 lên 0.5304 | balanced_inverse_frequency |

Với EuroSAT, phạm vi learning rate dừng ở `0.01` vì Stage B xác nhận `0.01` tốt hơn `0.001` trên full train split. Batch size `16` được chọn vì đạt validation macro F1 cao nhất trong nhóm so sánh, dù thời gian mỗi epoch cao hơn. Augmentation bảo thủ không được chọn vì validation macro F1 giảm.

Với Oxford-IIIT Pet, resolution `96x96` được chọn vì có validation macro F1 tốt hơn `160x160` trong Stage B, đồng thời thời gian huấn luyện thấp hơn nhiều. Learning rate `0.001` thắng rõ trong Stage B. Augmentation ảnh thú cưng bảo thủ không cải thiện validation macro F1 nên không đưa vào final protocol.

Với CDC Diabetes, standard scaling được chọn vì cải thiện validation macro F1 so với không scaling. Learning rate `0.01` tốt nhất trong dải logarithmic trước khi `0.03` giảm hiệu năng, nên không cần mở rộng biên. Class weighting được chọn vì cải thiện macro F1 và đặc biệt cải thiện recall của Prediabetes và Diabetes, dù accuracy tổng thể giảm.

## VI. Thực nghiệm bốn mô hình CNN

### EuroSAT

| Mô hình | Accuracy | Macro precision | Macro recall | Macro F1 | Parameters | Training time (s) | Inference time (s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BasicCNN2D | 0.7398 | 0.7440 | 0.7263 | 0.7256 | 24,202 | 365.39 | 40.82 |
| AlexNetInspired2D | 0.1111 | 0.0111 | 0.1000 | 0.0200 | 260,170 | 677.58 | 82.14 |
| VGGInspired2D | 0.1111 | 0.0111 | 0.1000 | 0.0200 | 304,810 | 1071.42 | 64.27 |
| ResNetInspired2D | 0.1111 | 0.0111 | 0.1000 | 0.0200 | 324,490 | 1467.59 | 16.27 |

### Oxford-IIIT Pet

| Mô hình | Accuracy | Macro precision | Macro recall | Macro F1 | Parameters | Training time (s) | Inference time (s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BasicCNN2D | 0.0472 | 0.0160 | 0.0478 | 0.0198 | 25,957 | 20.75 | 6.53 |
| AlexNetInspired2D | 0.0409 | 0.0078 | 0.0412 | 0.0115 | 263,653 | 36.93 | 7.81 |
| VGGInspired2D | 0.0273 | 0.0007 | 0.0270 | 0.0014 | 308,293 | 70.06 | 9.50 |
| ResNetInspired2D | 0.0433 | 0.0051 | 0.0431 | 0.0080 | 327,973 | 95.51 | 10.64 |

### CDC Diabetes

| Mô hình | Accuracy | Macro precision | Macro recall | Macro F1 | Weighted F1 | Recall class 1 | Recall class 2 | Parameters | Training time (s) | Inference time (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MajorityClassBaseline | 0.8424 | 0.2808 | 0.3333 | 0.3048 | 0.7703 | 0.0000 | 0.0000 | 0 | 0.00 | 0.00 |
| BasicCNN1D | 0.6953 | 0.4488 | 0.5039 | 0.4392 | 0.7557 | 0.2518 | 0.5273 | 2,787 | 6.47 | 0.09 |
| AlexNetInspired1D | 0.6080 | 0.4802 | 0.5016 | 0.4075 | 0.7089 | 0.5094 | 0.3412 | 29,635 | 12.36 | 0.15 |
| VGGInspired1D | 0.6793 | 0.4322 | 0.4921 | 0.4261 | 0.7355 | 0.1065 | 0.6777 | 38,299 | 10.21 | 0.19 |
| ResNetInspired1D | 0.7124 | 0.4321 | 0.4933 | 0.4356 | 0.7562 | 0.0921 | 0.6520 | 44,387 | 11.51 | 0.25 |

## VII. So sánh và đánh giá

Trên EuroSAT, BasicCNN2D là mô hình duy nhất học được classifier hữu ích dưới protocol đóng băng: accuracy `0.7398` và macro F1 `0.7256`. Ba mô hình sâu hơn đều có accuracy `0.1111` và macro F1 `0.0200`, cho thấy collapse dự đoán thay vì cải thiện nhờ depth. Đây là bằng chứng rằng tăng độ phức tạp không tự động cải thiện hiệu năng nếu optimizer/protocol không phù hợp với family đó.

Trên Oxford-IIIT Pet, mọi mô hình đều yếu với protocol CPU-aware ngắn. BasicCNN2D vẫn cao nhất trong bốn mô hình với accuracy `0.0472` và macro F1 `0.0198`. Các mô hình sâu hơn tăng parameter count và runtime nhưng không cải thiện macro F1. Kết luận ở đây là trade-off xấu dưới protocol đã chọn, không phải tuyên bố rằng kiến trúc sâu luôn kém cho Oxford-IIIT Pet.

Trên CDC Diabetes, majority baseline có accuracy `0.8424` nhưng Prediabetes recall và Diabetes recall đều `0.0000`, nên accuracy cao chủ yếu phản ánh class imbalance. Trong các CNN, BasicCNN1D có macro F1 cao nhất `0.4392`; AlexNetInspired1D có Prediabetes recall cao nhất `0.5094`; VGGInspired1D có Diabetes recall cao nhất `0.6777`; ResNetInspired1D có raw accuracy cao nhất trong các CNN `0.7124` nhưng Prediabetes recall chỉ `0.0921`. Vì vậy không thể chọn mô hình chỉ dựa vào accuracy.

## VIII. Phân tích lỗi

### EuroSAT: các cặp nhầm lẫn chính của BasicCNN2D

| Mô hình | True class | Predicted class | Count |
| --- | --- | --- | --- |
| BasicCNN2D | Industrial | Residential | 104 |
| BasicCNN2D | Highway | River | 93 |
| BasicCNN2D | River | Highway | 82 |
| BasicCNN2D | PermanentCrop | Highway | 76 |
| BasicCNN2D | PermanentCrop | HerbaceousVegetation | 72 |

BasicCNN2D nhầm nhiều giữa Industrial và Residential, cũng như Highway và River. Những pattern này phù hợp với error grids đã lưu: các lớp xây dựng có cấu trúc dày đặc giống nhau, còn Highway/River có các đặc trưng tuyến tính dài trong cảnh vệ tinh. Với AlexNet-inspired, VGG-inspired và ResNet-inspired, confusion matrix cho thấy collapse về AnnualCrop trên nhiều lớp, nên lỗi chính là hành vi suy biến của mô hình dưới protocol thay vì nhầm lẫn tinh tế giữa hai lớp cụ thể.

### Oxford-IIIT Pet: các cặp nhầm lẫn chính của BasicCNN2D

| Mô hình | True class | Predicted class | Count |
| --- | --- | --- | --- |
| BasicCNN2D | newfoundland | staffordshire_bull_terrier | 50 |
| BasicCNN2D | Ragdoll | Russian_Blue | 38 |
| BasicCNN2D | pomeranian | chihuahua | 36 |
| BasicCNN2D | British_Shorthair | Russian_Blue | 35 |
| BasicCNN2D | Sphynx | Abyssinian | 35 |

Oxford có 37 breed classes và ảnh tự nhiên đa dạng. Các cặp như pomeranian -> chihuahua hoặc Ragdoll -> Russian_Blue có thể có tương đồng thị giác trong một số mẫu đã lưu, nhưng báo cáo không quy toàn bộ lỗi cho một nguyên nhân hình ảnh duy nhất. Nhiều nhầm lẫn phản ánh mức tách lớp yếu của mô hình compact và số epoch ngắn.

### CDC Diabetes: confusion theo lớp

| model_family | class_name | precision | recall | f1 | support |
| --- | --- | --- | --- | --- | --- |
| MajorityClassBaseline | No diabetes | 0.8424 | 1.0000 | 0.9145 | 32055 |
| MajorityClassBaseline | Prediabetes | 0.0000 | 0.0000 | 0.0000 | 695 |
| MajorityClassBaseline | Diabetes | 0.0000 | 0.0000 | 0.0000 | 5302 |
| BasicCNN1D | No diabetes | 0.9395 | 0.7327 | 0.8233 | 32055 |
| BasicCNN1D | Prediabetes | 0.0312 | 0.2518 | 0.0555 | 695 |
| BasicCNN1D | Diabetes | 0.3758 | 0.5273 | 0.4388 | 5302 |
| AlexNetInspired1D | No diabetes | 0.9522 | 0.6543 | 0.7756 | 32055 |
| AlexNetInspired1D | Prediabetes | 0.0293 | 0.5094 | 0.0554 | 695 |
| AlexNetInspired1D | Diabetes | 0.4591 | 0.3412 | 0.3915 | 5302 |
| VGGInspired1D | No diabetes | 0.9438 | 0.6920 | 0.7985 | 32055 |
| VGGInspired1D | Prediabetes | 0.0197 | 0.1065 | 0.0332 | 695 |
| VGGInspired1D | Diabetes | 0.3331 | 0.6777 | 0.4466 | 5302 |
| ResNetInspired1D | No diabetes | 0.9347 | 0.7358 | 0.8234 | 32055 |
| ResNetInspired1D | Prediabetes | 0.0252 | 0.0921 | 0.0396 | 695 |
| ResNetInspired1D | Diabetes | 0.3363 | 0.6520 | 0.4437 | 5302 |

Diabetes error analysis phải nhìn vào recall từng lớp. Majority baseline bỏ sót hoàn toàn Prediabetes và Diabetes. BasicCNN1D cân bằng hơn nhưng Prediabetes recall vẫn chỉ `0.2518`. AlexNetInspired1D tăng Prediabetes recall lên `0.5094` nhưng giảm Diabetes recall. VGGInspired1D tăng Diabetes recall lên `0.6777` nhưng Prediabetes recall thấp. Các trade-off này quan trọng hơn raw accuracy.

## IX. Hạn chế

- CPU-only execution giới hạn kích thước mô hình, số epoch và phạm vi hyperparameter search.
- Các kiến trúc là phiên bản giáo dục đã scale nhỏ, không phải bản lịch sử đầy đủ của AlexNet, VGG hoặc ResNet.
- Conv1D trên CDC Diabetes không có locality không gian tự nhiên; adjacency của feature chỉ đến từ thứ tự cột CSV.
- Hyperparameter search dựa trên validation evidence nhưng không exhaustive.
- Oxford-IIIT Pet có 37 lớp ảnh tự nhiên khó; protocol ngắn và mô hình from-scratch compact tạo điểm thấp.
- Test set được giữ đúng vai trò đánh giá cuối, nên không dùng test results để retune sau khi thấy kết quả.

## X. Kết luận

Về khái niệm, CNN có thể hiểu như composition của các hàm convolution, activation, pooling và phân loại. Về kiến trúc, assignment đi từ Basic CNN đến AlexNet-inspired, VGG-inspired và ResNet-inspired để kiểm tra tác động của capacity, block lặp và residual learning.

Bằng chứng thực nghiệm không ủng hộ một winner phổ quát. Trên EuroSAT và Oxford-IIIT Pet, Basic CNN là mô hình tốt nhất dưới protocol đóng băng, trong khi các mô hình sâu hơn không cải thiện và đôi khi collapse. Trên Diabetes, BasicCNN1D có macro F1 tốt nhất, nhưng từng kiến trúc khác lại có trade-off riêng về minority-class recall. Tăng complexity vì vậy không cải thiện nhất quán; nó phải được đánh giá cùng parameter count, training time, inference time và metric phù hợp với dataset.

## Figures và bảng tham chiếu

| Phạm vi | Loại hình | File figure tham chiếu |
| --- | --- | --- |
| EuroSAT | Hyperparameter | results/figures/eurosat/hyperparameters/learning_rate_stage_a.png; results/figures/eurosat/hyperparameters/batch_size_comparison.png |
| EuroSAT | Final comparison | results/figures/eurosat/eurosat_complexity_tradeoffs.png; results/figures/eurosat/confusion_matrices/basic_confusion_matrix.png; results/figures/eurosat/confusion_matrices/alexnet_inspired_confusion_matrix.png; results/figures/eurosat/confusion_matrices/vgg_inspired_confusion_matrix.png; results/figures/eurosat/confusion_matrices/resnet_inspired_confusion_matrix.png; results/figures/eurosat/errors/basic_top_confusion_errors.png |
| Oxford-IIIT Pet | Hyperparameter | results/figures/oxford_pets/hyperparameters/resolution_stage_a.png; results/figures/oxford_pets/hyperparameters/learning_rate_stage_a.png; results/figures/oxford_pets/hyperparameters/batch_size_comparison.png |
| Oxford-IIIT Pet | Final comparison | results/figures/oxford_pets/oxford_pets_complexity_tradeoffs.png; results/figures/oxford_pets/confusion_matrices/basic_confusion_matrix.png; results/figures/oxford_pets/confusion_matrices/alexnet_inspired_confusion_matrix.png; results/figures/oxford_pets/confusion_matrices/vgg_inspired_confusion_matrix.png; results/figures/oxford_pets/confusion_matrices/resnet_inspired_confusion_matrix.png; results/figures/oxford_pets/errors/basic_top_confusion_errors.png |
| CDC Diabetes | Hyperparameter | results/figures/diabetes/hyperparameters/scaling_comparison.png; results/figures/diabetes/hyperparameters/learning_rate_comparison.png; results/figures/diabetes/hyperparameters/batch_size_comparison.png; results/figures/diabetes/hyperparameters/class_weight_comparison.png |
| CDC Diabetes | Final comparison | results/figures/diabetes/diabetes_final_metrics.png; results/figures/diabetes/diabetes_complexity_tradeoffs.png; results/figures/diabetes/confusion_matrices/majority_baseline_confusion_matrix.png; results/figures/diabetes/confusion_matrices/basic_confusion_matrix.png; results/figures/diabetes/confusion_matrices/alexnet_inspired_confusion_matrix.png; results/figures/diabetes/confusion_matrices/vgg_inspired_confusion_matrix.png; results/figures/diabetes/confusion_matrices/resnet_inspired_confusion_matrix.png |
| Tổng hợp | Model comparison | results/figures/model_comparison/accuracy_by_dataset.png; results/figures/model_comparison/macro_f1_by_dataset.png; results/figures/model_comparison/parameters_vs_macro_f1.png; results/figures/model_comparison/training_time_vs_macro_f1.png |

Tổng số PNG figures hiện có dưới `results/figures/`: `56`. Các bảng metric trong báo cáo được tạo từ `eurosat_models.csv`, `oxford_pets_models.csv`, `diabetes_models.csv`, các hyperparameter CSV và các per-class/confusion-pair CSV liên quan.

## Kiểm tra integrity của báo cáo

- Báo cáo được ghi bằng UTF-8.
- Không retrain model và không chạy `model.fit()` khi tạo báo cáo.
- Không thay đổi dataset splits, hyperparameters, checkpoints, metrics CSV hoặc model weights.
- Không phát hiện mojibake hoặc đoạn prose tiếng Anh không giải thích được trong nội dung báo cáo.
