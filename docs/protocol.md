# Đặc tả Giao thức Đồng thuận MiniVoting (PBFT-Inspired Consensus Protocol)

- **Mã tài liệu:** `TV2-W1-PROTOCOL`
- **Người phụ trách:** TV2 · Nguyễn Minh Đức (@DucNguyen)
- **Người thẩm định (Reviewers):** TV1 (Core), TV3 (Network/Storage), TV4 (Frontend/Evaluation)
- **Phiên bản:** 1.0 (Draft Tuần 1)
- **Tình trạng:** Chờ review nội bộ nhóm

---

## 1. Tổng quan và Định vị Giao thức

Giao thức này quy định cơ chế đồng thuận đạt sự nhất quán giữa các validator trong hệ thống blockchain phân tán `BlockChain_MiniVoting`. Giao thức dựa trên mô hình ba pha lấy cảm hứng từ PBFT (Castro & Liskov, 1999) gồm: **PROPOSE → PREPARE → COMMIT**.

### Tuyên bố phạm vi và giới hạn (Scope & Boundary)
1. **PBFT-Inspired (Không phải PBFT đầy đủ):** Bản lõi (Core/MVP) sử dụng **Leader cố định (`node1`)**. Giao thức không cài đặt thuật toán đổi Leader tự động (*View Change*) khi Leader gặp sự cố.
2. **Ưu tiên Tuyệt đối cho Safety (Tính an toàn):** Hệ thống chấp nhận **hy sinh Liveness (dừng tiến triển)** khi Leader offline hoặc mạng bị chia phiếu, nhằm bảo vệ tuyệt đối tính nhất quán của sổ cái (không rẽ nhánh / fork, không tiêu đúp / double-spending).

---

## 2. Mô hình Hệ thống và Mô hình Lỗi (System & Fault Model)

### 2.1 Thành phần mạng (Topology & Identity)
- **Mạng có cấp quyền (Permissioned):** Số lượng validator cố định là $n = 4$, được định danh tĩnh trong khối khởi tạo (`genesis.json`):
  - `node1`: Leader đề xuất khối kiêm Validator.
  - `node2`, `node3`, `node4`: Các Validator (Followers).
- **Định danh bằng khóa mật mã:** Mỗi validator sở hữu một cặp khóa bất đối xứng Ed25519 riêng biệt. Danh sách Public Key của 4 node được công bố và chốt cứng từ Genesis.
- **Kênh truyền:** Mạng bất đồng bộ có điều kiện (*Partial Synchrony*). Thông điệp có thể bị trễ, xáo trộn thứ tự hoặc mất tạm thời, nhưng được bảo đảm truyền tới đích sau một khoảng thời gian hữu hạn nhờ cơ chế Timeout và Retry.

### 2.2 Mô hình lỗi Byzantine (Byzantine Fault Tolerance - BFT)
- Hệ thống áp dụng định lý BFT cổ điển:
  $$n \ge 3f + 1$$
- Với $n = 4$, số lỗi Byzantine tối đa mà hệ thống chịu được là:
  $$f = \left\lfloor \frac{4 - 1}{3} \right\rfloor = 1$$
- **Hành vi lỗi trong phạm vi bảo đảm ($f \le 1$):**
  - Một validator rớt mạng, sập nguồn hoặc treo tiến trình (Crash Fault).
  - Một validator bị trễ mạng nghiêm trọng, drop gói tin.
  - Một validator gửi thông điệp rác, giả mạo dữ liệu, sai chữ ký.
  - Một validator có hành vi đối kháng gửi 2 phiếu khác nhau (*Equivocation*).

---

## 3. Lý thuyết Quorum và Bất biến An toàn (Quorum Mathematics & Safety Invariants)

### 3.1 Toán học Quorum
- Ngưỡng Quorum chốt là:
  $$q = 3 \quad \left(\text{tức } \frac{3}{4} \text{ tổng số validator}\right)$$
- Xét hai tập Quorum bất kỳ $Q_1$ và $Q_2$ (với $|Q_1| = 3$ và $|Q_2| = 3$):
  $$|Q_1 \cap Q_2| \ge |Q_1| + |Q_2| - n = 3 + 3 - 4 = 2$$
