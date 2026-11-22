# Đặc tả Hợp đồng Giao tiếp API & Wire Schema (MiniVoting API Contract)

- **Mã tài liệu:** `TV3-W1-API-CONTRACT`
- **Người phụ trách:** TV3 · Phương Văn Đức (@pvduc05)
- **Người thẩm định (Reviewers):**
  - TV1 (Core / Data Model): Thẩm định chữ ký, schema giao dịch, block và canonical bytes.
  - TV2 (Consensus): Thẩm định định dạng Vote, Certificate, mã lỗi đồng thuận và timeout.
  - TV4 (Frontend / Evaluation): Thẩm định dữ liệu giám sát Dashboard, Explorer và Metrics.
- **Phiên bản:** 1.0 (Chốt hợp đồng Tuần 1)
- **Tình trạng:** Đã hoàn thiện toàn diện, đồng bộ với [docs/protocol.md](protocol.md) và [docs/consensus-state-machine.md](consensus-state-machine.md).

---

## 1. Tổng quan & Nguyên tắc Thiết kế (Design Principles)

Hệ thống `BlockChain_MiniVoting` sử dụng giao thức HTTP RESTful kết hợp định dạng trao đổi dữ liệu JSON cho cả giao tiếp người dùng/client lẫn giao tiếp ngang hàng (*Peer-to-Peer Consensus Wire*).

### 1.1 Nguyên tắc Bất biến (Core Invariants)
1. **202 Accepted $\ne$ Committed:** Khi client gửi giao dịch tới `POST /transactions`, phản hồi `202 Accepted` chỉ chứng nhận giao dịch hợp lệ sơ bộ về mặt cú pháp và đã được tiếp nhận vào Mempool cục bộ. Giao dịch **CHƯA** được coi là đã chốt vào sổ cái cho tới khi nằm trong một khối đạt đủ Quorum $\ge 3/4$ chữ ký `COMMIT`.
2. **Health OK (200) $\ne$ Consensus Ready:** Phản hồi `GET /health` trả về `200 OK` chỉ xác nhận tiến trình API đang chạy và lắng nghe socket. Endpoint này **không biểu thị** node đã đủ Quorum mạng hay đã đồng bộ xong dữ liệu sổ cái.
3. **Persist-Before-Send (Ghi đĩa trước khi phát tán):** Mọi hành động phát phiếu `PREPARE` hay `COMMIT` qua các endpoint `/peer/*` phải được thực hiện **SAU KHI** khóa đồng thuận (`consensus_locks`) và chữ ký của chính node (`consensus_votes`) đã được ghi thành công và nguyên tử vào cơ sở dữ liệu SQLite cục bộ.
4. **Giới hạn tài nguyên nghiêm ngặt (Bounded Buffers):** Mọi endpoint tiếp nhận dữ liệu đều áp đặt ngưỡng trần kích thước (payload limits) và số lượng phần tử nhằm ngăn chặn tấn công từ chối dịch vụ (DoS) cạn kiệt bộ nhớ.

---

## 2. Tiêu chuẩn Mã hóa & Định dạng Dữ liệu (Wire Standards)

- **Chuẩn ký tự:** UTF-8.
- **Định dạng số:**
  - `amount`: Số nguyên dương thuần túy (`amount > 0`, kiểu `int` 64-bit), cấm số âm, số 0, số thực (`float`), hoặc chuỗi số.
  - `nonce`: Số nguyên không âm (`nonce >= 0`), tăng đơn điệu theo từng địa chỉ gửi.
  - `height`: Số nguyên không âm (`height >= 0`, Genesis có `height = 0`).
  - `view`: Số nguyên không âm (trong bản lõi cố định `view = 0`).
- **Mã băm (Hashes):** Chuỗi ký tự Hexadecimal viết thường 64 ký tự (SHA-256 digests, độ dài chính xác 64 hex characters).
- **Chữ ký số (Signatures):** Chuỗi ký tự Ed25519 (tối thiểu 64 ký tự hex/base64).
- **Cấu trúc lỗi chuẩn (Standard Error Envelope):**
  Mọi lỗi HTTP $4xx$ và $5xx$ đều trả về cấu trúc đồng nhất:
  ```json
  {
    "detail": {
      "code": "MA_LOI_CHUAN",
      "message": "Mô tả chi tiết nguyên nhân lỗi dễ hiểu.",
      "details": {
        "field": "thong_tin_bo_sung"
      }
    }
  }
  ```

