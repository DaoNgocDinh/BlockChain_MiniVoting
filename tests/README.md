# Kiểm thử

Mỗi người viết test cho module của mình; TV4 điều phối ma trận và regression.

- `test_health.py`: kiểm tra danh tính tiến trình và phân biệt health với consensus.
- `unit/`: TV1 và TV2 bổ sung các test hàm thuần.
- `simulation/`: TV2 bổ sung transport giả và sự kiện trễ/lặp/đảo thứ tự.
- `integration/`: TV3 và TV4 bổ sung kiểm thử bốn tiến trình thật.
- `fault/`: crash, restart, partition, forged/duplicate votes.

Các kịch bản T01–T30 và ngưỡng nghiệm thu nằm trong `docs/ke-hoach.md`, mục 15.
Khung ban đầu chưa kiểm chứng bất kỳ bảo đảm đồng thuận nào.