- **Hệ quả cốt lõi:** Hai Quorum bất kỳ luôn **giao nhau ít nhất 2 validator**.
- Với giả định tối đa $f = 1$ node Byzantine, số validator trung thực trong phần giao luôn thỏa mãn:
  $$\text{Số validator trung thực} \ge 2 - f = 2 - 1 = 1$$
  $\Rightarrow$ **Luôn tồn tại ít nhất 1 validator trung thực nằm ở phần giao giữa hai Quorum bất kỳ.**

### 3.2 Bất biến An toàn (Safety Invariants)

1. **Bất biến 1 (Quy tắc cấm ký hai lần - No Double-Signing):**
   Một validator trung thực không bao giờ ký hai thông điệp có nội dung khác nhau cho cùng một ngữ cảnh (*Context*):
   $$\text{Context} = \langle \text{chain\_id}, \text{height}, \text{view}, \text{phase} \rangle$$
2. **Bất biến 2 (Bảo vệ tính toàn vẹn của chuỗi - Fork-Free):**
   Nhờ Bất biến 1 và tính chất giao Quorum, không thể tồn tại hai khối khác nhau $B \ne B'$ cùng đạt đủ $q=3$ chữ ký COMMIT tại cùng một `height`. Chuỗi sổ cái là duy nhất và tuyến tính.
3. **Bất biến 3 (Không đảo ngược trạng thái - Finality Immutability):**
   Khi một khối đã đạt `CommitCertificate` hợp lệ (gồm đủ 3 chữ ký COMMIT hợp lệ), khối đó được coi là chốt vĩnh viễn (*Finalized*), không bao giờ bị hoàn tác (reorg) hay thay thế.

---

## 4. Chi tiết Giao thức Ba Pha (Three-Phase Consensus Protocol)

Mọi validator (kể cả Leader `node1`) đều phải tham gia quy trình bỏ phiếu PREPARE và COMMIT.

```
       LEADER (node1)                               FOLLOWERS (node2, 3, 4)
             │                                                 │
             │─────── PROPOSE(Block) ─────────────────────────>│  (Pha 1: Đề xuất)
             │                                                 │
             │<────── PREPARE(block_hash) ────────────────────>│  (Pha 2: Thống nhất thứ tự)
             │   (Broadcast all-to-all, thu thập đủ 3/4 phiếu)  │
             │                                                 │
             │<────── COMMIT(block_hash) ─────────────────────>│  (Pha 3: Cam kết chốt sổ)
             │   (Broadcast all-to-all, thu thập đủ 3/4 phiếu)  │
             │                                                 │
             ▼                                                 ▼
     [Ghi SQLite: Block + Certificate]                 [Ghi SQLite: Block + Certificate]
```

### 4.1 Pha 1: PROPOSE (Đề xuất khối)
- **Chủ thể:** Duy nhất **Leader (`node1`)**.
- **Điều kiện kích hoạt:**
  - Leader nhận giao dịch hợp lệ từ client/mempool.
  - Khối trước đó tại `height - 1` đã được chốt (hoặc bắt đầu từ Genesis ở `height = 1`).
- **Quy trình xử lý tại Leader:**
  1. Chọn danh sách giao dịch từ mempool.
  2. Thực thi thử tuần tự các giao dịch trên bản sao trạng thái tài khoản để tính `state_hash` và `tx_list_hash`.
  3. Đóng gói Header: `height`, `prev_hash`, `timestamp_ms`, `proposer_id`, `state_hash`, `tx_list_hash`.
  4. Tính `block_hash = SHA256(canonical_bytes(Header))`.
  5. Leader ký đề xuất: `proposal_sig = Sign(leader_private_key, block_hash)`.
  6. **Ghi đĩa trước (Persist-Before-Send):** Leader lưu `proposal` vào SQLite.
  7. Broadcast thông điệp `PROPOSE` kèm toàn bộ dữ liệu khối cho tất cả các node.

