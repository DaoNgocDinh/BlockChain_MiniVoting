# Khung báo cáo MiniVoting

W1 chỉ lập khung theo kế hoạch mục 20.1; chưa có số liệu hoặc kết luận nghiệm thu.
Tham khảo 25–40 trang nội dung chính nếu giảng viên không có mẫu riêng.
TV4 tổng hợp, từng người tự viết và chịu trách nhiệm phần mình.

| Chương | Nội dung, người viết và tài liệu nguồn | Bằng chứng cần bổ sung |
|---|---|---|
| 1. Giới thiệu | Cả nhóm; TV4 tổng hợp bài toán, mục tiêu, phạm vi bốn validator và phân công | Issue/PR, yêu cầu và bảng đóng góp thực |
| 2. Cơ sở lý thuyết | TV1: hash/chữ ký/blockchain; TV2: RSM, Byzantine, quorum, so sánh Raft/PBFT vừa đủ | Tài liệu tham khảo chính thức, chứng minh giao quorum |
| 3. Phân tích và thiết kế | TV1: dữ liệu; TV2: protocol/state machine; TV3: kiến trúc/API/persistence | Phiên bản hợp đồng đã thống nhất, sơ đồ và public fixtures |
| 4. Cài đặt | Bốn phần độc lập: [TV1 core](core.md), [TV2 consensus](consensus.md), [TV3 deployment](deployment.md), [TV4 dashboard](dashboard.md) | Source tại commit bàn giao, ví dụ và test từng module |
| 5. Kiểm thử và thực nghiệm | [TV4 điều phối đánh giá](evaluation.md); TV2 review kết luận consensus; TV3 review môi trường | [T01–T30](../test-matrix.md), raw CSV, metadata, seed/config và scripts |
| 6. Kết luận | Cả nhóm: đạt/chưa đạt có căn cứ, giới hạn, bài học và hướng mở rộng | Đối chiếu mục tiêu với evidence; không hứa view change chưa cài |
| Phụ lục | TV3/TV4: cài/chạy/dừng, config, API, public test vectors, đóng góp, demo | Link release, hướng dẫn máy mới, video và lịch sử PR |

## Quy tắc viết và tổng hợp

Mỗi phần có: mục tiêu → thiết kế → cài đặt thực tế → kiểm thử/evidence → giới hạn.
Phân biệt thiết kế đề xuất, code đã có và hành vi đã kiểm. Không chép source dài
thay giải thích. Link đến commit/file/artifact và nguồn tham khảo cho khẳng định.
Không gọi hệ thống là PBFT đầy đủ hoặc cam kết phục hồi leader tự động.

Tại W1, [wireframe](../ui.md), ma trận và khung này sẵn sàng review; protocol,
core/API còn ở PR riêng. Tất cả T01–T30 là Not run trong ma trận này.

## Cổng tổng hợp W5/W6

- [ ] Mỗi tác giả cập nhật chương của mình, reviewer xác nhận phần liên quan.
- [ ] Từng claim safety/liveness gắn evidence và giả định; ghi giới hạn fixed leader.
- [ ] Chương thực nghiệm khớp CSV, công thức, đơn vị và config thực chạy.
- [ ] Bảng đóng góp theo module/PR/test/tài liệu có nguồn kiểm tra được.
- [ ] Source, docs, slide và demo dùng cùng commit release đã được nhóm nghiệm thu.
