# Đặc tả Giao thức Đồng thuận MiniVoting (PBFT-Inspired Consensus Protocol)

- **Mã tài liệu:** `TV2-W1-PROTOCOL`
- **Người phụ trách:** TV2 · Nguyễn Minh Đức (@DucNguyen)
- **Người thẩm định (Reviewers):** TV1 (Core), TV3 (Network/Storage), TV4 (Frontend/Evaluation)
- **Phiên bản:** 1.2 (Cập nhật theo Review TV4 vòng 2)
- **Tình trạng:** Đã hoàn thiện cơ chế thoát STALLED, luồng trạng thái chuẩn và lưu bằng chứng Equivocation

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

### 2.2 Quy ước Chiều cao Khối (Height Conventions)
Để tránh nhầm lẫn giữa trạng thái sổ cái đã chốt và trạng thái đang xử lý đồng thuận:
- **`committed_height`:** Chiều cao của khối cao nhất đã được chốt (*finalized*) và ghi bền vững vào cơ sở dữ liệu SQLite cục bộ (sau Genesis, `committed_height = 0`).
- **`target_height`:** Chiều cao của khối đang được xử lý trong vòng đồng thuận hiện tại, luôn thỏa mãn:
  $$\text{target\_height} = \text{committed\_height} + 1$$
- **Phát hiện đồng bộ (Sync Detection):** Khi nhận thấy `peer_committed_height > local_committed_height`, node nhận biết mình đang bị tụt hậu và phải kích hoạt quy trình đồng bộ (*Sync*), kể cả khi `peer_committed_height == local_target_height`.

### 2.3 Mô hình lỗi Byzantine (Byzantine Fault Tolerance - BFT)
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
   Một validator trung thực không bao giờ ký hai thông điệp có nội dung khác nhau cho cùng một ngữ cảnh đầy đủ (*Full Context*):
   $$\text{Context} = \langle \text{protocol\_version}, \text{chain\_id}, \text{target\_height}, \text{view} = 0, \text{phase} \rangle$$
2. **Bất biến 2 (Bảo vệ tính toàn vẹn của chuỗi - Fork-Free):**
   Nhờ Bất biến 1 và tính chất giao Quorum, không thể tồn tại hai khối khác nhau $B \ne B'$ cùng đạt đủ $q=3$ chữ ký COMMIT tại cùng một `target_height`. Chuỗi sổ cái là duy nhất và tuyến tính.
3. **Bất biến 3 (Không đảo ngược trạng thái - Finality Immutability):**
   Khi một khối đã đạt `CommitCertificate` hợp lệ (gồm đủ 3 chữ ký COMMIT hợp lệ khớp Context), khối đó được coi là chốt vĩnh viễn (*Finalized*), không bao giờ bị hoàn tác (reorg) hay thay thế.

---

## 4. Chi tiết Giao thức Ba Pha (Three-Phase Consensus Protocol)

Mọi validator (kể cả Leader `node1`) đều phải tham gia quy trình bỏ phiếu PREPARE và COMMIT.