---

## 3. Tham số Giới hạn & Timeout Toàn hệ thống (Limits & Timeouts)

| Tham số | Giá trị | Phạm vi áp dụng | Mục đích bảo vệ |
|---|---|---|---|
| `MAX_TRANSACTION_PAYLOAD_BYTES` | `65,536` bytes (64 KB) | `POST /transactions` | Chống gửi payload giao dịch phình to |
| `MAX_REQUEST_BODY_BYTES` | `1,048,576` bytes (1 MB) | Toàn bộ API endpoints | Giới hạn dung lượng gói tin HTTP |
| `MAX_TRANSACTIONS_PER_BLOCK` | `50` transactions | `Block` đề xuất | Khống chế thời gian xử lý và dung lượng khối |
| `MAX_PENDING_MEMPOOL` | `1,000` transactions | Bộ nhớ tạm của Validator | Tránh tràn RAM khi nhận tải cao |
| `MAX_BUFFERED_EARLY_VOTES` | `100` votes / height | Bộ gom phiếu | Chống tấn công flood phiếu sớm |
| `PROPOSAL_TIMEOUT` | `5.0` giây | Máy trạng thái đồng thuận | Thời gian chờ Leader đề xuất block mới |
| `PREPARE_TIMEOUT` | `2.0` giây | Máy trạng thái đồng thuận | Thời gian gom Quorum 3/4 phiếu PREPARE |
| `COMMIT_TIMEOUT` | `2.0` giây | Máy trạng thái đồng thuận | Thời gian gom Quorum 3/4 phiếu COMMIT |
| `PEER_REQUEST_TIMEOUT` | `2.0` giây | HTTP Transport Client | Timeout khi gọi sang peer node |
| `MAX_FAST_RETRIES` ($K$) | `5` lần | Vòng lặp phát lại phiếu | Số lần retry nhanh trước khi chuyển STALLED |
| `SLOW_PROBE_INTERVAL` | `10.0` giây | Trạng thái STALLED | Chu kỳ thăm dò chậm phá vỡ bế tắc mạng |

---

## 4. Danh mục Mã lỗi Chuẩn (Standard Error Taxonomy)

| Mã lỗi (`code`) | HTTP Status | Diễn giải nguyên nhân |
|---|:---:|---|
| `CONSENSUS_NOT_READY` | 503 | Node chưa khởi động xong consensus hoặc đang ở giai đoạn khung phát triển |
| `INVALID_SIGNATURE` | 400 | Chữ ký Ed25519 của giao dịch, đề xuất hoặc phiếu bầu không hợp lệ |
| `INVALID_NONCE` | 400 | Nonce giao dịch không khớp với `current_nonce + 1` của tài khoản |
| `INSUFFICIENT_FUNDS` | 400 | Số dư tài khoản gửi không đủ để thực hiện giao dịch chuyển tiền |
| `INVALID_CHAIN_ID` | 400 | Chain ID trong thông điệp không khớp với cấu hình cluster (`minivoting-dev`) |
| `PAYLOAD_TOO_LARGE` | 413 | Kích thước gói tin vượt quá hạn mức tối đa quy định |
| `VALIDATION_FAILED` | 422 | Cấu trúc dữ liệu không thỏa mãn Pydantic schema hoặc logic nghiệm thu |
| `EQUIVOCATION_DETECTED` | 409 | Phát hiện cùng 1 validator ký 2 phiếu mâu thuẫn trong cùng một context |
| `ALREADY_COMMITTED` | 409 | Chiều cao hoặc giao dịch này đã được chốt vĩnh viễn vào sổ cái |
| `BLOCK_NOT_FOUND` | 404 | Không tìm thấy khối tại chiều cao (`height`) yêu cầu |
| `TRANSACTION_NOT_FOUND` | 404 | Không tìm thấy mã giao dịch (`tx_id`) trong mempool hoặc sổ cái |
| `ACCOUNT_NOT_FOUND` | 404 | Địa chỉ tài khoản chưa từng xuất hiện trên chuỗi (chưa có giao dịch) |
| `TIMEOUT` | 504 | Hết hạn thời gian chờ phản hồi từ peer hoặc hàng đợi |

