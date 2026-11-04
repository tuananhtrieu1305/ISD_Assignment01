<!-- page_target: 12-14; style: term_paper/config/style_spec.md -->

# CHƯƠNG 2. CÁC KỸ THUẬT MACHINE LEARNING CƠ BẢN

Chương này khảo sát machine learning có giám sát trên ba dạng bài toán dữ liệu bảng: phân loại nguy cơ diabetes, hồi quy giá nhà và phân loại churn. Phần thực nghiệm gồm hai track. Track A giữ nguyên kết quả của các thuật toán cổ điển trong ba pipeline nguồn. Track B cài đặt cùng một Multilayer Perceptron (MLP) bằng NumPy scratch, Keras và PyTorch. Ba implementation không dùng chung trọng số, nhưng dùng đúng cùng processed arrays, sample keys, topology, optimizer family, batch size, tập learning rate và tiêu chí early stopping.

Kết quả được báo trên ba seed mô hình 42, 52 và 62. Quyết định chạy ba seed không được đặt ra sau khi nhìn metric TEST: full matched run seed 42 mất 67,38 giây, thấp hơn ngưỡng 20 phút đã khóa trong hợp đồng thực nghiệm, nên hai repeat còn lại trở thành bắt buộc. Tổng cộng có 27 run chính, tương ứng 3 dataset × 3 framework × 3 seed. Mỗi run lưu model, prediction theo sample, metric tái tính từ prediction, learning-rate search, threshold search nếu có và hash provenance.

## 2.1. Bài toán học máy có giám sát

### 2.1.1. Classification và regression

Học có giám sát bắt đầu từ tập ví dụ \(D=\{(x_i,y_i)\}_{i=1}^{n}\), trong đó \(x_i\) là vector đặc trưng và \(y_i\) là nhãn hoặc giá trị cần dự đoán. Mô hình \(f_\theta\) được điều chỉnh để giảm một hàm mất mát trên TRAIN, nhưng mục tiêu thực tế là giảm sai số kỳ vọng trên các mẫu chưa thấy. Sự khác biệt giữa hai mục tiêu giải thích vì sao loss TRAIN thấp không đủ để kết luận mô hình tốt.

Trong classification, output thuộc một tập lớp rời rạc. Với binary classification, mô hình thường sinh một score hoặc probability \(p(y=1\mid x)\), sau đó áp dụng threshold \(t\):

\[
\hat{y}=\mathbb{1}[p\geq t].
\]

Accuracy đo tỷ lệ dự đoán đúng, nhưng có thể gây hiểu nhầm khi lớp dương hiếm. Precision trả lời “trong các mẫu được dự đoán dương, bao nhiêu mẫu thật sự dương”; recall trả lời “trong các mẫu dương thật, mô hình tìm được bao nhiêu”. F1 là trung bình điều hòa của precision và recall. ROC-AUC đánh giá thứ hạng score qua nhiều threshold, nhưng không thay thế việc chọn operating threshold cho use case cụ thể.

Trong regression, output là đại lượng liên tục. Mean Absolute Error (MAE) giữ cùng đơn vị với target và ít nhạy hơn với sai số lớn so với Root Mean Squared Error (RMSE). Hệ số \(R^2\) so sánh sai số mô hình với dự báo bằng mean target; \(R^2<0\) có nghĩa mô hình kém hơn baseline mean trên tập đang đánh giá. MAPE dễ diễn giải theo phần trăm nhưng không ổn định khi target gần 0. Trong bài toán housing của chương này, target dương từ 1,0 đến 11,5 tỷ VND nên MAPE được báo như metric phụ, còn RMSE là metric chọn chính.

Classification và regression dùng chung workflow nhưng khác output activation, loss và metric. Binary MLP dùng một logit ở lớp cuối, sigmoid khi suy luận và binary cross-entropy (BCE) khi huấn luyện. Regression MLP dùng output tuyến tính và mean squared error (MSE). Housing được huấn luyện trên standardized \(\log(1+y)\) để làm ổn định scale; mọi metric cuối được inverse-transform về tỷ VND.

### 2.1.2. Train/validation/test và khái quát hóa

Ba tập dữ liệu có vai trò tách biệt. TRAIN được dùng để fit imputer, scaler, vocabulary, one-hot categories và trọng số mô hình. VALIDATION được dùng để chọn learning rate, best checkpoint và threshold. TEST chỉ được đánh giá sau khi các lựa chọn đó đã khóa. Nếu scaler được fit trên toàn bộ dữ liệu hoặc threshold được tối ưu trực tiếp trên TEST, metric không còn mô tả đúng khả năng khái quát.

Protocol của chương giữ outer split 80/20 từ các notebook nguồn, sau đó tách 20% development làm VALIDATION. Tỷ lệ hiệu dụng là 64/16/20. Diabetes và churn dùng stratification; housing regression không stratify. Seed của split luôn là 42, kể cả khi seed khởi tạo mô hình chuyển sang 52 hoặc 62. Nhờ đó, độ lệch giữa các seed phản ánh tối ưu hóa và khởi tạo, không phản ánh việc đổi mẫu TEST.

Khái quát hóa còn phụ thuộc mức tương đồng giữa dữ liệu triển khai và dữ liệu huấn luyện. Một split ngẫu nhiên chỉ kiểm tra khả năng dự đoán các mẫu cùng snapshot phân phối. Nó không đo trực tiếp robustness trước thay đổi bệnh học, thị trường nhà ở hoặc hành vi khách hàng theo thời gian. Vì vậy, kết quả Chương 2 được giới hạn ở ba dataset và protocol đã công bố; không được chuyển thành tuyên bố về hiệu quả y khoa, định giá thị trường hoặc vận hành thương mại.

