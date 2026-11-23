# Chương TV4 · Dashboard và điều phối kiểm thử

Tác giả: @DaoNgocDinh. Review TV3 về API, TV2 về diễn giải consensus.
Trạng thái W1: đã có wireframe để review, chưa tích hợp ledger/consensus thật.

## Thiết kế và cài đặt W1

[Sáu màn wireframe](../ui.md) tách nguồn mẫu khỏi kết nối health/status thật,
hiển thị nguồn node/thời điểm, accepted/pending/proposed/committed/rejected/local-unknown,
snapshot tài khoản đã chốt, signer/certificate và timeline outcomes.
Frontend chỉ quan sát; không giữ validator key, ký phiếu hoặc chốt block.

## Phần cần viết trong W2–W4

API adapter theo schema được nhóm thông qua; ví/CLI của TV1, polling và xử lý
loading/offline/503; explorer/timeline thật, giới hạn events và stale snapshots.
Link source/commit, ảnh màn hình và kịch bản từ submit tới committed tại node nguồn.

## Bằng chứng và giới hạn

[Ma trận](../test-matrix.md) có T01–T30, chủ trì/review và evidence yêu cầu.
T27/T28 hiện **Not run**; demo mẫu không là bằng chứng consensus hay test T28.
Kết quả kiểm tra W1 và ảnh UI ghi tại PR bàn giao; kết quả W3/W4 bổ sung theo run.