---

## 5. Đặc tả Chi tiết Client & Explorer Endpoints

### 5.1 `GET /health`
- **Mục đích:** Kiểm tra tiến trình node còn sống hay không.
- **Query Params:** Không.
- **Phản hồi 200 OK:**
  ```json
  {
    "status": "ok",
    "node_id": "node1",
    "consensus_ready": false
  }
  ```

### 5.2 `GET /status`
- **Mục đích:** Cung cấp trạng thái tổng quan phục vụ Dashboard và kịch bản kiểm thử.
- **Phản hồi 200 OK (khi consensus sẵn sàng):**
  ```json
  {
    "node_id": "node1",
    "leader_id": "node1",
    "is_leader": true,
    "chain_id": "minivoting-dev",
    "committed_height": 12,
    "target_height": 13,
    "tip_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "phase": "PREPARING",
    "sync_state": "IDLE",
    "is_locked": true,
    "locked_block_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "is_stalled": false,
    "peers_count": 3,
    "peers_online": ["node2", "node3", "node4"]
  }
  ```
- **Phản hồi 503 Service Unavailable (trong bản scaffold hiện tại):**
  ```json
  {
    "detail": {
      "code": "CONSENSUS_NOT_READY",
      "message": "Consensus and persistent ledger are not implemented yet."
    }
  }
  ```

### 5.3 `POST /transactions`
- **Mục đích:** Tiếp nhận giao dịch đã được ký từ ví hoặc client.
- **Headers:** `Content-Type: application/json`
- **Request Body (`TransactionPayload`):**
  ```json
  {
    "chain_id": "minivoting-dev",
    "sender": "ed25519_public_key_alice_hex",
    "recipient": "ed25519_public_key_bob_hex",
    "amount": 50,
    "nonce": 1,
    "signature": "signature_hex_of_canonical_bytes"
  }
  ```
- **Phản hồi 202 Accepted (Đưa vào Mempool):**
  ```json
  {
    "tx_id": "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
    "status": "accepted",
    "message": "Transaction accepted into mempool; pending block proposal.",
    "block_height": null,
    "committed_at": null
  }
  ```
- **Phản hồi lỗi 400 Bad Request:** Khi sai chữ ký, âm tiền hoặc sai nonce.

### 5.4 `GET /transactions/{tx_id}`
- **Mục đích:** Tra cứu trạng thái xử lý của một giao dịch cụ thể.
- **Phản hồi 200 OK:**
  ```json
  {
    "tx_id": "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
    "status": "committed",
    "message": "Transaction committed in block #12.",
    "block_height": 12,
    "committed_at": "2026-11-22T23:15:00Z"
  }
  ```

### 5.5 `GET /accounts/{address}`
- **Mục đích:** Truy vấn số dư và nonce đã chốt bền vững của tài khoản.
- **Phản hồi 200 OK:**
  ```json
  {
    "address": "ed25519_public_key_alice_hex",
    "balance": 950,
    "nonce": 1,
    "committed_height": 12
  }
  ```

### 5.6 `GET /blocks` & `GET /blocks/{height}`
- **Mục đích:** Cung cấp dữ liệu duyệt khối kèm bằng chứng `CommitCertificate`.
- **Query Params cho `/blocks`:** `offset` (mặc định 0), `limit` (mặc định 20, max 100).
- **Phản hồi 200 OK cho `/blocks/{height}`:**
  ```json
  {
    "height": 1,
    "block_hash": "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b",
    "prev_hash": "0000000000000000000000000000000000000000000000000000000000000000",
    "state_hash": "d4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35",
    "tx_list_hash": "4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce",
    "proposer_id": "node1",
    "timestamp": 1700000000,
    "tx_count": 1,
    "transactions": [
      {
        "chain_id": "minivoting-dev",
        "sender": "alice_pubkey",
        "recipient": "bob_pubkey",
        "amount": 50,
        "nonce": 0,
        "signature": "sig_bytes"
      }
    ],
    "certificate": {
      "height": 1,
      "view": 0,
      "block_hash": "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b",
      "signatures": [
        {"sender_id": "node1", "signature": "sig1"},
        {"sender_id": "node2", "signature": "sig2"},
        {"sender_id": "node3", "signature": "sig3"}
      ]
    }
  }
  ```