### 4.2 Pha 2: PREPARE (Xác thực và Khóa thứ tự)
- **Chủ thể:** **Tất cả các Validator (kể cả Leader)**.
- **Quy trình tiếp nhận và thẩm định tại Validator $V_i$:**
  1. **Kiểm tra cơ sở:** Đúng `protocol_version`, đúng `chain_id`, đúng `view = 0`.
  2. **Kiểm tra Proposer:** `proposer_id` phải là `node1` và chữ ký proposal hợp lệ.
  3. **Kiểm tra chuỗi:** `height` phải bằng `current_height + 1`; `prev_hash` phải khớp với hash khối chốt gần nhất.
  4. **Kiểm tra nghiệp vụ (State verification):** Tự thực thi lại danh sách giao dịch, đối chiếu `state_hash` và `tx_list_hash`. Nếu sai lệch $\rightarrow$ Từ chối và ghi log `REJECT`.
  5. **Kiểm tra Khóa bền vững:** $V_i$ chưa từng ký một `block_hash` nào khác tại `height` này.
- **Bỏ phiếu:**
  1. $V_i$ tạo thông điệp vote `PREPARE` với `block_hash`.
  2. **Persist-Before-Send:** Ghi phiếu bầu của mình vào SQLite bảng `consensus_votes`.
  3. Broadcast thông điệp `PREPARE` tới toàn bộ $n=4$ node.
- **Tạo Prepared Certificate:**
  - Mỗi node duy trì một bộ thu thập phiếu (`VoteSet`).
  - Khi thu thập đủ $\ge 3$ phiếu `PREPARE` hợp lệ, từ các validator khác nhau, có cùng `block_hash` tại `height` hiện tại $\Rightarrow$ Tạo thành **`PreparedCertificate`**.
  - Node tiến hành **Khóa (Lock)** vào `block_hash` này.

### 4.3 Pha 3: COMMIT (Cam kết chốt vào sổ cái)
- **Chủ thể:** **Tất cả các Validator** (chỉ thực hiện sau khi đã sở hữu `PreparedCertificate`).
- **Quy trình xử lý tại Validator $V_i$:**
  1. Sau khi đạt trạng thái *Prepared*, $V_i$ tạo thông điệp vote `COMMIT` cho `block_hash` đã khóa.
  2. **Persist-Before-Send:** Ghi phiếu `COMMIT` của mình vào SQLite.
  3. Broadcast thông điệp `COMMIT` tới toàn bộ $n=4$ node.
- **Tạo Commit Certificate và Chốt sổ (Finalization):**
  - Khi node thu thập đủ $\ge 3$ phiếu `COMMIT` hợp lệ, từ các validator khác nhau, cùng `block_hash` tại `height` hiện tại $\Rightarrow$ Tạo thành **`CommitCertificate`**.
  - **Commit nguyên tử (Atomic DB Transaction):**
    - Ghi dữ liệu Block vào bảng `blocks`.
    - Ghi `CommitCertificate` vào bảng `certificates`.
    - Cập nhật số dư (balance) và nonce của các tài khoản vào bảng `accounts`.
    - Xóa các giao dịch đã chốt khỏi mempool.
    - Cập nhật `current_height = current_height + 1`.
  - Node phát sự kiện đã chốt và sẵn sàng tiếp nhận `height` tiếp theo.

---

## 5. Cấu trúc Thông điệp Chuẩn hóa (Message Specification)

Tất cả các thông điệp đồng thuận phải tuân theo cấu trúc Pydantic nghiêm ngặt, được chuẩn hóa (`canonical_bytes`) trước khi băm và ký:

### 5.1 Cấu trúc Thông điệp Bỏ phiếu (Vote Message)
Áp dụng chung cho cả pha `PREPARE` và `COMMIT`:

```json
{
  "protocol_version": 1,
  "chain_id": "minivoting-testnet-1",
  "height": 1,
  "view": 0,
  "phase": "PREPARE", 
  "block_hash": "a5c7f8...64_hex_chars...",
  "sender_id": "node2",
  "signature": "3b8e21...128_hex_chars..."
}
```

*Ghi chú:*
- `phase`: Chỉ nhận giá trị `"PREPARE"` hoặc `"COMMIT"`.
- Chữ ký `signature` được tính bằng thuật toán Ed25519 trên byte chuẩn hóa của thông điệp **sau khi đã bỏ qua trường `signature`**:
  $$\text{signature} = \text{Sign}_{SK}(\text{canonical\_bytes}(\text{Vote} \setminus \{\text{signature}\}))$$

