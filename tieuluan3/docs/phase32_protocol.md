# Giao thức nghiệm thu serving Phase32

Chỉ inference trên mẫu TRAIN/parent TRAIN cố định trong samples.json, seed42 đã
khai báo trước. Không train, tuning, hoặc mở TEST Ch2–6. KG–RAG là compact demo,
khác benchmark lịch sử; Wikidata chỉ browser. Agent ID-bound,không LLM.

1. CPU:18 dataset/family request (3MLP,3CNN,3RNN,3LSTM,3KG,3agent), đủ mọi slot.
   Wikidata5slot unavailable là kết quả đúng, browser có revision/citation thật.
2. Local GPU:12 request neural,36slot; scratch NumPy/CPU, Keras TensorFlow/CUDA và
   PyTorch/CUDA trong2env độc lập, không import framework native trong HTTP driver.
   Không fallback. Mỗi implementation so với CPU portable của chính checkpoint,
   không so output của3mô hình đã train độc lập như thể weights giống nhau.
3. Parity serving trước probe GPU:probabilities/values allclose rtol1e-4,atol1e-5,
   finite/shape/label mapping. Nếu fail giữ evidence, không nới ngưỡng/tuning/checkpoint.
   Đây là smoke TRAIN, không predictive accuracy hoặc benchmark TEST mới.
4. Đo first-call inference batch1 riêng, HTTP wall gồm coldload/process/poll500ms;
   không gọi là benchmark5warmup/30repeat cũ. Không suy p95 hay SLA từ một lượt.
5. Memory monitor0,1s: tổng PSS web worker và mọi process trong job group; RSS là
   fallback bảo thủ và được ghi cờ. BudgetCPU448MiB, GPU4GiB. Không gồm gunicorn
   master/OS/CUDA VRAM, không cam kết không bỏ qua peak giữa2mẫu. Chừa64MiB so với
   free-tier512MB; chỉ proxy local, cần thực tế Render để khẳng định cloud fit/SLA.
6. Hard job deadlineCPU60s/GPU300s; từng tác tử/tool giữ giới hạn15s cũ. Cancel,
   timeout/memory →terminate/kill process group và trạng thái rõ; không tự retry
   inference đã hoàn tất. Restart không durable; pending/running cũ không tự lặp.
7. Metadata schema/OpenAPI,body/depth/MIME/shape/finite,ownership/idempotency,CORS,
   rate/capacity/TTL,partialfailure,artifacthash và nạp CPU không pickle tùy ý.
8. Lock dependency CPU là subset đúng phiên bản/hash uv.lock; không nâng env cũ.
   Gói nhỏ chỉ runtime closure,không raw train/cache/test predictions/notebook.

## Development incident: CPU package dev1

Live Gunicorn đã qua12request neural; FinQA kích guard memory_budget448MiB,5slot
unavailable đúng cấu trúc. Liveness không crash-loop. Chưa lưu peak đầy đủ vì
smoke script dừng ở assert; không bịa số peak. Log: http_cpu_dev1.gunicorn.log.
Không coi dev1 PASS. Bản gói dev1 giữ nguyên làm development snapshot.

Nguyên nhân allocation:loader cũ đọc gzip→bytes→decode→splitlines toàn corpus và
nạp cả2miền. Loader mới apps/api/v3/rag_streaming.py stream từng dòng và chỉ giữ
corpus/index miền được yêu cầu, vẫn kiểm manifest6file/hash/size/budget trướcjoblib.
Giữ source/index/ranking/answer Phase30 nguyên byte. TDD exact parity evidence/
graph_paths/prediction trên2câu demo phải PASS trước đo RAM lại. Không rebuild corpus.

## Kết quả phát triển tiếp theo

Domain-only streaming dev2 vẫn vượt guard: peak sampled web+job456,85MiB.
Không nâng budget448MiB. Bản cuối giữ full immutable index, tính cùng ranking B0–B4,
stream kiểm toàn bộ corpus/hash/ID/count nhưng chỉ giữ union top-k text tối đa50.
Frozen service tính lại ranking/answer như cũ. Exact evidence/graph/prediction parity
medical và finance PASS; không rebuild, serialize hoặc thay candidate universe.
CPU dev3 PASS; CPU finalv2 FinQA401,04MiB,medical288,72MiB.

Lượt GPUv2 bị gián đoạn không có final receipt, process đã thoát. Log gốc được giữ
ở interruptions theo biên bản riêng, sau đó chạy lại nguyên bộ smoke TRAIN với
cùng package/checkpoint/tolerance. Không ghép lượt dở, không mở TEST.
