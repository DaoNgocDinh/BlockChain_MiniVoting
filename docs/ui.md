# Wireframe dashboard · TV4 W1

Phạm vi: [issue #4](https://github.com/DaoNgocDinh/BlockChain_MiniVoting/issues/4).
Chủ trì @DaoNgocDinh; review API @pvduc05, diễn giải consensus @germnguyen,
đối chiếu dữ liệu core @CaoDucDao. Trạng thái: **sẵn sàng review, chưa được nhóm thông qua**.

## Chạy và review

Tại `frontend`, dùng Node 24.21.0 (`.nvmrc`), `npm ci`, `npm run dev`.
Mở URL Vite hiển thị. Chọn từng màn ở menu; mọi điều khiển dùng được bằng Tab,
Enter/Space và phím mũi tên của select. Hash có thể mở đầy đủ và chọn để sao chép.
Kiểm tra ở desktop, 375px và ngang điện thoại; bảng dài cuộn trong khung.

- **Kết nối thật** là mặc định: chỉ màn mạng đọc GET `/health` và `/status`
  của bốn node qua proxy local. Timeout 3 giây; đọc lúc mở màn/nhấn Kiểm tra lại,
  không polling nền ở W1. Có nguồn node và thời gian hoàn tất quan sát. Khi kiểm tra lại,
  xóa snapshot cũ để tránh hiển thị online từ dữ liệu cũ.
- **Wireframe mẫu**: nhãn cố định trên mọi màn; dữ liệu bố cục chỉ nằm trong module
  `src/wireframe.js` và component mẫu. Chuyển sang mẫu unmount màn thật và hủy request
  đang chờ. Không có fallback từ lỗi API sang dữ liệu mẫu. Request đã gửi có thể đã tới server.
- Màn ledger thật chưa tích hợp hiển thị lời giải thích và nút mở wireframe.
  Đây là wireframe W1, chưa phải dashboard tích hợp W2/W3. Không có POST, ký phiếu,
  nút commit, private key validator hoặc chứng chỉ giả có chữ ký.

## Bố cục và hợp đồng trường

Menu trái trên desktop, lưới menu trên điện thoại; tiêu đề → nguồn dữ liệu →
điều khiển kịch bản → nội dung → chú thích. Dùng màu kèm nhãn chữ, focus rõ,
heading theo cấp, label cho select, caption cho bảng và liên kết bỏ qua menu.

| Màn | Thành phần wireframe | Nguồn API dự kiến khi tích hợp |
|---|---|---|
| Mạng validator | 4 node, vai trò, health, consensus_ready; committed_height, target_height, phase, sync_state, tip_hash mẫu; PREPARE/COMMIT theo round | `/health`, `/status`, `/consensus/{height}` |
| Giao dịch | tx_id, status, observed_node_id, height/block_hash có thể null, reason; select 5 trạng thái | `/transactions/{tx_id}`, phản hồi POST `/transactions` từ ví TV1 |
| Tài khoản | address, balance nguyên, nonce, committed_height, tip_hash của snapshot | `/accounts/{address}` |
| Block explorer | height, proposer_id, timestamp_ms, transaction_count, block_hash, prev_hash, state_hash, hướng đọc certificate | `/blocks`, `/blocks/{height}` |
| Certificate | context version/chain/height/view/COMMIT/hash, danh tính signer, vị trí chữ ký và kết quả xác minh từ node | `FinalizedBlock.certificate` hoặc `ConsensusView.certificate` |
| Timeline | seq, observed_at_ms, peer_id, sender_id, phase, block_hash, outcome, reason | `ConsensusView.events` |

Block list dự kiến tăng theo height, `from_height` bao gồm, limit mặc định 20 (1–50).
Height 0 dùng genesis, `timestamp_ms=null`; block dương dùng proposal + certificate.
W1 chỉ review bố cục và quy tắc trang, chưa thực hiện truy vấn/phân trang.
Node nguồn/timestamp không được lấy từ dữ liệu mẫu khi ở chế độ thật.

## Quy tắc trạng thái cần nhóm xác nhận

| Trạng thái | Cách trình bày và giới hạn |
|---|---|
| accepted / HTTP 202 | Đã nhận cục bộ; không phải trạng thái committed, không đổi balance |
| pending | Trong mempool cục bộ, height/block_hash null |
| proposed | Trong proposal; có height/hash nhưng chưa ghi sổ |
| committed | Đọc được bản ghi đã chốt kèm certificate; không suy từ timer hoặc count |
| rejected | Dấu vết loại tại node, kèm reason; không kết luận toàn mạng |
| local-unknown | Node không biết ID; không đổi thành rejected |
| COMMITTING, 2 COMMIT | Chờ chữ ký thứ ba hợp lệ, chưa chốt |
| STALLED | Hiển thị pha kẹt và count cục bộ; không giảm quorum hay mở khóa |
| LEADER_UNAVAILABLE | Chờ leader cố định; không hứa tự bầu leader |
| SYNCING | Health ready=false; ledger chỉ đọc snapshot chốt an toàn nếu có |
| DECIDED | Mẫu thể hiện điều kiện chốt, không tự xác minh proof ở trình duyệt |
| 503 CONSENSUS_NOT_READY | Hiện mã lỗi, để trống ledger; health vẫn có thể phản hồi |
| NETWORK_OR_INVALID_RESPONSE | Không đọc được API; có thể là lỗi mạng, timeout hoặc dữ liệu sai, không khẳng định process đã chết |

Timeline phân biệt valid, invalid, duplicate, buffered, equivocation. Sender trên
event invalid là danh tính **khai báo**. Chỉ unique valid sender đúng context tăng
quorum; event buffered/duplicate không tự tăng count. Events có thể rỗng sau restart.
Peer giao nhận và sender ký là hai trường riêng, phải tách khi tích hợp.

## Điểm mở giữa các PR, cần xử lý trước W2

Căn cứ W1: kế hoạch mục 7–11, 15, 17 và đề xuất [PR #27](https://github.com/DaoNgocDinh/BlockChain_MiniVoting/pull/27).
[PR #25](https://github.com/DaoNgocDinh/BlockChain_MiniVoting/pull/25) và
[PR #28](https://github.com/DaoNgocDinh/BlockChain_MiniVoting/pull/28) đang review;
wireframe không tuyên bố các đề xuất này đã merge hoặc đồng bộ.

- TV3: xác nhận `NodeStatus`, `TxLookup`, `BlockRecord`, `ConsensusView`, envelope
  `error.code` theo #27. Adapter W1 đọc thêm `detail.code` của FastAPI scaffold trên main.
  Adapter thật W1 mới dùng health/status, không phụ thuộc
  toàn bộ schema ledger của #28. Trên main hiện tại status trả 503.
- TV3/TV2: #28 mô tả hạn mức 64 KiB transaction/1 MiB body/50 tx/1000 mempool;
  #27 đề xuất 4 KiB transaction-vote/512 KiB proposal-finalized/1024 mempool.
  Chốt một bộ trước W2; W1 không thêm form submit phụ thuộc các hạn mức khác nhau.
- TV2: xác nhận enum/phase, prepared/commit counts, nguồn dữ liệu certificate,
  STALLED/LEADER_UNAVAILABLE và việc không suy commit từ ba dòng hiển thị.
- TV1: xác nhận tên trường address/proposer, số nguyên an toàn cho JavaScript,
  genesis/hash và định dạng giao dịch từ ví/CLI.

## Checklist review trên PR

- [ ] TV3 review sáu màn và bảng endpoint/trường, lỗi 503, source node, nullable fields.
- [ ] TV2 review accepted ≠ committed, quorum 3 danh tính, hai COMMIT còn chờ,
  fixed leader, trạng thái stall/sync và sender khai báo.
- [ ] TV1 đối chiếu account/block/genesis và ranh giới ví với validator keys.
- [ ] Cả nhóm xem mẫu rồi chuyển về thật, xác nhận lỗi API không nhận mẫu thay thế.

Các ô này cần phản hồi thực của thành viên; chỉ merge sau review theo CONTRIBUTING.
