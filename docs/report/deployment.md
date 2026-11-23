# Chương TV3 · Mạng, lưu trữ và triển khai

Tác giả: @pvduc05. Review TV1/TV2; TV4 review API. Trạng thái: khung W1.

## Thiết kế cần giải thích

Topology bốn process, DB/keys riêng; API/HTTPX, timeout/retry/idempotency và limits;
schema SQLite, vote/lock/proposal bền vững, WAL/FULL, atomic apply và sync tuần tự.

## Cài đặt và ví dụ cần bổ sung

Link source/commit `src/network`, `src/storage`, `src/api`, scripts/config;
hướng dẫn máy mới, start/health/stop đúng PID, crash points và recovery.
Ghi phiên bản schema thực tế sau khi các PR W1 thống nhất.

## Bằng chứng và giới hạn

Gắn run T18–T26/T29/T30 và phần T05/T11/T15 phối hợp; hiện **Not run** trong ma trận.
Lưu môi trường và bằng chứng restart/sync; phân biệt health, readiness, quorum.
Ghi giới hạn đo nhiều process trên cùng laptop so với mạng phân tán thật.
