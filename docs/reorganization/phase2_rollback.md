# Rollback REORG Phase2

Không git reset/clean/checkout cả cây. Dừng runner do migration sở hữu trước. Đọc canonical_map.json và relocation journal; baseline_path trỏ byte gốc, old_path là đường dẫn logic cũ. Nếu phục hồi layout cũ, copy baseline vào một thư mục revision riêng, kiểm SHA256/bytes rồi mới chọn entry point; không ghi đè source hiện hành hoặc file người dùng.

Staging và backup Phase1 vẫn có; commit/blob/OID trong restoration/supplementary manifests có thể lấy lại code đã commit. Hai web chưa commit và nested metadata phải lấy từ backup_manifest/bản provenance, không thể dựa Git root để khôi phục. Scientific raw/checkpoint unique không xóa. Runtime view tái tạo được từ runtime_view_map, dùng source/hash hiện hành (có CRLF representation adapter A06); không dùng map_base cũ để ghi đè revision.