## 2.2. Các thuật toán nền tảng

### 2.2.1. Linear/logistic regression và hàm mất mát

Linear regression mô hình hóa target bằng tổ hợp tuyến tính:

\[
\hat{y}=w^Tx+b.
\]

Với MSE, nghiệm tối ưu tìm tham số làm nhỏ trung bình bình phương residual. Mô hình dễ kiểm tra và tạo baseline quan trọng, nhưng giả định quan hệ tuyến tính trong không gian đặc trưng. Pipeline housing áp dụng linear regression sau one-hot và log target. Kết quả nguồn cho thấy mô hình tuyến tính nhạy với representation và bất ổn trong một cấu hình; vì vậy báo cáo không dùng nó làm bằng chứng rằng mọi mô hình tuyến tính đều không phù hợp, mà giữ Random Forest làm baseline cổ điển mạnh hơn.

Logistic regression thay output tuyến tính bằng xác suất sigmoid:

\[
p=\sigma(w^Tx+b)=\frac{1}{1+e^{-(w^Tx+b)}}.
\]

Với nhãn \(y\in\{0,1\}\), BCE cho một mẫu là

\[
\mathcal{L}_{BCE}=-y\log p-(1-y)\log(1-p).
\]

Logistic regression vẫn tạo biên tuyến tính trong không gian đã biến đổi, nhưng probability output cho phép điều chỉnh threshold. Trong customer churn, logistic regression nguồn đạt F1 0,3562 và là baseline cổ điển cao nhất theo F1. Kết quả này có ý nghĩa vì matched MLP không vượt baseline đó một cách ổn định.

### 2.2.2. k-nearest neighbors và support vector machine

k-nearest neighbors (KNN) không học một hàm tham số cố định. Khi suy luận, thuật toán tìm \(k\) mẫu TRAIN gần nhất và tổng hợp nhãn hoặc target của chúng. Phương pháp đơn giản nhưng phụ thuộc mạnh vào scale, metric khoảng cách, giá trị \(k\) và số chiều. Khi số chiều tăng, khoảng cách giữa các điểm dễ trở nên kém phân biệt; preprocessing vì vậy là một phần của mô hình chứ không phải bước trang trí. Nền tảng phân loại nearest-neighbor và tính chất lỗi tiệm cận được trình bày trong công trình của Cover và Hart [@cover1967nearest].

Support Vector Machine (SVM) tìm siêu phẳng có margin lớn giữa các lớp. Với soft margin, các mẫu vi phạm được cho phép thông qua biến slack và hệ số điều chuẩn. Kernel có thể ánh xạ quan hệ phi tuyến sang không gian đặc trưng khác; pipeline nguồn dùng cấu hình phù hợp với quy mô dữ liệu thay vì search không giới hạn. Trên diabetes, SVM đạt F1 0,7552, thấp hơn Random Forest và matched MLP nhưng vẫn là baseline cạnh tranh. Công thức và cơ chế support-vector network được giới thiệu trong công trình của Cortes và Vapnik [@cortes1995svm].

KNN và SVM minh họa hai cách kiểm soát độ phức tạp khác nhau. KNN trì hoãn phần lớn tính toán đến inference và dựa vào locality của dữ liệu. SVM nén quyết định vào support vectors và margin. Không có thuật toán nào mặc nhiên tốt hơn; cách biểu diễn feature và phân bố dữ liệu quyết định phần lớn kết quả.

### 2.2.3. Decision tree, random forest và boosting

Decision tree chia không gian đặc trưng bằng các điều kiện tuần tự. Với classification, split có thể giảm impurity; với regression, split có thể giảm phương sai hoặc squared error trong node. Cây dễ diễn giải theo đường quyết định nhưng có phương sai cao: thay đổi nhỏ trong TRAIN có thể tạo cấu trúc khác. Pruning, giới hạn depth và minimum samples per leaf là các cơ chế kiểm soát. Nền tảng của cây classification/regression được hệ thống hóa trong CART [@breiman1984cart].

Random Forest huấn luyện nhiều cây trên các bootstrap sample và subset feature ngẫu nhiên, sau đó tổng hợp dự đoán. Việc trung bình hóa giảm phương sai so với một cây riêng lẻ [@breiman2001randomforests]. Trong các artifact nguồn, Random Forest là baseline mạnh nhất cho diabetes theo F1 0,7602 và housing theo RMSE 1,4399 tỷ VND. Với churn, Random Forest có ROC-AUC 0,6792 cao nhất trong các baseline cổ điển, dù F1 0,3561 gần logistic regression.

Gradient Boosting xây mô hình cộng dồn theo từng stage; mỗi weak learner mới đi theo hướng làm giảm loss của ensemble hiện tại. Cách nhìn tối ưu hóa trong không gian hàm được Friedman trình bày cho regression và classification [@friedman2001gradient]. Boosting có thể học quan hệ phi tuyến mạnh nhưng nhạy với learning rate, số estimator và độ sâu của cây con. Trong housing nguồn, Gradient Boosting không vượt Random Forest; đây là kết quả của cấu hình và dữ liệu cụ thể, không phải thứ hạng phổ quát giữa hai họ thuật toán.

### 2.2.4. Multilayer perceptron và backpropagation

MLP nối nhiều phép biến đổi affine và activation. Với hai hidden layer:

\[
h_1=\mathrm{ReLU}(XW_1+b_1),\quad
h_2=\mathrm{ReLU}(h_1W_2+b_2),\quad
z=h_2W_3+b_3.
\]

