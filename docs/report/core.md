# Chương TV1 · Lõi blockchain

Tác giả: @CaoDucDao. Review TV2; TV3 về persistence. Trạng thái: khung W1, chờ tác giả viết.

## Thiết kế cần giải thích

Genesis và registry; Transaction/Block/AccountState; amount nguyên, nonce,
canonical bytes, hash, miền ký; thực thi tuần tự trên state tạm và atomic apply.

## Cài đặt và ví dụ cần bổ sung

Link source/commit `src/core`, public genesis/vectors, ví CLI và đường tx → block.
Giải thích validation, tamper/replay/double spend và snapshot balance/nonce.

## Bằng chứng và giới hạn

Gắn run T01–T09, T23/T26 tương ứng; tất cả hiện **Not run** trong ma trận W1.
Ghi actual/expected, ảnh hưởng state và phần chưa cài. Không đưa private key vào báo cáo.