```
       LEADER (node1)                               FOLLOWERS (node2, 3, 4)
             │                                                 │
             │─────── PROPOSE(Block) ─────────────────────────>│  (Pha 1: Đề xuất)
             │                                                 │
             │   [Persist Lock & Own PREPARE trước khi gửi]    │
             │<────── PREPARE(block_hash) ────────────────────>│  (Pha 2: Thống nhất thứ tự)
             │   (Broadcast all-to-all, thu thập đủ 3/4 phiếu)  │
             │                                                 │
             │   [Đạt PreparedCert -> Persist Own COMMIT]      │
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
  - Vòng trước đó tại `committed_height` đã hoàn tất (hoặc bắt đầu từ Genesis ở `committed_height = 0`, `target_height = 1`).
- **Quy trình xử lý tại Leader:**
  1. Chọn danh sách giao dịch từ mempool.
  2. Thực thi thử tuần tự các giao dịch trên bản sao trạng thái tài khoản để tính `state_hash` và `tx_list_hash`.
  3. Đóng gói Header: `height = target_height`, `prev_hash = tip_hash`, `timestamp_ms`, `proposer_id = 'node1'`, `state_hash`, `tx_list_hash`.
  4. Tính `block_hash = SHA256(canonical_bytes(Header))`.
  5. Leader tạo `SignedContext` (7 trường: `protocol_version`, `chain_id`, `height = target_height`, `view = 0`, `phase = 'PROPOSE'`, `block_hash`, `sender_id = 'node1'`).
  6. Leader ký đề xuất có phân tách miền ký Ed25519 (theo RFC 8032):
     $$\text{proposal\_signing\_bytes} = \text{ASCII}(\text{"MINIVOTING-V1/PROPOSE"}) \mathbin{\Vert} \text{0x00} \mathbin{\Vert} \text{canonical\_bytes}(\text{SignedContext})$$
     $$\text{proposal\_sig} = \text{Sign}(\text{leader\_private\_key}, \text{proposal\_signing\_bytes})$$
  7. **Ghi đĩa trước (Persist-Before-Send):** Leader lưu `proposal` vào SQLite để sẵn sàng phát lại nếu peer yêu cầu.
  8. Broadcast thông điệp `PROPOSE` (gồm `SignedContext`, `proposal_sig` và `block` đính kèm ở cùng cấp JSON) cho tất cả các node.

### 4.2 Pha 2: PREPARE (Xác thực và Khóa thứ tự)
- **Chủ thể:** **Tất cả các Validator (kể cả Leader)**.
- **Quy trình tiếp nhận và thẩm định tại Validator $V_i$:**
  1. **Kiểm tra cơ sở (Context):** Đúng `protocol_version`, đúng `chain_id`, đúng `view = 0`.
  2. **Kiểm tra Proposer:** `proposer_id` phải là `node1` và chữ ký proposal hợp lệ.
  3. **Kiểm tra chuỗi:** `height` phải bằng `target_height` (`committed_height + 1`); `prev_hash` phải khớp với hash khối chốt gần nhất (`tip_hash`).
  4. **Kiểm tra nghiệp vụ (State verification):** Tự thực thi lại danh sách giao dịch, đối chiếu `state_hash` và `tx_list_hash`. Nếu sai lệch $\rightarrow$ Từ chối và ghi log `REJECT`.
  5. **Kiểm tra Khóa bền vững:** $V_i$ chưa từng khóa một `block_hash` nào khác tại `target_height` này.
- **Lưu khóa và Bỏ phiếu (Persist-Before-Send bắt buộc - Tiêu chí T22, T29):**
  1. $V_i$ tạo thông điệp vote `PREPARE` cho `block_hash`.
  2. **Lưu nguyên tử vào SQLite TRƯỚC KHI phát mạng:**
     - Ghi khóa bền vững: `consensus_locks(height = target_height, locked_block_hash = block_hash)`.
     - Ghi phiếu bầu của chính mình: `consensus_votes(height = target_height, phase = 'PREPARE', ...)`.
  3. Chỉ sau khi Database commit thành công, $V_i$ mới broadcast thông điệp `PREPARE` tới toàn bộ $n=4$ node.
- **Tạo Prepared Certificate:**
  - Mỗi node duy trì một bộ thu thập phiếu (`VoteSet`) cho pha PREPARE.
  - Khi thu thập đủ $\ge 3$ phiếu `PREPARE` hợp lệ, từ các validator khác nhau, khớp toàn bộ Context và có cùng `block_hash` tại `target_height` $\Rightarrow$ Tạo thành **`PreparedCertificate`**.
  - Node chính thức bước vào trạng thái **PREPARED**.

### 4.3 Pha 3: COMMIT (Cam kết chốt vào sổ cái)
- **Chủ thể:** **Tất cả các Validator** (chỉ thực hiện sau khi đã sở hữu `PreparedCertificate`).
- **Quy trình xử lý tại Validator $V_i$:**
  1. Khi đạt trạng thái `PREPARED`, $V_i$ bắt buộc phải ký, lưu và phát phiếu `COMMIT`:
     - Tạo thông điệp vote `COMMIT` cho `block_hash` đã khóa.
     - **Persist-Before-Send:** Ghi phiếu `COMMIT` của mình vào SQLite bảng `consensus_votes`.
     - Broadcast thông điệp `COMMIT` tới toàn bộ $n=4$ node.
     - Node chuyển sang trạng thái **COMMITTING**.
  2. **Tạo Commit Certificate và Chốt sổ (Finalization):**
     - Khi node thu thập đủ $\ge 3$ phiếu `COMMIT` hợp lệ, từ các validator khác nhau, khớp toàn bộ Context và cùng `block_hash` tại `target_height` $\Rightarrow$ Tạo thành **`CommitCertificate`**.
     - Node chuyển sang trạng thái **DECIDED**.
  3. **Commit nguyên tử (Atomic DB Transaction):**
     - Ghi dữ liệu Block vào bảng `blocks`.
     - Ghi `CommitCertificate` vào bảng `certificates`.
     - Cập nhật số dư (balance) và nonce của các tài khoản vào bảng `accounts`.
     - Xóa các giao dịch đã chốt khỏi mempool.
     - Xóa `consensus_locks` của `target_height` đã hoàn tất.
     - Cập nhật `committed_height = target_height`.
  4. Node phát sự kiện đã chốt và sẵn sàng tăng `target_height` cho vòng tiếp theo.

---

## 5. Cấu trúc Thông điệp Chuẩn hóa (Message Specification)

Tất cả các thông điệp đồng thuận phải tuân theo cấu trúc Pydantic nghiêm ngặt, được chuẩn hóa (`canonical_bytes`) trước khi băm và ký:

### 5.1 Cấu trúc Ngữ cảnh Ký (SignedContext)
`SignedContext` là cấu trúc 7 trường dùng chung cho việc ký đề xuất `PROPOSE` và các phiếu `PREPARE`, `COMMIT`:

```json
{
  "protocol_version": 1,
  "chain_id": "minivoting-testnet-1",
  "height": 1,
  "view": 0,
  "phase": "PREPARE", 
  "block_hash": "a5c7f8...64_hex_chars...",
  "sender_id": "node2"
}
```

### 5.2 Cấu trúc Thông điệp Đề xuất (Proposal Message)
`Proposal` mở rộng từ `SignedContext` (với `phase = 'PROPOSE'`), bổ sung chữ ký của leader và khối đính kèm ở cùng cấp JSON:

```json
{
  "protocol_version": 1,
  "chain_id": "minivoting-testnet-1",
  "height": 1,
  "view": 0,
  "phase": "PROPOSE",
  "block_hash": "a5c7f8...64_hex_chars...",
  "sender_id": "node1",
  "signature": "3b8e21...128_hex_chars...",
  "block": {
    "header": {
      "protocol_version": 1,
      "chain_id": "minivoting-testnet-1",
      "height": 1,
      "prev_hash": "0000000000000000000000000000000000000000000000000000000000000000",
      "proposer_id": "node1",
      "timestamp_ms": 1732316400000,
      "tx_list_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "state_hash": "4a5e1e...64_hex_chars..."
    },
    "transactions": [],
    "block_hash": "a5c7f8...64_hex_chars..."
  }
}
```

*Lưu ý về chữ ký Proposal:* Chữ ký `signature` của Leader chỉ bao phủ `SignedContext` với miền ký `MINIVOTING-V1/PROPOSE`. Dữ liệu khối `block` đính kèm được thẩm định độc lập thông qua việc tính lại `tx_list_hash`, `state_hash` và `block_hash`.

### 5.3 Cấu trúc Thông điệp Bỏ phiếu (Vote Message)
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

*Quy tắc ký Ed25519 có phân tách miền (Domain Separation Prefix - RFC 8032):*
- Chuỗi byte đưa vào hàm ký/xác thực Ed25519 được ghép nối bằng tiền tố domain ASCII và byte `0x00`:
  $$\text{signing\_bytes} = \text{ASCII}(\text{"MINIVOTING-V1/"} + \text{phase}) \mathbin{\Vert} \text{0x00} \mathbin{\Vert} \text{canonical\_bytes}(\text{SignedContext})$$
  $$\text{signature} = \text{Sign}_{SK}(\text{signing\_bytes})$$
- Tiền tố miền tương ứng: `"MINIVOTING-V1/PROPOSE"`, `"MINIVOTING-V1/PREPARE"`, hoặc `"MINIVOTING-V1/COMMIT"`. Quy tắc này ngăn chặn 100% việc tái sử dụng chữ ký giữa các pha hoặc các ngữ cảnh khác nhau (Tiêu chí T14).

### 5.4 Cấu trúc Certificate (PreparedCertificate và CommitCertificate)
`PreparedCertificate` và `CommitCertificate` có chung cấu trúc, đứng ngoài `Block` để tránh phụ thuộc vòng:

```json
{
  "protocol_version": 1,
  "chain_id": "minivoting-testnet-1",
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

*Quy tắc xác minh Certificate:*
- Với mỗi mục `(sender_id, signature)` trong `signatures`:
  1. Dựng lại `SignedContext` từ các trường của certificate, gán `sender_id` là khóa trong map, `phase = 'PREPARE'` (đối với PreparedCertificate) hoặc `phase = 'COMMIT'` (đối với CommitCertificate).
  2. Tính `signing_bytes` theo đúng miền ký tương ứng và xác thực bằng public key của `sender_id` từ Genesis registry.
  3. Certificate hợp lệ khi và chỉ khi có $\ge 3$ chữ ký hợp lệ từ các validator khác nhau được ủy quyền.

---

## 6. Cơ chế Bền vững và Khóa (Durable Locks & Persist-Before-Send)

### 6.1 Nguyên tắc Persist-Before-Send (Tiêu chí T22, T29)
1. Mọi validator tuyệt đối **không được phát thông điệp mạng trước khi hoàn tất ghi đĩa (SQLite)**.
2. Trình tự bắt buộc tại pha PREPARE:
   $$\text{Tạo Vote} \longrightarrow \text{Ghi Lock + Vote vào SQLite} \longrightarrow \text{Broadcast HTTP}$$
3. **Phục hồi sau Crash (Restart Recovery):**
   - Khi node khởi động lại, CSM đọc bảng `consensus_locks` và `consensus_votes` tại `target_height`.
   - Nếu đã tồn tại lock cho `target_height`, node nạp lại `locked_block_hash` vào bộ nhớ và chỉ gửi lại (*retransmit*) phiếu bầu cũ, kiên quyết từ chối ký bất kỳ đề xuất nào khác (ngăn chặn double-signing ngoài ý muốn).

### 6.2 Khóa bền vững (Durable Lock)
- Khóa được xác lập ngay tại thời điểm node đồng ý phát phiếu `PREPARE` cho `block_hash`.
- Khóa chỉ được mở/xóa khi:
  1. Khối tại `target_height` được commit thành công vào sổ cái.
  2. Hoặc node thực hiện đồng bộ (*sync*) từ một peer đã có `peer_committed_height >= target_height` kèm `CommitCertificate` hợp lệ.

---

## 7. Chính sách Timeout, Retry và Phục hồi Liveness (Timeout, Retry & Liveness Recovery)

### 7.1 Ba bộ đếm thời gian (Timers)

| Bộ đếm (Timer) | Thời gian mặc định | Ngữ cảnh kích hoạt | Hành động khi hết hạn (On Timeout) |
|---|---|---|---|
| `PROPOSAL_TIMEOUT` | 5.0 giây | Chờ Leader gửi `PROPOSE` khi bắt đầu `target_height` | Cảnh báo `LEADER_UNAVAILABLE`. Gửi yêu cầu kéo proposal từ Leader. Chờ tiếp |
| `PREPARE_TIMEOUT` | 2.0 giây | Đã gửi PREPARE nhưng chưa gom đủ 3 phiếu PREPARE | Kích hoạt Retry: Broadcast lại chính phiếu `PREPARE` cũ |
| `COMMIT_TIMEOUT` | 2.0 giây | Đã gửi COMMIT nhưng chưa gom đủ 3 phiếu COMMIT | Kích hoạt Retry: Broadcast lại chính phiếu `COMMIT` cũ |
| `STALLED_PROBE_TIMER` | 10.0 giây (± 2s jitter) | Kích hoạt khi node rơi vào `STALLED` | Phát lại chậm (Slow Probe) phiếu đã lưu hoặc thăm dò trạng thái peer |

### 7.2 Lấy lại Proposal và Xử lý Phiếu Đến Sớm (Early Vote Buffering - Tiêu chí T15)
1. **Lấy lại Proposal bị mất:**
   - Nếu Follower nhận được phiếu `PREPARE` hoặc `COMMIT` cho `target_height` nhưng bản thân chưa nhận được `PROPOSE` (do trễ mạng hoặc gói tin mất):
   - Follower chủ động gửi request `GET /consensus/proposal?height=target_height` tới Leader (hoặc peers).
   - Leader đọc đề xuất đã lưu trong SQLite (`Persist-Before-Send`) và phát lại nguyên vẹn cho Follower.
2. **Hàng đợi đệm phiếu đến sớm (Early Votes Buffer):**
   - Gói tin mạng có thể bị đảo thứ tự: Phiếu `COMMIT` đến trước `PREPARE`, hoặc phiếu bầu đến trước khi nhận được `PROPOSE`.
   - Node duy trì một bộ đệm có giới hạn (`early_votes_buffer`, tối đa 50 phần tử để chống tràn bộ nhớ theo tiêu chí T30).
   - Khi khối proposal tương ứng được tiếp nhận và thẩm định thành công, node tự động xả (*flush*) các phiếu trong buffer ra để kiểm tra Quorum.

### 7.3 Giải quyết Bế tắc Liveness khi Mạng 2–2 Phục hồi (Tiêu chí E4 & Phục hồi STALLED)
- **Kịch bản Deadlock tiềm tàng:** Bốn node đều nhận cùng proposal, mạng bị chia cắt 2–2 đủ lâu khiến cả 4 node cạn kiệt 5 lượt retry nhanh và cùng rơi vào `STALLED`. Nếu các node hoàn toàn im lặng, khi mạng nối lại sẽ không có ai phát tin để kích hoạt tiếp.
- **Cơ chế Slow Probe và Phát lại Kép (Dual-Vote Retransmission - theo `module-interfaces.md §4`):**
  - Khi ở trạng thái `STALLED`, node **dừng retry dồn dập (fast retry 2s)** để tránh nghẽn mạng, nhưng **chuyển sang chế độ Thăm dò Chậm (Slow Probe)**:
    - Định kỳ mỗi $10 \pm 2$ giây (có jitter ngẫu nhiên để tránh xung đột đồng thời), node phát lại phiếu bầu đã lưu của mình:
      - **Nếu node đã lưu cả own PREPARE và own COMMIT**: Node bắt buộc phát lại **CẢ HAI PHIẾU**. Lý do: Một peer bị trễ mạng còn kẹt ở pha PREPARE cần phiếu PREPARE của node này để đạt `PreparedCertificate`. Nếu node này chỉ phát lại COMMIT, peer kia sẽ không thể tiến lên.
      - **Nếu node chỉ mới lưu own PREPARE**: Node phát lại own PREPARE.
    - Hoặc node gửi request thăm dò trạng thái `GET /consensus/status?height=target_height` tới các peer.
  - Khi phân vùng mạng 2–2 được hàn gắn, cơ chế Slow Probe bảo đảm các node trao đổi được các phiếu còn thiếu, phá vỡ thế bế tắc và đưa hệ thống tiến triển tiếp.
  - Toàn bộ quá trình phục hồi **tuyệt đối giữ nguyên lock đã lưu và ngưỡng Quorum $q=3$**.

### 7.4 Đường Chuyển Trạng thái khi Thoát khỏi STALLED và Đường Dẫn Nhanh (Fast-Path)
Quy trình phục hồi từ `STALLED` phải tuân thủ tuần tự theo đúng pha đồng thuận:
1. **Nếu đang kẹt ở pha PREPARE:**
   - Khi nhận đủ $\ge 3$ phiếu `PREPARE` hợp lệ $\Rightarrow$ Node chuyển sang **`PREPARED`**.
   - Tại `PREPARED`, node bắt buộc thực hiện: Ký own `COMMIT`, lưu vào SQLite, phát `COMMIT` ra mạng $\Rightarrow$ Node chuyển sang **`COMMITTING`**. *(Tuyệt đối không nhảy cóc từ STALLED sang thẳng COMMITTING mà bỏ qua bước lưu/phát COMMIT)*.
2. **Nếu đang kẹt ở pha COMMIT:**
   - Khi nhận đủ $\ge 3$ phiếu `COMMIT` hợp lệ (hoặc nhận được `CommitCertificate` hợp lệ từ peer) $\Rightarrow$ Node chuyển sang **`DECIDED`** và thực hiện commit nguyên tử vào SQLite.
3. **Đường dẫn nhanh qua Finalized Block (`POST /peer/finalized`):**
   - Nếu node (ở bất kỳ trạng thái `WAIT_PROPOSAL`, `PREPARING`, `COMMITTING`, `STALLED`) nhận được `FinalizedBlock` (gồm `Proposal` + `CommitCertificate` hợp lệ từ $\ge 3$ validator khác) tại `target_height`:
   - Node xác minh Proposal signature, xác thực từng chữ ký trong CommitCertificate, và tự thực thi lại block trên snapshot. Nếu hợp lệ, node được phép **chuyển thẳng sang `DECIDED` và commit nguyên tử vào SQLite** mà không bắt buộc bản thân phải sở hữu `PreparedCertificate` cục bộ trước đó (rất hữu ích cho follower bị chậm nhịp hoặc vừa phục hồi sau crash).
4. **Nếu phát hiện peer đã đi trước:**
   - Nếu `peer_committed_height > local_committed_height` $\Rightarrow$ Node chuyển sang **`SYNCING`**.

---

## 8. Cơ chế Bắt và Lưu Trữ Bằng Chứng Equivocation (Tiêu chí T17)

Để ngăn chặn validator Byzantine lách luật bằng cách đảo thứ tự gửi phiếu và cung cấp đầy đủ bằng chứng cho TV3 lưu trữ:

### 8.1 Thuật toán Kiểm tra Độc lập Thứ tự
- Hệ thống duy trì bảng chứng cứ phiếu đã quan sát:
  $$\text{seen\_votes}[\langle \text{target\_height}, \text{phase} \rangle][\text{sender\_id}] = \text{vote}$$
- Bảng bằng chứng gian lận:
  $$\text{equivocation\_evidence}[\text{sender\_id}] = \langle \text{vote}_1, \text{vote}_2 \rangle$$

### 8.2 Quy trình Xử lý khi nhận Phiếu $V$ từ `sender_id`:
1. **Nếu `sender_id` chưa có trong `seen_votes`:**
   - Lưu `seen_votes[sender_id] = V`.
   - Nếu $V.\text{block\_hash} == \text{expected\_block\_hash}$, đưa $V$ vào `quorum_votes`.
2. **Nếu `sender_id` đã có trong `seen_votes` ($V_{\text{old}} = \text{seen\_votes}[sender\_id]$):**
   - **Trường hợp A (Trùng lặp hợp lệ - Idempotency):**
     Nếu $V.\text{block\_hash} == V_{\text{old}}.\text{block\_hash}$ và $V.\text{signature} == V_{\text{old}}.\text{signature}$ $\rightarrow$ Bỏ qua (không tăng đếm Quorum).
   - **Trường hợp B (Gian lận Byzantine - Equivocation):**
     Nếu $V.\text{block\_hash} \ne V_{\text{old}}.\text{block\_hash}$:
     - **Lưu toàn bộ cặp phiếu làm bằng chứng:** Ghi nhận `equivocation_evidence[sender_id] = (V_{\text{old}}, V)`.
     - **Gọi Storage Interface (TV3):** Chuyển giao cặp bằng chứng xuống bảng SQLite `consensus_equivocations(height, phase, sender_id, vote_a_json, vote_b_json, detected_at)`.
     - **Xử lý Quorum:** Loại bỏ hoàn toàn `sender_id` khỏi `quorum_votes` (nếu trước đó đã thêm vào).
     - Ghi log cảnh báo mức CRITICAL: *Phát hiện Byzantine Equivocation từ validator `sender_id`*.
- **Tính độc lập thứ tự:** Dù validator gửi $A$ trước $B$ sau, hay $B$ trước $A$ sau, hệ thống đều bắt được hành vi double-signing ngay khi phiếu thứ hai tới và lưu trữ đủ cả 2 chữ ký đối lập làm bằng chứng.

---

## 9. Ma trận Phân tích Kịch bản Lỗi (Fault Scenarios Analysis)

| Kịch bản | Tiêu chí | Hiện tượng | Kết quả của Giao thức | Đảm bảo Safety? | Đảm bảo Liveness? |
|---|:---:|---|---|:---:|:---:|
| **4 node bình thường** | Baseline | Mạng thông suốt, không có lỗi | Chốt block tuần tự, $4/4$ phiếu | ĐẠT | ĐẠT |
| **1 Follower sập (Crash)** | T18 | 3 node còn lại online | 3 node gom đủ $3/4$ phiếu $\Rightarrow$ Tiếp tục chốt | ĐẠT | ĐẠT |
| **1 Follower gửi phiếu sai Context** | T14 | Trộn height/chain/phase hoặc view != 0 | Bị loại bỏ ngay trước khi tính Quorum | ĐẠT | ĐẠT |
| **Phiếu tới trễ / đảo thứ tự** | T15 | Phiếu đến trước proposal hoặc COMMIT trước PREPARE | Lưu vào early buffer, kéo proposal thiếu | ĐẠT | ĐẠT |
| **Leader Equivocation** | T16 | Leader gửi 2 block cạnh tranh | Chia phiếu (Split-vote), không block nào đủ 3 phiếu $\Rightarrow$ Dừng an toàn (`STALLED`) | ĐẠT | KHÔNG |
| **Byzantine Double-Signing** | T17 | Follower gửi 2 phiếu khác hash (thứ tự A→B hoặc B→A) | Phát hiện Equivocation độc lập thứ tự, lưu đủ 2 phiếu làm chứng cứ | ĐẠT | ĐẠT |
| **Restart khi đang bỏ phiếu** | T22, T29 | Sập nguồn sau khi gửi hoặc 2 request đồng thời | Khôi phục Lock và Own Vote từ SQLite, không ký giá trị khác | ĐẠT | ĐẠT |
| **Phân vùng mạng 2 - 2 rồi nối lại** | E4 | 4 node vào STALLED, sau đó mạng phục hồi | Cơ chế Slow Probe phá deadlock, gom đủ 3 phiếu chốt block | ĐẠT | ĐẠT |
| **Phân vùng mạng 3 - 1** | E4 | Nhóm 3 node chứa Leader; 1 follower bị cô lập | Nhóm 3 node đạt Quorum $3/4$ và tiếp tục; node cô lập sync sau | ĐẠT | ĐẠT |

---

## 10. Tiêu chuẩn Nghiệm thu & Kế hoạch Tích hợp (DoD & Interfaces)

### Phối hợp với TV1 (Core Module):
- Thống nhất hàm băm chuẩn hóa: `canonical_bytes()`.
- Xác nhận các trường trong `Vote` không bị thay đổi thứ tự khi parse JSON.
- TV1 cung cấp hàm verify chữ ký: `verify_signature(public_key, message_bytes, signature)`.

### Phối hợp với TV3 (Network & Storage):
- TV3 cài đặt bảng SQLite:
  - `consensus_votes(height, phase, block_hash, signature, created_at)`
  - `consensus_locks(height, locked_block_hash)`
  - `consensus_equivocations(height, phase, sender_id, vote_a_json, vote_b_json, detected_at)`
- TV3 đảm bảo quy tắc `Persist-Before-Send`: ghi khóa và phiếu bầu vào SQLite trong cùng transaction trước khi gọi hàm broadcast của HTTP transport.
- Cài đặt endpoint `GET /consensus/proposal?height={height}` để phục vụ lấy lại proposal bị thiếu.
- Cài đặt endpoint `GET /consensus/status?height={height}` phục vụ cơ chế Slow Probe khi ở trạng thái `STALLED`.

### Phối hợp với TV4 (Frontend & Monitoring):
- TV2 cung cấp trạng thái hiện tại qua API: `committed_height`, `target_height`, `current_phase`, `votes_received`, `is_locked`, `is_stalled`.
- TV4 dùng dữ liệu này để hiển thị Timeline bỏ phiếu trực quan theo thời gian thực và cảnh báo vi phạm Equivocation nếu có.