Binary model dùng \(p=\sigma(z)\), còn regression dùng trực tiếp \(z\). ReLU tạo phi tuyến và có đạo hàm bằng 1 khi pre-activation dương, bằng 0 khi âm. Backpropagation áp dụng quy tắc dây chuyền từ loss về \(W_3,W_2,W_1\), cho phép tối ưu toàn bộ mạng bằng gradient [@rumelhart1986backprop].

Ba implementation dùng Adam, một optimizer duy trì exponential moving average của gradient và bình phương gradient [@kingma2014adam]. Với bước \(t\), Adam hiệu chỉnh bias của hai moment rồi cập nhật từng tham số theo tỷ lệ giữa moment bậc nhất và căn moment bậc hai. Chương này không xem Adam là lời giải tối ưu cho mọi bài toán; nó được chọn để ba framework có cùng optimizer family và để scratch thể hiện một update thực sự, không chỉ forward demo.

Topology 64–32 có số tham số phụ thuộc input dimension \(d\):

\[
P=(d\times64+64)+(64\times32+32)+(32\times1+1).
\]

Do đó diabetes có 3.521 tham số, housing có 11.329 và churn có 25.729. Parameter count bằng nhau giữa NumPy, Keras và PyTorch trên từng dataset; điều này xác nhận topology logic được giữ, dù kernel số học và dtype có thể khác.

## 2.3. Quy trình dữ liệu và kiểm soát leakage

### 2.3.1. Làm sạch, mã hóa, chuẩn hóa và fit scope

Pipeline dữ liệu được thực hiện trước huấn luyện nhưng sau khi xác định ranh giới thông tin. Diabetes chuyển toàn bộ 22 cột sang numeric, loại 1.635 exact duplicate rồi giữ 21 predictor. Housing parse đơn vị diện tích, frontage, access road và price; tách address thành thành phần location; loại 6 hàng có target/area không hợp lệ. Customer churn tổng hợp transaction, session và review chỉ đến cutoff `2024-10-01 23:59:05`; `lifetime_value` và ID không được đưa vào X.

Numeric feature dùng median imputation và StandardScaler. Categorical feature dùng giá trị `Unknown` và one-hot encoding với xử lý an toàn cho category chưa thấy. Text review của customer dùng TF-IDF tối đa 300 feature, unigram và bigram. Mọi estimator trong các bộ biến đổi chỉ fit trên TRAIN. VALIDATION và TEST chỉ gọi `transform`.

Fit scope ảnh hưởng trực tiếp số chiều. Pipeline housing cũ fit preprocessor trên development 80% và tạo 154 cột. Matched protocol mới fit trên TRAIN 64%, nên các category hiếm chịu `min_frequency=20` tạo 143 cột. Đây không phải lỗi mất feature; đó là hệ quả của việc loại VALIDATION khỏi fit scope. Cả ba framework nhận đúng matrix 143 cột và cùng SHA-256 processed artifact. Phân bố target sau cleaning được tổng hợp ở Hình 2.1.

![Hình 2.1. Phân bố target của ba dataset Chương 2](../../artifacts/figures/ch2/ch2_dataset_distributions.png)

*Nguồn: sinh từ split manifest của Phase 3; mọi split được ghép lại đúng một lần.*

### 2.3.2. Split, seed, threshold và baseline

Bảng 2.1 tóm tắt dataset sau làm sạch và split. `split_sha256` đầy đủ nằm trong metadata; tiền tố trong bảng giúp đối chiếu mà không làm bảng quá rộng.

**Bảng 2.1. Quy mô dữ liệu và split khóa của Chương 2**

| Dataset | Bài toán | Raw → model rows | Raw → transformed features | TRAIN / VAL / TEST | Split hash (12 ký tự đầu) |
|---|---|---:|---:|---:|---|
| CDC Diabetes | Binary classification | 70.692 → 69.057 | 21 → 21 | 44.196 / 11.049 / 13.812 | `138c04fa519a` |
| Vietnam Housing | Regression | 30.229 → 30.223 | 12 → 143 | 19.342 / 4.836 / 6.045 | `8d8d69071704` |
| E-Commerce Behavior | Binary churn | 10.000 → 10.000 | 51 → 368 | 6.400 / 1.600 / 2.000 | `b9bf6fd92b31` |

*Nguồn bảng: `term_paper/artifacts/metrics/ch2_dataset_summary.csv` và metadata/split manifests Chương 2.*

Learning rate được chọn riêng cho từng framework/seed từ hai candidate 0,01 và 0,003 theo validation loss. Max epoch là 80, batch size 512, patience 10 và `min_delta=10^{-5}`. Early stopping phục hồi checkpoint có validation loss thấp nhất. Cách này cho phép optimizer trajectory khác nhau nhưng giữ search space và budget bằng nhau.

Threshold binary được chọn sau khi learning rate và checkpoint đã khóa. Grid gồm 61 giá trị từ 0,20 đến 0,80; tiêu chí là validation F1. TEST không tham gia lựa chọn. Threshold diabetes nằm trong khoảng 0,31–0,40. Churn biến động mạnh hơn, từ 0,20 đến 0,50, cho thấy score chưa ổn định theo seed và không nên mặc định threshold 0,5.

Baseline có hai nghĩa được tách rõ. Baseline tham chiếu đơn giản là majority class cho classification hoặc median target cho regression. Baseline cổ điển là các thuật toán đã có trong pipeline: logistic/linear regression, KNN, decision tree, Random Forest, Gradient Boosting và SVM khi phù hợp. Kết quả cổ điển không nằm trong matched topology table vì chúng không có cùng số tham số hay cơ chế huấn luyện. Chúng được dùng để kiểm tra liệu MLP có mang lại lợi ích thực tế trên dataset hay không.

