# Rollback và phục hồi REORG

Không git reset/clean hoặc checkout cả cây. Dừng web runner trước thao tác source. Giữ nguyên checkpoint khoa học/TEST seals và user changes.

Original mapping: Phase2 canonical_map.json cộng Phase3 preservation_overrides.json; baseline_path sau overlay trỏ đúng byte gốc. Notebook/code gốc ở provenance/originals; web trước sửa ở provenance/phase3_originals. Các bản dựng root dist cũ được lưu trong tieuluan3/provenance/build_history/root-dist-before-reorg.zip, SHA/count trong phase3/build_history_backup.json. Archive này local-only, không dùng làm active source.

Muốn khôi phục, giải vào một thư mục revision mới trong workspace và kiểm manifest/hash, không ghi đè source đang dùng. Staging Phase1 đã được dọn sau gate, file thực của nó đã ở các project canonical/provenance; commit/blob và manifest phục hồi Phase1 vẫn giữ. Hai web chưa commit có backup_manifest riêng. Không xóa raw/checkpoint unique hoặc nested Git metadata.

Tái tạo runtime views: scripts/materialize_assignment.py, gồm recipe Phase2 + source overlay Phase3; cung cấp đúng file data/model bị ignore trước. Source overlay chỉ đổi vị trí, không đổi logical namespace/hash. Render dùng scripts/render_project.py và serving archive versioned; sửa backend source cần build deployment revision mới. Không tự redeploy/reset seal để phục hồi layout.
