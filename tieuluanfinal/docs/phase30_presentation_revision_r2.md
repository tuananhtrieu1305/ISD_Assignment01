# Revision trình bày Ch5 r2 — không đổi kết quả

Visual QA Phase30 giữ nguyên toàn bộ hình và manuscript baseline, đồng thời phát hiện:

- Nhãn tiếng Việt ngoài plot của hình tổng quan dataset cũ bị lỗi font.
- Nhãn ablation cũ quá sát nhau; sơ đồ schema cũ chỉ có các ô loại node, không có cạnh.
- Hình lỗi cũ lọc riêng public TEST, trong khi đoạn văn lấy số từ JSON aggregate cộng cả
  TEST và challenge. Không có mâu thuẫn metric khi tách đúng phạm vi.

Đối chiếu saved `phase15_error_analysis.csv` cho TEST medical62 và finance1.147 query,
challenge8 query/miền. Entity-linking TEST là0/1.053, challenge8/8; tổng8/1.061 khớp
nguyên JSON `error_category_counts`. Không sửa JSON, CSV, query, prediction, model hay
evaluator, không chạy inference. Bản r2 sửa phạm vi câu diễn giải, không đổi benchmark.

Bốn hình PNG300dpi/SVG mới ở `artifacts/figures/phase30/r2/`, cùng ba hình Phase30 đã đạt QA.
Manuscript `report/sections/v3/ch05_knowledge_rag_r2.md` và generation manifest riêng
`artifacts/manifests/phase30/revisions/presentation_r2/report_generation.json` giữ link
supersedes tới r1. Active pointer đổi sang r2; r1 không bị ghi đè.

Trong graph_schema lịch sử, dòng bảng ASKS_ABOUT nói kế thừa gold document nhưng mục
chống rò rỉ và extractor thực tế dùng longest exact normalized phrase từ question text.
Đã đọc extractor: fallback gold document chỉ cấp provenance; việc chọn anchor chỉ dựa
question text. Giữ file cũ và nêu rõ điểm diễn đạt không nhất quán ở caption mới;
không tái dựng graph/TEST để sửa lịch sử. Diagram r2 chỉ hiển thị subset cạnh có vai trò
truy hồi, không ngụ ý mọi node đều có SAME_AS.

Demo compact duyệt toàn corpus do bundle không còn split; benchmark lịch sử giới hạn
candidate theo split. Graph free-question cũng khác query-ID/full adjacency cũ. Không
đồng nhất output/timing demo với phép đánh giá TEST đã khóa.
