# Mẫu giải thích một biểu đồ output

Đây là template dùng khi đã có dữ liệu thật, không phải nội dung kết quả hiện tại.
Mỗi hình có một record/đoạn phân tích tương ứng; kiểm không bỏ sót hình trong notebook.

## Thông tin bắt buộc

- Figure ID và câu hỏi/phần báo cáo được hỗ trợ.
- Script/hàm tạo hình; CSV/run IDs và hash dữ liệu.
- Trục x, trục y, đơn vị, train/evaluation và mẫu số.
- Ý nghĩa từng đường/cột/vùng sai số.
- Aggregation: raw, moving average K episode, mean/std qua n training seed, hoặc CI.
- Quan sát chính bằng số liệu đo: mức đầu/cuối, chênh lệch, dao động.
- So sánh phù hợp: giữ gì cố định, chỉ đổi yếu tố nào.
- Cách giải thích có cơ sở; điều nào mới là giả thuyết, chưa chứng minh.
- Kết luận vừa đủ và giới hạn: một seed, mô phỏng, không chứng minh hội tụ/nhân quả.

## Gợi ý theo loại hình

Learning curve: nói rõ raw reward khác moving average; trục episode khác step;
epsilon giảm có thể làm đổi train reward. Đường tăng không tự chứng minh policy tốt.

Alpha/exploration comparison: phân biệt chất lượng cuối với tốc độ/độ ổn định học;
không coi mức cao nhất tốt nhất trước khi xem dữ liệu.

Error bars: ghi std giữa training seed hay variability episode trong một run;
không dùng hai đại lượng thay thế nhau, không suy luận ý nghĩa thống kê chỉ từ overlap.

Policy/Q heatmap: ghi state/action và màu xám đại diện Q hoặc action nào; Q là giá trị
chiết khấu ước lượng, không phải trực tiếp profit/step của evaluation.

Robustness: phân biệt policy đóng băng dưới môi trường thay đổi với policy được train
lại; không gán tác dụng cho agent nếu đồng thời thay nhiều yếu tố.