### 5.7 `GET /consensus/{height}`
- **Mục đích:** Tra cứu snapshot trạng thái đồng thuận tại một khối để vẽ timeline phiếu bầu.
- **Phản hồi 200 OK:**
  ```json
  {
    "height": 1,
    "view": 0,
    "phase": "DECIDED",
    "block_hash": "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b",
    "prepared_votes": [],
    "commit_votes": [],
    "is_locked": false,
    "locked_block_hash": null,
    "is_stalled": false
  }
  ```

### 5.8 `GET /metrics`
- **Mục đích:** Phục vụ bài đo benchmark, latency và throughput (TV4).
- **Phản hồi 200 OK:**
  ```json
  {
    "node_id": "node1",
    "uptime_seconds": 3600.5,
    "committed_height": 500,
    "total_transactions_committed": 2500,
    "total_votes_sent": 1000,
    "total_votes_received": 3000,
    "stalled_count": 0,
    "equivocations_detected": 0
  }
  ```

---

## 6. Đặc tả Peer Wire Consensus Endpoints (P2P Protocols)

### 6.1 `POST /peer/propose`
- **Người gửi:** Leader (`node1`).
- **Người nhận:** Các Followers (`node2`, `node3`, `node4`).
- **Request Body (`ProposalMessage`):**
  ```json
  {
    "protocol_version": "1.0",
    "chain_id": "minivoting-dev",
    "height": 1,
    "view": 0,
    "block": {
      "header": {
        "height": 1,
        "prev_hash": "0000000000000000000000000000000000000000000000000000000000000000",
        "tx_list_hash": "4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce",
        "state_hash": "d4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35",
        "proposer_id": "node1",
        "timestamp": 1700000000
      },
      "transactions": []
    },
    "block_hash": "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b",
    "sender_id": "node1",
    "signature": "leader_signature_over_proposal"
  }
  ```
- **Xử lý:** Validator thẩm định chữ ký Leader, `prev_hash == tip_hash`, execute thử block để so khớp `state_hash` và `tx_list_hash`. Nếu hợp lệ, ghi Lock vào SQLite và phát `PREPARE`.
- **Phản hồi 202 Accepted:** `{"status": "proposal_accepted"}`.

### 6.2 `POST /peer/prepare`
- **Người gửi & nhận:** Mọi Validator phát tán đa hướng (Broadcast) cho nhau.
- **Request Body (`VoteMessage`):**
  ```json
  {
    "protocol_version": "1.0",
    "chain_id": "minivoting-dev",
    "height": 1,
    "view": 0,
    "phase": "PREPARE",
    "block_hash": "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b",
    "sender_id": "node2",
    "signature": "validator_signature_over_vote_context"
  }
  ```
- **Xử lý:** Kiểm tra chữ ký Ed25519 từ public key của `sender_id`.
  - Nếu trùng lặp cùng hash và chữ ký $\rightarrow$ Idempotent (bỏ qua, 202).
  - Nếu trùng `sender_id` nhưng khác `block_hash` $\rightarrow$ **Equivocation Detected!** Lưu bằng chứng vào SQLite, hủy tư cách Quorum của sender, trả `409 Conflict`.
  - Nếu gom đủ 3 phiếu hợp lệ $\rightarrow$ Tạo `PreparedCertificate`, ghi đĩa và phát `COMMIT`.
- **Phản hồi 202 Accepted:** `{"status": "prepare_vote_accepted"}`.

### 6.3 `POST /peer/commit`
- **Người gửi & nhận:** Mọi Validator broadcast cho nhau sau khi đạt pha PREPARED.
- **Request Body (`VoteMessage`):**
  Tương tự như `POST /peer/prepare`, với trường `"phase": "COMMIT"`.
- **Xử lý:** Gom đủ $\ge 3$ chữ ký COMMIT hợp lệ $\rightarrow$ Tạo `CommitCertificate`, thực hiện commit nguyên tử vào SQLite (chốt khối, cập nhật state, giải phóng lock, chuyển sang `height + 1`).
- **Phản hồi 202 Accepted:** `{"status": "commit_vote_accepted"}`.