## 2.4. Datasets của Chương 2

### 2.4.1. CDC Diabetes Health Indicators — binary

CDC Diabetes Health Indicators bản balanced có 70.692 hàng raw và 22 cột, gồm target `Diabetes_binary` cùng 21 chỉ báo sức khỏe/lối sống. Nguồn/link là [trang dataset Kaggle](https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset) [@teboul2019diabetes]; license chưa xác minh được từ metadata chính thức có thể truy cập nên báo cáo không suy đoán từ bản mirror. Nguồn local có kích thước 6.347.570 bytes. Sau khi loại exact duplicate, còn 69.057 hàng: class 0 có 33.960 mẫu và class 1 có 35.097 mẫu, tương ứng positive rate 50,82%.

Các predictor gồm binary indicator như `HighBP`, `HighChol`, `Smoker`, `PhysActivity`; ordinal survey code như `GenHlth`, `Age`, `Education`, `Income`; số ngày sức khỏe tinh thần/thể chất kém và BMI. Không có missing value biểu diễn trực tiếp trong snapshot, nhưng median imputer vẫn nằm trong pipeline để schema inference ổn định.

Bản balanced thuận lợi cho so sánh thuật toán nhưng không mô tả prevalence diabetes trong dân số. Một metric accuracy hoặc recall cao ở đây không phải độ chính xác chẩn đoán lâm sàng. Dữ liệu là health indicators tự báo cáo và nhãn dataset, không phải hồ sơ chẩn đoán được thẩm định cho từng use case triển khai.

### 2.4.2. Vietnam Housing Dataset 2024

