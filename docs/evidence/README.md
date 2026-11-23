# Bằng chứng kiểm tra giao diện W1

Ngày bàn giao: 23/11/2026. Phạm vi issue #4, nhánh `feat/tv4-w1-wireframe`.
Ảnh là **wireframe mẫu**, không phải block/certificate/log thật.

- [Desktop · mạng validator](w1-network-desktop.jpg): bốn thẻ, nguồn mẫu,
  trạng thái COMMITTING và 2/3 COMMIT còn chờ.
- [Điện thoại · giao dịch pending](w1-transaction-mobile.jpg): viewport 375×812,
  bố cục một cột, nguồn mẫu và accepted chưa committed.

Đã kiểm bằng trình duyệt local qua Vite:

1. Mặc định kết nối thật; bốn backend không chạy hiện lỗi API và để trống readiness.
2. Chuyển sang mẫu; duyệt sáu màn và sáu round PREPARING/COMMITTING/STALLED/
   LEADER_UNAVAILABLE/SYNCING/DECIDED, chọn đủ năm trạng thái giao dịch.
3. Kiểm bốn màn explorer/account/certificate/timeline tại 375×812; chiều rộng
   document bằng clientWidth (360px sau scrollbar), không tràn ngang toàn trang.
4. Kiểm timeline ngang 812×375: document/clientWidth cùng 797px; bảng cuộn nội bộ.
5. Trở về kết nối thật: lỗi API hiện lại, không còn số liệu mẫu. Reset viewport.

Môi trường frontend: Node 24.21.0, npm 12.2.1. Các lệnh `npm ci --no-audit --no-fund`,
`npm run lint`, `npm test` (4 test adapter) và `npm run build` đã chạy đạt.
Đối chiếu tự động có đủ 30 ID T01–T30 duy nhất, đều Not run và 23 liên kết tài liệu local hợp lệ.
Trong sandbox Windows, Vite gặp EPERM realpath; chạy kiểm tra ngoài sandbox đạt.
Khi cài lại lúc dev server đang chạy, esbuild bị khóa; đã dừng dev server và cài lại đạt.

Chưa chạy bốn backend, ledger end-to-end, consensus/fault hoặc T01–T30. Lỗi 503
hiện tại và đề xuất v1 được kiểm qua test adapter với response giả lập tách khỏi UI thật.
Review TV2/TV3 và nghiệm thu sau merge vẫn đang chờ.