### 6.4 `POST /peer/finalized` (Đồng bộ khối)
- **Mục đích:** Gửi khối đã chốt kèm `CommitCertificate` cho node bị tụt hậu (*Syncing*).
- **Request Body (`FinalizedBlockMessage`):** Chứa `block` đầy đủ và `certificate` gồm ít nhất 3 chữ ký.
- **Xử lý:** Node nhận tự kiểm chứng tính toàn vẹn của certificate và nội dung khối trước khi ghi vào SQLite cục bộ. Tuyệt đối không append mù.
- **Phản hồi 200 OK:** `{"status": "block_synced", "height": 1}`.

---

## 7. Giao diện Cơ sở dữ liệu SQLite cho TV3 (Storage Interface)

Nhằm đảm bảo quy tắc **Persist-Before-Send**, module Storage (`src/storage/`) do TV3 phụ trách sẽ khởi tạo và quản trị các bảng sau trong từng tệp SQLite riêng biệt (`data/{node_id}/ledger.db`):

```sql
-- 1. Bảng khóa đồng thuận bền vững
CREATE TABLE IF NOT EXISTS consensus_locks (
    height INTEGER PRIMARY KEY,
    locked_block_hash TEXT NOT NULL,
    locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bảng lưu phiếu bầu của chính mình (chống ký 2 lần sau restart)
CREATE TABLE IF NOT EXISTS consensus_votes (
    height INTEGER NOT NULL,
    phase TEXT NOT NULL,
    block_hash TEXT NOT NULL,
    signature TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (height, phase)
);

-- 3. Bảng lưu vết bằng chứng gian lận Byzantine Equivocation
CREATE TABLE IF NOT EXISTS consensus_equivocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    height INTEGER NOT NULL,
    phase TEXT NOT NULL,
    sender_id TEXT NOT NULL,
    vote_a_json TEXT NOT NULL,
    vote_b_json TEXT NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Bảng khối đã chốt (Committed Blocks)
CREATE TABLE IF NOT EXISTS blocks (
    height INTEGER PRIMARY KEY,
    block_hash TEXT NOT NULL UNIQUE,
    prev_hash TEXT NOT NULL,
    state_hash TEXT NOT NULL,
    tx_list_hash TEXT NOT NULL,
    proposer_id TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    certificate_json TEXT NOT NULL
);

-- 5. Bảng trạng thái số dư tài khoản
CREATE TABLE IF NOT EXISTS accounts (
    address TEXT PRIMARY KEY,
    balance INTEGER NOT NULL CHECK(balance >= 0),
    nonce INTEGER NOT NULL DEFAULT 0,
    updated_at_height INTEGER NOT NULL
);
```

---

## 8. Ma trận Kiểm tra Đối soát Nghiệm thu (DoD Verification)

| Tiêu chí | Mô tả tiêu chuẩn | Trạng thái | Minh chứng |
|---|---|:---:|---|
| **Bốn /health độc lập** | Trả đúng `node_id`, không khẳng định sai về quorum hay sync | **ĐẠT** | `tests/test_health.py`, `tests/test_node_endpoints.py` |
| **Dependency Lockfile** | Cài đặt tái lập được trên môi trường máy khác | **ĐẠT** | `requirements-lock.txt`, `pyproject.toml` |
| **Cô lập DB & Khóa** | 4 node dùng 4 thư mục riêng, không chia sẻ khóa hay SQLite file | **ĐẠT** | `tests/test_config.py`, `config/nodes.json`, `scripts/generate-dev-keys.py` |
| **Quản lý tiến trình an toàn** | Script chạy và dừng đúng 4 tiến trình, kiểm tra PID và CommandLine, không kill bừa | **ĐẠT** | `scripts/start-all-nodes.ps1`, `scripts/stop-all-nodes.ps1` |
| **Hợp đồng API & Wire Schema** | Đầy đủ 13 endpoint, định dạng lỗi chuẩn, hạn mức payload và timeout | **ĐẠT** | `docs/api-contract.md`, `src/api/schemas.py`, OpenAPI schema test |
