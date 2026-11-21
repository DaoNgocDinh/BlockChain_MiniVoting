# Thực nghiệm · TV4, phối hợp TV2 và TV3

Các kịch bản, công thức đo và baseline nằm tại mục 16–17 của `docs/ke-hoach.md`.
Chưa có số liệu benchmark ở bản khung. Mỗi lần chạy phải lưu:

- Commit SHA, OS/CPU/RAM, phiên bản Python/Node, config và seed.
- Offered/submitted/committed/rejected/unfinished transactions.
- Commit latency p50/p95/p99 và TPS tính trên khoảng thời gian định nghĩa rõ.
- Hash và trạng thái các node, lỗi và thời điểm fault injection.

Đề xuất thư mục `experiments/runs/<run-id>/` gồm metadata.json, transactions.csv,
nodes.csv và summary.json. Chỉ commit dữ liệu thí nghiệm đã chọn, không commit khóa,
database hoặc log chứa thông tin nhạy cảm. Không tính accepted là committed;
không bỏ các giao dịch chưa hoàn tất khỏi báo cáo để làm đẹp latency/TPS.