### 5.2 Cấu trúc Commit Certificate
`CommitCertificate` không được tính vào `block_hash` nhằm tránh hiện tượng phụ thuộc vòng (circular dependency):

```json
{
  "height": 1,
  "view": 0,
  "block_hash": "a5c7f8...64_hex_chars...",
  "signatures": {
    "node1": "sig_node1_hex...",
    "node2": "sig_node2_hex...",
    "node3": "sig_node3_hex..."
  }
}
```

---

## 6. Cơ chế Bền vững và Khóa (Durable Locks & Persist-Before-Send)

### 6.1 Nguyên tắc Persist-Before-Send
1. Mọi validator tuyệt đối **không được phát thông điệp mạng trước khi hoàn tất ghi đĩa (SQLite)**.
2. Trình tự bắt buộc:
   $$\text{Tạo Vote} \longrightarrow \text{Ghi SQLite thành công} \longrightarrow \text{Gọi HTTP Transport Broadcast}$$
3. **Mục đích:** Nếu tiến trình bị sập nguồn (Crash) ngay sau khi gửi hoặc trong khi gửi, khi khởi động lại, node đọc dữ liệu từ SQLite và biết chính xác mình đã bỏ phiếu cho giá trị nào, ngăn chặn hoàn toàn việc vô tình ký giá trị thứ hai.

### 6.2 Khóa bền vững (Durable Lock)
- Khi một node phát `PREPARE` hoặc đạt `PreparedCertificate` cho khối $B$ ở `height` $h$, biến khóa `locked_block_hash = B` được lưu bền vững vào bảng trạng thái.
- Node sẽ kiên quyết từ chối mọi khối khác $B' \ne B$ tại `height` $h$, bất kể nhận được bao nhiêu yêu cầu.

---

## 7. Chính sách Timeout và Retry (Consensus Timeout & Retry Policy)

### 7.1 Ba bộ đếm thời gian (Timers)

| Bộ đếm (Timer) | Thời gian mặc định | Ngữ cảnh kích hoạt | Hành động khi hết hạn (On Timeout) |
|---|---|---|---|
| `PROPOSAL_TIMEOUT` | 5.0 giây | Chờ Leader gửi `PROPOSE` khi bắt đầu height mới | Cảnh báo `LEADER_UNAVAILABLE`. Không tự tạo block. Chờ tiếp |
| `PREPARE_TIMEOUT` | 2.0 giây | Đã gửi PREPARE nhưng chưa gom đủ 3 phiếu PREPARE | Kích hoạt Retry: Broadcast lại chính phiếu `PREPARE` cũ |
| `COMMIT_TIMEOUT` | 2.0 giây | Đã gửi COMMIT nhưng chưa gom đủ 3 phiếu COMMIT | Kích hoạt Retry: Broadcast lại chính phiếu `COMMIT` cũ |

### 7.2 Quy tắc Bất biến khi Retry (Retry Invariant)
1. **Chỉ phát lại bản ghi cũ (Retransmission Only):**
   Khi kích hoạt retry, validator đọc lại bản ghi vote đã lưu trong SQLite và phát lại nguyên vẹn thông điệp cũ. Tuyệt đối không sinh lại chữ ký mới, không thay đổi trường dữ liệu.
2. **Tính lũy đẳng (Idempotency):**
   Phía node nhận: Nếu nhận nhiều thông điệp trùng lặp từ một `sender_id` (do retry hoặc mạng lặp), node chỉ lưu 1 phiếu duy nhất vào `VoteSet`. Bộ đếm Quorum tuyệt đối không được tăng lặp.

### 7.3 "Bốn KHÔNG" của Timeout (Safety Anti-patterns)
Khi xảy ra timeout, hệ thống tuyệt đối cấm các hành vi sau:
1. **KHÔNG HẠ QUORUM:** Không bao giờ hạ ngưỡng từ 3 xuống 2.
2. **KHÔNG TỰ Ý CHỐT BLOCK:** Không chốt khi chưa đủ 3 chữ ký COMMIT hợp lệ.
3. **KHÔNG XÓA DURABLE LOCK:** Không xóa khóa để đổi sang ký block khác ở cùng height.
4. **KHÔNG TỰ Ý ĐỔI LEADER:** Bản lõi không tự chuyển quyền Proposer sang node khác.

