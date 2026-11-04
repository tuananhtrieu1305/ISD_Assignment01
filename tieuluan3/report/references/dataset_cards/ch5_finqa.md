# Dataset card — FinQA

## Nhận dạng và nguồn

- Dataset ID: `ch5_finqa`.
- Chương/bài toán: Chương 5, truy hồi bằng chứng và suy luận số học trên báo cáo tài chính.
- Repo chính thức: <https://github.com/czyssrs/FinQA>; bài báo EMNLP 2021: <https://aclanthology.org/2021.emnlp-main.300/>.
- Snapshot: commit `0f16e2867befa6840783e58be38c9efb9229d742`, truy cập 2026-10-12.
- License: MIT theo file `LICENSE` của repo.
- Local: `term_paper/knowledge_rag/data/raw/finqa`; 122.256.362 byte; 46 file; manifest SHA-256 `ab4284ccef57f880660c3f0049aaf47fa707ba34a7cc5e3da3be020c7f1728ca`.

## Kích thước và schema đo từ snapshot

- Bốn file split chứa 9.200 example/QA: train 6.251, dev 883, public test 1.147 và private test 919.
- Ba split public có 8.281 reasoning program; private test không công bố gold reference. Audit quan sát 993 output rỗng trên cả bốn split, chủ yếu do thiết kế private test.
- ID có dạng `company/year/page.pdf-index`; có 799 khóa company-year khác nhau trong snapshot. Đây là số đo trên ID local, không được diễn giải thành số báo cáo pháp lý độc lập nếu chưa đối chiếu nguồn gốc.
- Mỗi example có `pre_text`, `post_text`, `table`, `id`, và `qa`; phần `qa` public chứa question, program, gold evidence và execution answer.
- Nếu đếm trên từng example (có lặp context giữa câu hỏi), có 58.322 table row và 223.354 text segment.

## Phân bố sơ bộ

- Phép đầu tiên trong program: `subtract` 3.214; `divide` 3.029; `add` 1.140; `multiply` 488; `greater` 138; các phép tổng hợp bảng 272.
- Hình split: `term_paper/knowledge_rag/artifacts/figures/phase11/finqa_split_distribution.png`.
- Phase 12 giữ nguyên official train/dev/public-test split; private test chỉ dùng inference demo vì không có gold.

## Tiền xử lý và split Phase 12

- Official train/dev/public-test được giữ nguyên và `dev` đổi tên hiển thị thành validation: 6.251/883/1.147 query; private test có 919 query.
- Context dedupe thành 2.789 page document và 86.421 chunk theo đúng locator `text_i`/`table_i`; 14.108 gold evidence đều ánh xạ được.
- Public page group không giao nhau giữa split. Company-year report key vẫn overlap 197/243/93; đây là giới hạn official split và được nêu rõ, không remap hậu nghiệm.
- Private test trùng 303 page với public test, chỉ dùng inference; một query trùng exact public/private được ghi trong duplicate audit với ID phân biệt source.
- 328 khác biệt gold text chỉ do spacing/punctuation; token-level mismatch bằng 0. TEST chưa dùng tuning.

## Mẫu input/output

- ID `ADI/2009/page_49.pdf-1` hỏi interest expense năm 2009; gold execution answer là `3.8` và program gồm hai phép `divide`.
- ID `ABMD/2012/page_75.pdf-1` là câu hỏi so sánh; gold answer `yes`, program kết hợp `multiply` và `greater`, có hai gold evidence item.
- UI/report chỉ hiển thị câu hỏi, bằng chứng ngắn, program và kết quả; không sao chép toàn bộ báo cáo tài chính.

## Nhận xét và giới hạn

- Context bảng và văn bản có thể lặp giữa nhiều QA; thống kê table row/text segment trên example không phải số hàng độc nhất toàn corpus.
- Hệ thống phải đánh giá retrieval và execution/program riêng, vì answer đúng do đoán không chứng minh truy hồi hoặc suy luận đúng.
- Đây là benchmark hỏi đáp báo cáo tài chính, không phải dự báo giá cổ phiếu và không tạo khuyến nghị đầu tư.

## Bằng chứng local

- Audit: `term_paper/knowledge_rag/artifacts/metrics/phase11_data_audit.json`.
- File-level hash: `term_paper/knowledge_rag/artifacts/manifests/raw_manifest.csv`.
- Snapshot/provenance: `term_paper/knowledge_rag/artifacts/manifests/phase11_snapshot_manifest.json`.

