# Phase34 — lịch sử kiểm tra trước phát hành

R1:37test/0skip PASS, nội dung manuscript đã đủ sáu chương. Rà soát traceability cho
thấy các yêu cầu cleanup/runtime/thu nhận chưa có liên kết trực tiếp tới biên bản
thực thi20–23, dù các phase đó đã hoàn tất. R2 bổ sung report/hash của các phase này
và environment.json, thêm một test RED→GREEN. Không sửa SRS/metric/manuscript.

R3:giữ38test, cô lập output integration trong TemporaryDirectory riêng bên dưới
report/, cùng độ sâu thư mục để kiểm relative link. Guard xác minh đúng thư mục do
test sở hữu, không trỏ publication; tempfile chỉ dọn các fixture mới đó. Test hồi
quy sau phát hành vì vậy không ghi đè bản thảo frozen. RED isolation guard được giữ.

Active nghiệm thu: acceptance-tests-r3.xml, acceptance_coverage_r3.json và lint-r3.json.
R1/r2 XML/coverage/review giữ nguyên, không cộng trùng số test. Source đúng thời điểm
review r1/r2 được giữ trong ZIP riêng, không chuyển verdict cũ sang source đã sửa:

- source_review_r1.zip SHA256958df127843df435ca0029b596bdc94fbb9e03d9ea748f92e773d9ce4cef9ce6.
- source_review_r2.zip SHA256ec66ae12f3f18819bbcb65fc926e9feb711ee3155374e291502d5ff18e0b2b30.

Các thay đổi này chỉ ở bộ tích hợp/kiểm tra chưa phát hành của Phase34, không chạm
source/evaluator/TEST/config/checkpoint đã khóa22–33. Bản thảo cuối vẫn SHA256
dcb895acfd76f1ad616baecd7fdc7fa099becbc0cc508a80b3c0432eabef2b19.
Không có lần train/forward validation/TEST hoặc batch benchmark mới.