### 7.4 Kịch bản Dừng An toàn (Graceful Stall)
Nếu sau $K = 5$ lần Retry liên tiếp mà vẫn không đạt đủ Quorum:
- Node chuyển trạng thái sang **`STALLED`**.
- Hệ thống ngừng tiến trình xử lý, giữ nguyên trạng thái sổ cái hiện có và hiển thị cảnh báo lên giao diện quan sát.

---

## 8. Ma trận Phân tích Kịch bản Lỗi (Fault Scenarios Analysis)

| Kịch bản | Hiện tượng | Kết quả của Giao thức | Đảm bảo Safety? | Đảm bảo Liveness? |
|---|---|---|:---:|:---:|
| **4 node bình thường** | Mạng thông suốt, không có lỗi | Chốt block tuần tự, $4/4$ phiếu | ĐẠT | ĐẠT |
| **1 Follower sập (Crash)** | 3 node còn lại online | 3 node gom đủ $3/4$ phiếu $\Rightarrow$ Tiếp tục chốt | ĐẠT | ĐẠT |
| **1 Follower gửi phiếu giả** | Chữ ký sai hoặc nội dung sai | 3 node trung thực loại bỏ phiếu rác $\Rightarrow$ Vẫn đủ $3/4$ phiếu | ĐẠT | ĐẠT |
| **Leader sập (Crash)** | Không có `PROPOSE` được phát | Timeout `PROPOSAL_TIMEOUT` kích hoạt $\Rightarrow$ Hệ thống dừng (`STALLED`) | ĐẠT | KHÔNG |
| **Leader Equivocation** | Leader gửi Block A cho Node 1,2; gửi Block B cho Node 3,4 | Mỗi block chỉ nhận được tối đa 2 phiếu PREPARE ($< 3$) $\Rightarrow$ Chia phiếu (Split-vote), dừng an toàn | ĐẠT | KHÔNG |
| **Phân vùng mạng 2 - 2** | Nhóm 1 {node1, node2}, Nhóm 2 {node3, node4} | Cả 2 nhóm đều tối đa 2 phiếu ($< 3$) $\Rightarrow$ Không bên nào chốt, chờ nối mạng | ĐẠT | KHÔNG |
| **Phân vùng mạng 3 - 1** | Nhóm 3 node chứa Leader; 1 follower bị cô lập | Nhóm 3 node đạt Quorum $3/4$ và tiếp tục; node cô lập sẽ sync lại sau | ĐẠT | ĐẠT |
| **Node khởi động lại (Restart)** | Node bị sập nguồn khi đang bỏ phiếu | Đọc lại SQLite, phục hồi Lock, không ký sai giá trị | ĐẠT | ĐẠT |

---

## 9. Tiêu chuẩn Nghiệm thu & Kế hoạch Tích hợp (DoD & Interfaces)

### Phối hợp với TV1 (Core Module):
- Thống nhất hàm băm chuẩn hóa: `canonical_bytes()`.
- Xác nhận các trường trong `Vote` không bị thay đổi thứ tự khi parse JSON.
- TV1 cung cấp hàm verify chữ ký: `verify_signature(public_key, message_bytes, signature)`.

### Phối hợp với TV3 (Network & Storage):
- TV3 cài đặt bảng SQLite:
  - `consensus_votes(height, phase, block_hash, signature, created_at)`
  - `consensus_locks(height, locked_block_hash)`
- TV3 đảm bảo giao diện HTTPX Transport thực hiện `retry` có backoff và không giữ Database lock khi đang đợi HTTP.

### Phối hợp với TV4 (Frontend & Monitoring):
- TV2 cung cấp trạng thái hiện tại qua API: `current_phase`, `current_height`, `votes_received`, `is_locked`, `is_stalled`.
- TV4 dùng dữ liệu này để hiển thị Timeline bỏ phiếu trực quan theo thời gian thực.
