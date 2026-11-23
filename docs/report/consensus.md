# Chương TV2 · Đồng thuận

Tác giả: @germnguyen. Review TV1/TV3. Trạng thái: khung W1, chờ tác giả viết.

## Thiết kế cần giải thích

n=4, q=3, tối đa một Byzantine; giao quorum; PROPOSE/PREPARE/COMMIT,
mọi validator kể cả leader bỏ phiếu; context ký, unique sender, prepared/lock,
persist-before-send, early votes, timeout/retry và state machine.

## Cài đặt và ví dụ cần bổ sung

Link đặc tả đã thống nhất, source/commit `src/consensus`, transport giả và lịch
messages có seed; phân biệt local counts với certificate được verify toàn bộ.

## Bằng chứng và giới hạn

Gắn run T10–T17, T19/T22/T29 và message counts thật; hiện **Not run**.
Tách safety/liveness. Fixed leader lỗi hoặc split vote có thể stall; không phải
PBFT đầy đủ, không khẳng định chống hai Byzantine hoặc view change tự động.
