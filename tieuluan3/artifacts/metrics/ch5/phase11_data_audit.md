# Phase 11 — Báo cáo kiểm định dữ liệu

Ngày khóa snapshot: 2026-10-12. Số liệu chi tiết có máy đọc nằm trong `phase11_data_audit.json`; mọi kích thước và phân bố dưới đây được tính trực tiếp từ file local.

## Kết quả tổng hợp

| Nguồn | Snapshot | Kích thước | Số đo logic chính | License |
|---|---|---:|---|---|
| MedQuAD | `577bd37b96c02d1833b2c9eed2de9f96964e96cb` | 37.183.352 B | 11.274 XML; 47.441 QA; 16.407 answer hiện hữu | CC BY 4.0 |
| FinQA | `0f16e2867befa6840783e58be38c9efb9229d742` | 122.256.362 B | 8.281 public QA có program; 919 private-test QA | MIT |
| Wikidata | 10 revision ID trong snapshot manifest | 3.528.666 B | 10 entity; 785 property bucket; 2.056 claim | CC0 1.0 |

## Kiểm định chất lượng và quyết định

- MedQuAD: 11.274/11.274 XML parse thành công. Số local thấp hơn README upstream 16 QA; báo cáo dùng số local. Có 31.034 answer rỗng và chính sách acquisition khóa `removed_answers_recovered=false`; không crawl URL của ba subset bị gỡ vì bản quyền.
- FinQA: official split được giữ nguyên. Public train/dev/test lần lượt 6.251/883/1.147; private test 919 không có gold đầy đủ. Context lặp theo QA nên thống kê table/text được ghi rõ là số đếm trên example.
- Wikidata: chỉ gọi search API và `Special:EntityData` cho 10 seed entity. Cache lưu 10 search response, 10 entity JSON và một index; không tải dump.
- Raw manifest gồm 11.345 file dữ liệu và có aggregate SHA-256 `b7af4e6c5e5e8bc4bc4d09e8fad05df119ada7a1159438cc467bb1e678dafcb1`.

## Tái lập và bất biến

1. Chạy test parser/provenance trước acquisition.
2. Clone hai repo chính thức ở đúng commit và gọi Wikidata bằng User-Agent đã khai báo.
3. Chạy `python -m term_paper.tools.build_phase11_sources` để audit, tạo manifest và hình phân bố.
4. Chạy `python -m term_paper.tools.verify_phase11` để băm lại toàn bộ raw.

Sau khi `raw_manifest.csv` được phát hành, mọi thay đổi nội dung raw phải tạo snapshot và manifest mới; không được sửa âm thầm tại chỗ.
