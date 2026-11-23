# Khung kiểm thử và thực nghiệm

Chủ trì TV4; TV2 review kết luận consensus, TV3 review môi trường, TV1 validity.
Trạng thái W1: kế hoạch, **chưa có dữ liệu đo**, không có giá trị TPS/latency để báo cáo.

## Phương pháp cần hoàn thiện W4–W5

Theo kế hoạch mục 16–17: baseline, tắt follower/leader, duplicate, partition,
restart/sync, workload và tham số batch/timeout. Ghi seed, warm-up, cửa sổ đo,
số lần lặp, toàn bộ config có hiệu lực, commit, OS/CPU/RAM và phiên bản thư viện.

## Chỉ số và dữ liệu đầu vào

- TPS: số ID tx duy nhất committed trong cửa sổ / số giây cửa sổ; không đếm accepted.
- Latency: từ lần gửi đầu đến quan sát committed trên cùng đồng hồ đơn điệu client;
  báo p50/p95/p99, định nghĩa chính xác tập mẫu và phương pháp percentile khi có script.
- Báo riêng submitted, accepted, committed, rejected và unfinished; giữ run lỗi.
- Consistency: hash mọi height chung, balances/nonces của bốn node; không chỉ so tip height.
- Message count/bytes theo phase và số lần retry, đối chiếu log thô; môi trường cùng
  laptop có giới hạn, không suy ra thông lượng mạng production.

## Bảng kết quả chờ thực chạy

| Kịch bản / run | Seed/config/commit | Committed/rejected/unfinished | TPS / latency | Artifact | Kết quả |
|---|---|---|---|---|---|
| Baseline và fault runs W5 | Chưa có | Chưa đo | Chưa đo | — | Not run |

Bổ sung raw CSV, script tính và biểu đồ có đơn vị, nhãn run/commit, độ biến thiên
khi có lần lặp. Mỗi kết luận phải dẫn run và nêu giới hạn; liên kết [ma trận](../test-matrix.md).
