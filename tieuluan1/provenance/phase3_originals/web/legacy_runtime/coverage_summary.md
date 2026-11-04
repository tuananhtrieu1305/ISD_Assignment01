# Coverage summary — Phase 6

Đo ngày 2026-10-06 bằng `python -m trace --count --missing --summary` trên 12 test trong `term_paper/deployment/tests/`.

| Module triển khai | Executable lines | Coverage |
|---|---:|---:|
| `app/model_service.py` | 159 | 96% |
| `app/schemas.py` | 98 | 82% |
| `app/server.py` | 134 | 75% |
| **Tổng có trọng số** | **391** | **85,3%** |

Các file `.cover` cùng thư mục lưu dấu dòng đã chạy/chưa chạy. Mức tổng hợp chỉ tính ba module deployment, không gộp thư viện chuẩn, dependency, lớp model scratch đã được kiểm thử ở Phase 3–5 hoặc bản thân test.