Vietnam Housing Dataset 2024 có 30.229 hàng raw, 12 cột và file 3.532.685 bytes. Nguồn/link là [trang dataset Kaggle](https://www.kaggle.com/datasets/nguyentiennhan/vietnam-housing-dataset-2024) [@nguyen2024housing]; license chưa xác minh được từ metadata chính thức có thể truy cập và được ghi `UNVERIFIED` trong registry. Sáu hàng bị loại do price/area không hợp lệ; tập model còn 30.223 hàng. Target `Price_BillionVND` nằm trong khoảng 1,0–11,5 tỷ VND, mean 5,873 và median 5,9. Diện tích sau làm sạch có median 56 m² và mean 68,51 m².

Sáu feature numeric là area, frontage, access road, floors, bedrooms và bathrooms. Sáu feature categorical gồm city, district, legal status, furniture state, house direction và balcony direction. `price_per_m2_million` chỉ được dùng cho EDA; đưa biến này vào X sẽ tiết lộ trực tiếp target. Raw address cũng không được one-hot toàn chuỗi vì cardinality cao và nguy cơ ghi nhớ listing; pipeline chỉ dùng các thành phần location đã tách.

Target được biến đổi theo \(z=(\log(1+y)-\mu_{TRAIN})/\sigma_{TRAIN}\). Giá trị \(\mu\) và \(\sigma\) chỉ tính trên TRAIN, được lưu trong metadata và dùng chung cho ba framework. Prediction TEST được inverse bằng \(\exp(z\sigma+\mu)-1\) trước khi tính MAE/RMSE/R²/MAPE. Nhờ vậy, bảng kết quả giữ đơn vị tỷ VND thay vì scale nội bộ khó diễn giải.

Dataset là snapshot rao bán, không nhất thiết là giá giao dịch. Missingness cao ở hướng nhà, hướng ban công, access road và furniture có thể mang thông tin về hành vi đăng tin, không chỉ về tài sản. Kết quả không được suy rộng thành chỉ số giá nhà toàn Việt Nam.

### 2.4.3. Synthetic E-Commerce Customer Behavior

Synthetic E-Commerce Customer Behavior có nguồn/link tại [trang dataset Kaggle](https://www.kaggle.com/datasets/lorenzoscaturchio/ecommerce-behavior) [@scaturchio2026ecommerce]. README đi kèm snapshot local ghi GPL-3.0; registry đánh dấu `PARTIALLY_VERIFIED` vì license chưa được đối chiếu độc lập từ metadata trang nguồn. Dataset gồm năm bảng: 10.000 customers, 1.000 products, 120.000 transactions, 80.000 sessions và 25.000 reviews; tổng dung lượng năm CSV chính và README là 17.139.547 bytes. Target churn có 8.306 class 0 và 1.694 class 1, tức positive rate 16,94%.

Feature engineering chỉ dùng sự kiện trước cutoff. Transaction tạo RFM-like aggregate, trạng thái order, category/brand diversity và spend theo tám category phổ biến. Session tạo count, duration, page views, conversion, bounce, cart addition, device/channel. Review tạo count, rating, low-rating share, verified share, helpful votes và text gộp. Sau preprocessing, 51 raw feature thành 368 transformed feature.

Bảng 2.2 đưa ba mẫu rút gọn để minh họa input/output. Đây là hàng dữ liệu thật đã giảm cột hoặc ẩn định danh; không phải request schema đầy đủ.

**Bảng 2.2. Mẫu input/output rút gọn và phân bố target**

| Dataset | Một số input của mẫu | Output mẫu | Phân bố/summary chính |
|---|---|---|---|
| Diabetes | `HighBP=1`, `HighChol=0`, `BMI=26`, `Smoker=0`, `PhysActivity=1`, `Age=4`, `Income=8` | `Diabetes_binary=0` | Class 0/1 = 33.960/35.097 sau cleaning |
| Housing | `Area=84 m²`, `Floors=4`, `Legal status=Have certificate`; một số trường hướng/road thiếu | `Price=8,6` tỷ VND | Median 5,9; khoảng 1,0–11,5 tỷ VND |
| E-Commerce | Khách đã ẩn ID, tuổi 28, giới tính M, country BR, segment Premium, email/app opt-in = 0 | `is_churned=0` | Không churn/churn = 8.306/1.694 |

*Nguồn bảng: raw rows và dataset summaries được khóa trong manifests Chương 2; các định danh đã được lược bỏ khi trình bày.*

Dữ liệu churn là synthetic, giúp tái lập và không chứa PII thật, nhưng quan hệ feature–target có thể phản ánh rule của generator. Dataset cung cấp nhãn `is_churned` mà không có churn date chính xác; cutoff giảm future leakage ở feature nhưng không giải quyết hoàn toàn ambiguity của outcome window.

## 2.5. Ba cách cài đặt MLP

### 2.5.1. NumPy scratch: forward, loss, backpropagation và update

Implementation scratch không gọi autograd hay layer API. Constructor khởi tạo ba ma trận trọng số theo He initialization và bias bằng 0. Forward lưu \(X,z_1,h_1,z_2,h_2\) để backprop. Binary gradient tại output là \((p-y)/n\); regression là \(2(\hat{y}-y)/n\). Với churn, sample weight theo class được nhân vào output gradient và chuẩn hóa bằng tổng weight.

Đoạn mã rút gọn sau cho thấy đường gradient; code đầy đủ nằm trong `term_paper/src/scratch/mlp.py`.

```python
score, cache = self._forward(x)
delta = (score - y) / n if self.task == "binary" else 2 * (score - y) / n
gradients["W3"] = cache["h2"].T @ delta
gradients["b3"] = np.sum(delta, axis=0, keepdims=True)
delta2 = (delta @ self.params["W3"].T) * (cache["z2"] > 0)
gradients["W2"] = cache["h1"].T @ delta2
gradients["b2"] = np.sum(delta2, axis=0, keepdims=True)
delta1 = (delta2 @ self.params["W2"].T) * (cache["z1"] > 0)
gradients["W1"] = cache["x"].T @ delta1
gradients["b1"] = np.sum(delta1, axis=0, keepdims=True)
```

Adam scratch duy trì hai state cho từng parameter, hiệu chỉnh bias và update theo mini-batch. Unit test kiểm tra output shape/range, loss giảm trên toy binary/regression, numerical gradient tại một phần tử `W3` và prediction parity sau save/load. Scratch tính bằng NumPy float64 trong phần lõi; Keras/PyTorch dùng float32. Đây là implementation deviation có chủ ý để numerical-gradient test ổn định, và được giữ trong diễn giải sai khác số học.

### 2.5.2. Keras Dense MLP

Keras model dùng `Sequential`: `Input(d) → Dense(64, relu) → Dense(32, relu) → Dense(1)`. Lớp cuối không gắn sigmoid; `BinaryCrossentropy(from_logits=True)` dùng logit ổn định khi train, còn sigmoid chỉ áp dụng trong `predict_score`. Regression dùng `MeanSquaredError`. `EarlyStopping` theo `val_loss` và `restore_best_weights=True`.

```python
self.model = keras.Sequential([
    keras.layers.Input(shape=(input_dim,)),
    keras.layers.Dense(64, activation="relu"),
    keras.layers.Dense(32, activation="relu"),
    keras.layers.Dense(1),
])
loss = (keras.losses.BinaryCrossentropy(from_logits=True)
        if task == "binary" else keras.losses.MeanSquaredError())
self.model.compile(
    optimizer=keras.optimizers.Adam(learning_rate),
    loss=loss,
)
```

Model lưu ở định dạng `.keras` cùng metadata JSON mô tả input dimension, task, hidden units, seed và learning rate. Test tải lại model và yêu cầu prediction parity với tolerance \(10^{-6}\). Keras cung cấp graph/layer abstraction thuận tiện, nhưng abstraction đó không thay thế việc khóa preprocessing và threshold bên ngoài model.

### 2.5.3. PyTorch MLP

PyTorch dùng `nn.Sequential` với ba `nn.Linear` và hai `nn.ReLU`. Training loop được viết rõ: tạo permutation theo seed, lấy mini-batch, `zero_grad`, forward, loss, `backward`, `optimizer.step`, sau đó đo train/validation loss. Best `state_dict` được sao chép và phục hồi khi kết thúc.

```python
self.model = nn.Sequential(
    nn.Linear(input_dim, 64), nn.ReLU(),
    nn.Linear(64, 32), nn.ReLU(),
    nn.Linear(32, 1),
)
optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
optimizer.zero_grad(set_to_none=True)
loss = self._loss(self.model(x_batch), y_batch, sample_weight)
loss.backward()
optimizer.step()
```

PyTorch model lưu config và `state_dict` trong `.pt`. Inference chạy trong `torch.no_grad()`. Test xác nhận train/infer/save/load và parameter count. Sự khác nhau chính so với Keras nằm ở mức điều khiển training loop; phép toán logic của topology không đổi. Bảng 2.3 đối chiếu các điểm tương đương và khác biệt được quản lý của ba implementation.

**Bảng 2.3. Đối chiếu ba implementation MLP**

| Thành phần | NumPy scratch | Keras | PyTorch |
|---|---|---|---|
| Dense/ReLU | Matrix operation tự cài đặt | `Dense` | `Linear` + `ReLU` |
| Gradient | Backprop viết tay, có numerical-gradient test | Autodiff | Autograd |
| Optimizer | Adam viết tay | `keras.optimizers.Adam` | `torch.optim.Adam` |
| Early stopping | Loop viết tay, copy best parameters | Callback | Loop viết tay, copy `state_dict` |
| Dtype chính | float64 trong model core | float32 | float32 |
| Save/load | `.npz` | `.keras` + metadata | `.pt` config + state |
| Tham số Diabetes/Housing/Churn | 3.521 / 11.329 / 25.729 | Giống scratch | Giống scratch |

*Nguồn bảng: `term_paper/src/scratch/mlp.py`, `keras_impl/mlp.py`, `pytorch_impl/mlp.py` và load/parameter-parity tests.*

## 2.6. Kết quả thực nghiệm và so sánh

Hình 2.2 đặt metric chính của ba framework trên cùng TEST cạnh nhau; Hình 2.3 dùng validation loss của seed 42 để kiểm tra diễn biến hội tụ, không dùng để chọn kết quả thuận lợi.

![Hình 2.2. Metric chính của matched MLP trên TEST](../../artifacts/figures/ch2/ch2_framework_primary_metrics.png)

*Nguồn: `ch2_framework_comparison.csv`; cột là mean và error bar là sample standard deviation của ba seed.*

![Hình 2.3. Validation loss của learning rate được chọn ở seed 42](../../artifacts/figures/ch2/ch2_validation_loss_curves.png)

*Nguồn: history artifact của run seed 42. Hình dùng để kiểm tra hội tụ, không dùng để xếp hạng framework.*

Bảng 2.4 trình bày metric TEST dạng mean ± SD. Với classification, F1 là cột chính; với regression, RMSE là cột chính. Dấu “—” thể hiện metric không áp dụng, không phải dữ liệu thiếu.

**Bảng 2.4. Matched MLP trên TEST, mean ± SD của ba seed**

| Dataset | Framework | Accuracy | Precision | Recall | F1 | ROC-AUC | MAE | RMSE | R² |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Diabetes | NumPy | 0,7326 ± 0,0069 | 0,6780 ± 0,0110 | 0,9035 ± 0,0165 | 0,7746 ± 0,0020 | 0,8199 ± 0,0007 | — | — | — |
| Diabetes | Keras | 0,7338 ± 0,0045 | 0,6801 ± 0,0074 | 0,8997 ± 0,0108 | 0,7746 ± 0,0014 | 0,8213 ± 0,0012 | — | — | — |
| Diabetes | PyTorch | 0,7372 ± 0,0041 | 0,6867 ± 0,0052 | 0,8882 ± 0,0051 | 0,7745 ± 0,0023 | 0,8220 ± 0,0013 | — | — | — |
| Housing | NumPy | — | — | — | — | — | 1,0530 ± 0,0084 | 1,4061 ± 0,0147 | 0,5862 ± 0,0086 |
| Housing | Keras | — | — | — | — | — | 1,0637 ± 0,0112 | 1,4111 ± 0,0104 | 0,5833 ± 0,0061 |
| Housing | PyTorch | — | — | — | — | — | 1,0488 ± 0,0040 | 1,3990 ± 0,0033 | 0,5905 ± 0,0019 |
| Churn | NumPy | 0,5718 ± 0,0578 | 0,2345 ± 0,0078 | 0,6686 ± 0,1127 | 0,3454 ± 0,0078 | 0,6379 ± 0,0085 | — | — | — |
| Churn | Keras | 0,5125 ± 0,0627 | 0,2166 ± 0,0101 | 0,7109 ± 0,0922 | 0,3308 ± 0,0083 | 0,6260 ± 0,0172 | — | — | — |
| Churn | PyTorch | 0,6012 ± 0,0618 | 0,2410 ± 0,0141 | 0,6195 ± 0,1110 | 0,3443 ± 0,0080 | 0,6476 ± 0,0215 | — | — | — |

*Nguồn bảng: `term_paper/artifacts/metrics/ch2_framework_summary.csv`, TEST predictions của seed 42/52/62 và verifier Phase 3.*

### 2.6.1. So sánh trên diabetes classification

Ba framework gần như bằng nhau theo F1: 0,7746 với NumPy, 0,7746 với Keras và 0,7745 với PyTorch sau khi làm tròn bốn chữ số. Chênh lệch giữa mean nhỏ hơn SD của từng implementation, nên không có bằng chứng thực nghiệm để tuyên bố một framework tốt hơn theo F1. Điều đáng chú ý hơn là trade-off precision–recall: NumPy có recall mean 0,9035, Keras 0,8997 và PyTorch 0,8882; PyTorch đổi một phần recall lấy precision/accuracy cao hơn.

Threshold validation giải thích trade-off này. Qua chín run diabetes, threshold nằm 0,31–0,40, đều thấp hơn 0,5. Việc hạ threshold tăng số mẫu được dự đoán class 1, từ đó tăng recall và giảm precision. Nếu dùng 0,5 cố định, so sánh sẽ đánh đồng calibration khác nhau với năng lực xếp hạng. ROC-AUC 0,8199–0,8220 gần nhau hơn F1 thresholded và cũng gần Random Forest nguồn 0,8208.

Matched MLP vượt Random Forest nguồn theo F1: best mean 0,7746 so với 0,7602. Tuy nhiên, so sánh này không phải controlled topology comparison vì baseline nguồn dùng outer TRAIN 80% cho fit, còn MLP dùng TRAIN 64% và VALIDATION 16% riêng. Kết quả cho thấy MLP cạnh tranh trong protocol hiện tại; nó không chứng minh MLP phổ quát hơn Random Forest hay phù hợp để chẩn đoán.

### 2.6.2. So sánh trên house-price regression

PyTorch có RMSE mean thấp nhất trong ba matched implementation: 1,3990 ± 0,0033 tỷ VND. NumPy đạt 1,4061 ± 0,0147 và Keras 1,4111 ± 0,0104. Khoảng cách PyTorch–NumPy khoảng 0,0072 tỷ VND, nhỏ so với sai số tuyệt đối hơn một tỷ VND và không đủ để tạo kết luận kiến trúc, vì topology giống nhau. PyTorch cũng có MAE 1,0488 và \(R^2=0,5905\), cao nhất trong nhóm.

Cả ba matched MLP vượt Random Forest nguồn RMSE 1,4399 trong lần so sánh này. Best PyTorch cải thiện khoảng 0,0409 tỷ VND, tương đương 2,84% RMSE của baseline. Mức cải thiện có thật trong artifact nhưng nhỏ so với độ phân tán giá và giới hạn dữ liệu. Không nên chuyển chênh lệch này thành lời khẳng định MLP định giá tốt hơn trong vận hành.

Input dimension của housing là 143, không phải 154 như notebook nguồn. Việc fit category vocabulary chỉ trên TRAIN làm representation chặt hơn và tránh để VALIDATION ảnh hưởng feature space. Kết quả vì vậy không so trực tiếp từng chữ số với Improved DNN cũ; nó là một matched experiment mới với protocol nghiêm ngặt hơn.

### 2.6.3. So sánh trên customer churn classification

Churn là kết quả âm quan trọng nhất. NumPy có F1 mean 0,3454 ± 0,0078; PyTorch 0,3443 ± 0,0080; Keras 0,3308 ± 0,0083. Không implementation nào vượt logistic regression nguồn 0,3562 hoặc Random Forest 0,3561. Theo ROC-AUC, PyTorch đạt 0,6476, NumPy 0,6379 và Keras 0,6260, đều dưới Random Forest nguồn 0,6792.

Accuracy không được dùng để che kết quả này. Majority class đã chiếm 83,06%, nên một mô hình dự đoán tất cả khách không churn có accuracy cao nhưng F1 lớp churn bằng 0. Matched MLP chủ động hạ threshold để tăng recall; Keras mean recall 0,7109 nhưng precision chỉ 0,2166. Đây là operating point phát hiện nhiều churner hơn với chi phí false positive lớn.

Độ lệch giữa seed rõ hơn diabetes và housing. Accuracy SD của ba framework khoảng 0,058–0,063; recall SD khoảng 0,092–0,113. Threshold Keras ở hai seed chạm cận dưới 0,20, còn seed thứ ba là 0,36. Dấu hiệu này cho thấy score calibration và decision boundary chưa ổn định. Thay vì chọn một seed đẹp, báo cáo giữ mean ± SD và kết luận rằng MLP 64–32 không tạo cải thiện đáng tin cậy trên representation churn hiện tại. Hình 2.4 và Bảng 2.5 đặt kết quả này cạnh baseline cổ điển để phân biệt cải thiện thật với trường hợp mô hình sâu không tạo lợi ích.

![Hình 2.4. Baseline cổ điển mạnh nhất và matched MLP](../../artifacts/figures/ch2/ch2_classical_vs_mlp.png)

*Nguồn: baseline từ CSV của pipeline gốc; MLP là mean ± SD của ba seed. Với housing, thấp hơn là tốt hơn; với hai bài classification, cao hơn là tốt hơn.*

**Bảng 2.5. Baseline cổ điển mạnh nhất so với matched MLP tốt nhất**

| Dataset | Metric | Baseline cổ điển | Giá trị baseline | Matched framework cao nhất/thấp nhất phù hợp | Mean ± SD |
|---|---|---|---:|---|---:|
| Diabetes | F1 ↑ | Random Forest | 0,7602 | Keras | 0,7746 ± 0,0014 |
| Housing | RMSE ↓ | Random Forest Regressor | 1,4399 | PyTorch | 1,3990 ± 0,0033 |
| Churn | F1 ↑ | Logistic Regression | 0,3562 | NumPy scratch | 0,3454 ± 0,0078 |

*Nguồn bảng: `term_paper/artifacts/metrics/ch2_best_vs_classical.csv`; baseline từ assignment nguồn, matched MLP từ TEST seed 42/52/62.*

Training duration chỉ mô tả máy và lần chạy cụ thể. Mean training time dao động mạnh khi hệ thống có tải nền; một số repeat NumPy/Keras chậm hơn rõ dù cùng cấu hình. Keras `model.predict` còn có overhead API khác PyTorch direct tensor call. Vì vậy duration được lưu để audit operational cost, không dùng làm bằng chứng một framework “nhanh nhất” phổ quát.

## 2.7. Phân tích sai số và giới hạn

### 2.7.1. Imbalance, calibration và failure cases

Diabetes gần cân bằng sau cleaning nên F1, accuracy và ROC-AUC cùng mang thông tin. Tuy vậy threshold tối ưu F1 thấp hơn 0,5 làm recall cao và precision thấp hơn. Trong ngữ cảnh screening, điều này có thể phù hợp nếu false negative đắt; trong ngữ cảnh khác, false positive có thể tạo chi phí. Dataset không cung cấp cost matrix lâm sàng, nên tiểu luận không chọn operating point cho bệnh viện và không diễn giải probability như nguy cơ đã calibration.

Churn cho thấy imbalance làm metric thay đổi theo threshold. Score có ROC-AUC trên 0,62 nhưng F1 chỉ quanh 0,33–0,35. Khi threshold giảm, recall tăng nhưng precision vẫn thấp vì base rate 16,94%. Hai seed Keras chọn threshold 0,20 ở biên search là failure signal: search range có thể chưa bao phủ optimum, hoặc output probability bị dịch do class weighting. Mở rộng range sau khi nhìn TEST sẽ vi phạm protocol; vì vậy run được giữ nguyên. Hướng tiếp theo là calibration trên VALIDATION, PR-AUC làm metric chọn chính, hoặc focal loss/class-balanced sampling được pre-register trước run mới.

Housing có RMSE xấp xỉ 1,40 tỷ VND và MAE xấp xỉ 1,05 tỷ VND. RMSE lớn hơn MAE cho thấy một số listing có sai số cao hơn mặt bằng. Không có evidence để quy các residual đó cho một nguyên nhân duy nhất. Location được mã hóa bằng category với minimum frequency; listing ở district hiếm có thể rơi vào nhóm infrequent. Missingness của frontage/road/hướng cũng có thể tạo uncertainty. Một phân tích tiếp theo nên chia residual theo price band, city và missingness pattern, nhưng không được điều chỉnh model sau khi xem TEST mà vẫn dùng lại cùng TEST để tuyên bố cải thiện.

Ở cấp implementation, topology giống nhau không làm quỹ đạo tối ưu giống nhau. NumPy dùng float64, Keras/PyTorch dùng float32; framework có kernel order và shuffle implementation khác. Learning rate được chọn riêng theo validation; best epoch cũng khác. Kết quả diabetes gần nhau cho thấy những sai khác này không làm thay đổi F1 đáng kể trong bài toán đó. Kết quả churn biến động hơn cho thấy dữ liệu/decision threshold đang chi phối nhiều hơn tên framework.

### 2.7.2. Tác động của dữ liệu tổng hợp và tính đại diện

Customer dataset được sinh theo rule và seed. Ưu điểm là tái lập, schema phong phú và không dùng danh tính thật. Nhược điểm là mô hình có thể học dấu vết của generator, trong khi quan hệ churn ngoài đời chịu tác động của chiến dịch, cạnh tranh, seasonality và định nghĩa nghiệp vụ. Không có churn timestamp chính xác cũng làm observation/label window khó xác định. Matched MLP không vượt logistic regression là một kết quả hợp lý: nhiều quan hệ có thể gần tuyến tính trong engineered feature space, hoặc sample 10.000 chưa đủ để topology sâu hơn tạo lợi ích.

Diabetes balanced loại bỏ prevalence tự nhiên, nên positive predictive value ngoài dataset có thể khác mạnh. Các biến self-report chứa recall bias và coding theo survey. Nếu triển khai, model cần external validation trên quần thể đích, calibration và review y khoa. Output trong Phase 6 sẽ có cảnh báo “không phải chẩn đoán y khoa”.

Housing là snapshot rao bán. Giá asking không bằng giá giao dịch; location parsing từ chuỗi address có thể lỗi; các category hiếm bị gộp. Model cũng không biết lãi suất, thời điểm giao dịch hoặc chất lượng xây dựng chi tiết. Do split ngẫu nhiên, hàng cùng khu vực có thể xuất hiện ở cả TRAIN và TEST. Một đánh giá khó hơn nên dùng temporal hoặc geographic holdout.

Cuối cùng, baseline cổ điển và matched MLP không dùng hoàn toàn cùng fit scope. Các CSV nguồn được tái sử dụng để bảo toàn bằng chứng assignment; MLP mới dùng VALIDATION riêng và preprocessor fit 64% TRAIN. Bảng 2.5 vì vậy là contextual comparison, không phải phép thử chỉ thay đổi model. So sánh công bằng nhất trong chương là giữa NumPy/Keras/PyTorch ở Track B, nơi processed hash và split hash giống nhau.

## 2.8. Tiểu kết chương

Chương 2 đã trình bày các kỹ thuật supervised learning từ mô hình tuyến tính, KNN, SVM, cây, Random Forest, boosting đến MLP. Phần thực nghiệm bổ sung ba implementation train/infer/save/load được trên cả ba dataset. Numerical-gradient test xác nhận backprop scratch; parameter count khớp giữa framework; 27 prediction artifact cho phép tái tính metric mà không dựa vào số nhập tay.

Với diabetes, ba framework đạt F1 gần như trùng nhau quanh 0,7745 và đều cạnh tranh với baseline cổ điển. Với housing, PyTorch có RMSE mean thấp nhất 1,3990 tỷ VND, nhưng khoảng cách giữa framework nhỏ so với sai số bài toán. Với churn, cả ba MLP không vượt logistic regression/Random Forest nguồn; threshold và recall biến động theo seed. Kết quả này trả lời một phần RQ1: khi protocol và topology được giữ, tên framework không tạo ưu thế nhất quán; chênh lệch lớn hơn xuất hiện từ dữ liệu, calibration và stochastic optimization.

Bài học chuyển sang Chương 3 là inductive bias. MLP coi transformed feature như một vector không có cấu trúc không gian. CNN đưa locality và weight sharing vào kiến trúc, phù hợp tự nhiên hơn với ảnh. Tuy nhiên, Chương 3 cũng kiểm tra Conv1D trên dữ liệu bảng để cho thấy một inductive bias chỉ có giá trị khi quan hệ lân cận giữa feature được giải thích và kiểm soát.
