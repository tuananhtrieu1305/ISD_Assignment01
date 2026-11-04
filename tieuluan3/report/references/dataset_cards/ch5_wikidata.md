# Dataset card — Wikidata narrow snapshots

## Nhận dạng và nguồn

- Dataset ID: `ch5_wikidata`.
- Chương/bài toán: Chương 5, nguồn tri thức có cấu trúc cho KG và GraphRAG ở hai miền y khoa–tài chính.
- Nguồn/API chính thức: <https://www.wikidata.org/wiki/Wikidata:Data_access> và `Special:EntityData`.
- Snapshot: truy cập 2026-10-12 bằng User-Agent riêng, có cache, retry/backoff, timestamp, endpoint và revision ID cho từng entity.
- License: CC0 1.0 theo <https://www.wikidata.org/wiki/Wikidata:Copyright>.
- Local: `term_paper/knowledge_rag/data/raw/wikidata`; 3.528.666 byte; 21 file; manifest SHA-256 `35f304194ea037b044f66586f3a60bcebff71af2352eb3264be629b43c63da4b`.

## Phạm vi và schema đo từ snapshot

- Snapshot hẹp gồm đúng 10 entity, chia đều medical 5 và finance 5; không tải full Wikidata dump.
- Medical: diabetes `Q12206`, type-1 diabetes `Q124407`, type 2 diabetes `Q3025883`, insulin `Q50265665`, hyperglycemia `Q271993`.
- Finance: financial statement `Q192907`, annual report `Q699735`, revenue `Q850210`, net income `Q570938`, Apple Inc. `Q312`.
- Tổng cộng 785 property bucket và 2.056 claim trong JSON gốc. Mỗi record index lưu QID, label/description tiếng Anh, endpoint, `lastrevid`, modified time, SHA-256 và domain.

## Revision và phân bố

- Revision ID: Q12206 `2554502707`; Q124407 `2556005597`; Q3025883 `2549752035`; Q50265665 `2555721146`; Q271993 `2549698902`.
- Revision ID: Q192907 `2556173446`; Q699735 `2551742693`; Q850210 `2547192660`; Q570938 `2551809219`; Q312 `2548367127`.
- Q312 có 1.219/2.056 claim nên phân bố lệch mạnh; Phase 13 phải giới hạn predicate/neighbor expansion để một hub không lấn át graph.
- Hình: `term_paper/knowledge_rag/artifacts/figures/phase11/wikidata_claim_distribution.png`.

## Mẫu input/output

- Input acquisition: search term `diabetes mellitus`; entity được khóa là Q12206 qua alias chính xác.
- Output chuẩn hóa: `{qid, label_en, description_en, revision_id, property_count, claim_count}`; JSON gốc vẫn được giữ để Phase 13 trích triple có provenance.
- Ví dụ Q192907 có label `financial statement`, mô tả về hồ sơ chính thức của hoạt động/vị thế tài chính và 70 claim trong revision đã khóa.

## Nhận xét và giới hạn

- Đây là seed snapshot để kiểm định acquisition/provenance, chưa phải graph cuối. Phase 13 mới quyết định predicate, neighbor, entity linking và giới hạn hop.
- Wikidata thay đổi liên tục; mọi kết quả phải gắn revision thay vì giả định dữ liệu “mới nhất”.
- Label/claim do cộng đồng đóng góp có thể thiếu hoặc mâu thuẫn; KG không tự động trở thành ground truth cho câu trả lời y khoa/tài chính.

## Bằng chứng local

- Entity/index cache: `term_paper/knowledge_rag/data/raw/wikidata/`.
- Audit: `term_paper/knowledge_rag/artifacts/metrics/phase11_data_audit.json`.
- File-level hash: `term_paper/knowledge_rag/artifacts/manifests/raw_manifest.csv`.
- Snapshot/provenance: `term_paper/knowledge_rag/artifacts/manifests/phase11_snapshot_manifest.json`.

