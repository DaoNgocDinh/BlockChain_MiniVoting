# Hợp đồng giao tiếp MiniVoting v1

**Trạng thái:** đề xuất để cả nhóm review. **Chủ trì:** TV3, phối hợp TV1 (core), TV2 (consensus) và TV4 (dashboard, kiểm thử, thực nghiệm). Phạm vi là mạng demo bốn validator, leader cố định `node1`, ba pha PROPOSE → PREPARE → COMMIT, quorum 3/4, `view = 0`.

Tài liệu này quy định giao tiếp HTTP. [Mô hình dữ liệu và chữ ký](wire-models.md) quy định dữ liệu trên dây, bytes ký/băm và fixture. [Interface giữa các module](module-interfaces.md) quy định trách nhiệm, điểm ghi bền vững, đồng bộ và phục hồi. [Kế hoạch](ke-hoach.md) mục 7–11 và 16–17 là căn cứ thiết kế. Hai route có trong scaffold là `GET /health` và `GET /status` trả 503. Các route khác và phản hồi 200 của `/status` là mục tiêu triển khai.

## 1. Quy ước HTTP

- Cổng mặc định theo [topology](../config/nodes.json) là 8001–8004. Ví, dashboard và peer gọi cùng API của từng node. Giao thức dành cho mạng demo được kiểm soát. Xác thực phiếu bằng khóa công khai từ genesis cục bộ. Host, IP, ID tự khai và thông tin ở API quan sát chỉ dùng để định tuyến hoặc hiển thị.
- Request có body dùng `Content-Type: application/json`, UTF-8. Chỉ nhận `Content-Encoding: identity` hoặc không gửi header này. Kiểm số byte thực đọc trước khi parse. Giới hạn 4 KiB cho giao dịch và vote, 512 KiB cho proposal và thông báo finalized. Giới hạn byte của Block chuẩn hóa và số giao dịch một block lấy từ genesis trong trần v1.
- Dùng `snake_case`. Trừ field được ghi nullable, field đã khai báo là bắt buộc và không nhận `null`. Kiểm kiểu chặt, từ chối key lặp và field lạ với các đối tượng wire. Không nhận bool, float hoặc chuỗi thay cho số nguyên trong JSON. Query/path số dùng chữ số thập phân không dấu, trong khoảng tương ứng. Hash, địa chỉ, chữ ký và ID tuân theo mô hình wire.
- `uint` là `UInt` trong mô hình wire. `target_height = committed_height + 1`. Các timestamp hậu tố `_ms` dùng mili giây Unix UTC theo đồng hồ node quan sát. `timestamp_ms` trong header tham gia hash của block và không tham gia tính toán state.
- API trả JSON và `Cache-Control: no-store` cho dữ liệu động. Đọc các field đã chốt trong một snapshot cục bộ nhất quán. Các node có thể báo khác nhau trong lúc đồng bộ. Đăng ký hai route tĩnh `/consensus/proposal`, `/consensus/status` trước route động `/consensus/{height}` trong FastAPI.

### Lỗi dùng chung

```json
{"detail":{"code":"CONSENSUS_NOT_READY","message":"Consensus and persistent ledger are not implemented yet."}}
```

`detail.code` là mã máy đọc. `detail.message` dành cho người đọc. Khi hữu ích, `detail.fields` là danh sách lỗi theo trường dạng `{path: string, reason: string}`, với `path` là JSON Pointer hoặc tên query/path parameter. Client dựa vào mã, không so chuỗi thông báo. Xử lý lỗi validation của FastAPI theo envelope này khi triển khai các route v1.

| HTTP | Mã | Hành vi |
|---|---|---|
| 400 | `MALFORMED_JSON` | JSON sai cú pháp, UTF-8 sai hoặc key lặp |
| 404 | `BLOCK_NOT_FOUND`, `PROPOSAL_NOT_FOUND`, `ROUND_NOT_FOUND` | Node chưa có dữ liệu được yêu cầu |
| 409 | `CONTEXT_MISMATCH`, `HEIGHT_AHEAD`, `PROPOSAL_CONFLICT`, `VOTE_CONFLICT`, `NONCE_CONFLICT`, `INSUFFICIENT_FUNDS`, `PENDING_CONFLICT` | Dữ liệu xung đột với round, lock hoặc trạng thái cục bộ. Lấy trạng thái trước khi quyết định retry |
| 413 | `PAYLOAD_TOO_LARGE` | Vượt giới hạn body hoặc block |
| 415 | `UNSUPPORTED_MEDIA_TYPE`, `UNSUPPORTED_CONTENT_ENCODING` | Kiểu nội dung hoặc cách mã hóa không hỗ trợ |
| 422 | `INVALID_REQUEST`, `INVALID_TRANSACTION`, `INVALID_SIGNATURE`, `INVALID_BLOCK`, `INVALID_CERTIFICATE`, `UNAUTHORIZED_VALIDATOR` | Kiểu, cấu trúc, hash, chữ ký hoặc bằng chứng không hợp lệ. Sửa dữ liệu trước khi gửi lại |
| 429 | `MEMPOOL_FULL`, `EARLY_BUFFER_FULL` | Hàng đợi nhận đã đầy. Có thể gửi lại sau với backoff |
| 503 | `CONSENSUS_NOT_READY`, `NODE_SYNCING`, `NODE_HALTED` | Node chưa phục vụ thao tác này. `NODE_HALTED` cần điều tra trước khi chạy lại |

Khi trả `429`, node gửi `Retry-After` theo giây (mặc định 2). Lỗi 5xx ngoài bảng và lỗi mạng được client hiển thị như lỗi tạm thời. Chi tiết nội bộ ghi log; không đưa khóa, stack trace hay đường dẫn máy vào API.

## 2. Endpoint cho ví, dashboard và công cụ

| Method và route | Request | Response thành công hoặc chưa sẵn sàng | Trường hợp riêng |
|---|---|---|---|
| `GET /health` | Không body/query | 200 `Health` | Khi tiến trình đáp ứng, không phụ thuộc quorum/peers |
| `GET /status` | Không body/query | 200 `NodeStatus`, 503 với envelope lỗi | Scaffold trả `CONSENSUS_NOT_READY`. Node đã khởi tạo có thể báo `SYNCING` hoặc `STALLED` bằng 200 |
| `POST /transactions` | `Transaction` đã ký | 202 `TxSubmission` nếu nhận mới/còn chờ. 200 nếu ID đã chốt | 409 nonce, tiền hoặc trùng giao dịch chờ khác ID. 422 sai dữ liệu/chữ ký. 429 quá tải. 503 chưa nhận được giao dịch ở trạng thái hiện tại |
| `GET /transactions/{tx_id}` | `tx_id: Hash32` | 200 `TxLookup` | ID đúng định dạng chưa biết tại node vẫn trả 200 `local-unknown` |
| `GET /accounts/{address}` | `address: Hash32` | 200 `AccountView` | Địa chỉ hợp lệ chưa có trên ledger có `balance = 0`, `nonce = 0` |
| `GET /blocks` | `from_height?: uint`, mặc định 0. `limit?: int` từ 1 đến 50, mặc định 20 | 200 `BlockPage` | Thứ tự height tăng, bắt đầu từ `from_height` (bao gồm). Trang rỗng nếu bắt đầu sau tip |
| `GET /blocks/{height}` | `height: uint` | 200 `BlockRecord` | 404 nếu height chưa chốt ở node. Height 0 trả genesis |
| `GET /consensus/{height}` | `height: uint` lớn hơn 0 | 200 `ConsensusView` | Hỗ trợ round hiện tại và block dương đã chốt. 404 cho round ngoài phạm vi cục bộ |
| `GET /metrics` | Không body/query | 200 `Metrics` | Bộ đếm thuộc tiến trình, có thể đọc khi chưa sẵn sàng |

Các request GET không được gửi body. Query ngoài bảng và tham số sai kiểu trả `422 INVALID_REQUEST`. Khi chưa mở sổ cái, các route đọc ledger và round trả 503. Khi đang sync, route đọc ledger tiếp tục dùng snapshot đã chốt gần nhất nếu còn đọc được. Khi dữ liệu không thể đọc an toàn, trả `503 NODE_HALTED`.

### Health và trạng thái node

```json
{"status":"ok","node_id":"node1","consensus_ready":false}
```

`Health.consensus_ready` cho biết node đã khởi tạo genesis, mở kho dữ liệu và có khả năng tham gia consensus tại thời điểm đọc. Đặt `false` khi chưa khởi tạo, đang sync hoặc halt. Giá trị này không suy ra quorum.

`NodeStatus` gồm `protocol_version: Version`, `chain_id: ChainId`, `node_id: NodeId`, `leader_id: NodeId`, `committed_height: uint`, `tip_hash: Hash32`, `target_height: uint`, `consensus_state: ConsensusState`, `phase: Phase | null`, `sync_state: "SYNCED" | "SYNCING"`, `observed_at_ms: uint`. `tip_hash` ở height 0 là `genesis_hash`. `SYNCED` nghĩa là node chưa biết bằng chứng hợp lệ cho tip cao hơn cần đồng bộ. Các enum trạng thái và ý nghĩa nằm trong [interface module](module-interfaces.md).

`Phase` là `PROPOSE | PREPARE | COMMIT`. `phase` thuộc round hiện tại. Dùng PROPOSE lúc chờ hoặc xác thực proposal, PREPARE lúc gom phiếu prepare, COMMIT từ khi đã prepared và bắt đầu commit. STALLED giữ phase bị kẹt, LEADER_UNAVAILABLE giữ PROPOSE, INITIALIZING và SYNCING dùng `null`. Một node halt trả 503 cho `/status`.

### Nhận và tra cứu giao dịch

- `TxSubmission = {tx_id: Hash32, admission: "accepted" | "already-known", status: "pending" | "proposed" | "committed", observed_node_id: NodeId}`. Gửi lại cùng `tx_id` với dữ liệu hợp lệ trả `already-known`. Cả ví lẫn follower phải gửi lại cùng giao dịch đã ký khi kết quả gửi chưa rõ. Node vẫn xác thực giao dịch trước khi xử lý trùng. Sau ghi sổ, `tx_id` chỉ được áp dụng một lần.
- Node kiểm tra giao dịch theo snapshot đã chốt, một giao dịch chờ mỗi sender và giới hạn dung lượng mempool tối đa 1.024 giao dịch. V1 nhận nonce kế tiếp và số dư đủ. Định nghĩa thực thi block theo thứ tự ở core vẫn áp dụng cho nhiều giao dịch của cùng sender trong block.
- Follower nhận và xếp hàng chuyển tiếp đúng bytes giao dịch đã ký tới leader qua `POST /transactions`. Leader là điểm nhận cuối. 202 xác nhận node nhận cục bộ, có thể mất khi khởi động lại nếu chưa chốt. Follower dùng HTTP timeout 1 giây mỗi lần, tối đa 5 lần retry sau lần đầu cho lỗi mạng/429/503/5xx, với backoff từ 0,5 giây, nhân đôi đến trần 5 giây và tôn trọng `Retry-After` trong thời hạn hàng đợi. 4xx khác là phản hồi cuối của lượt chuyển tiếp. Hàng đợi forward không vượt giới hạn mempool, không có luồng forward đệ quy.
- `TxLookup = {tx_id: Hash32, status: TxStatus, observed_node_id: NodeId, height: uint | null, block_hash: Hash32 | null, reason: string | null}`. Chọn trạng thái theo thứ tự kiểm tra sau.

| `TxStatus` | Điều kiện tại node | `height` và `block_hash` | `reason` |
|---|---|---|---|
| `committed` | Đã có chỉ mục giao dịch đã chốt và block kèm certificate | Block đã chốt | `null` |
| `proposed` | Có trong proposal hợp lệ đã lưu của round đang xử lý | Block đề xuất | `null` |
| `pending` | Đang chờ tại mempool cục bộ | `null` | `null` |
| `rejected` | Node từng nhận rồi loại, còn dấu vết cục bộ | `null` | Mã lý do, ví dụ `NONCE_CONFLICT`, `INSUFFICIENT_FUNDS` hoặc `MEMPOOL_EXPIRED` |
| `local-unknown` | Node không giữ thông tin của ID | `null` | `null` |

Giao dịch đang chờ mà chưa vào proposal hết hạn sau 300 giây kể từ lần nhận gần nhất vào mempool. Dấu vết loại giữ tối đa 300 giây và 1.024 mục, bỏ mục cũ nhất khi đầy. Dấu vết này không ngăn nhận lại cùng giao dịch còn hợp lệ. Một lỗi trả ngay lúc submit hoặc việc follower hết lượt chuyển tiếp không tạo trạng thái `rejected`. Client có thể gửi lại tới leader. Khi sổ cái ghi thành công, `committed` ưu tiên hơn mọi trạng thái cục bộ trước đó.

```json
{"tx_id":"0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef","admission":"accepted","status":"pending","observed_node_id":"node2"}
```

### Ledger và phân trang

- `AccountView = {account: AccountState, committed_height: uint, tip_hash: Hash32}`. Số dư và nonce chỉ lấy từ committed state.
- `BlockRecord` là `GenesisRecord` ở height 0 hoặc `FinalizedBlock` ở height dương. Có thể phân biệt bằng top-level `genesis` hoặc `proposal`. Mỗi block dương trả đầy đủ proposal, giao dịch và commit certificate. Sync kéo từng height bằng route chi tiết.
- `BlockPage = {items: BlockSummary[], next_from_height: uint | null, committed_height: uint}`. `BlockSummary = {height: uint, block_hash: Hash32, timestamp_ms: uint | null, transaction_count: uint}`. Genesis có `block_hash = genesis_hash`, `timestamp_ms = null`, `transaction_count = 0`. `next_from_height` bằng height cuối + 1 nếu còn dữ liệu trong snapshot; nếu hết trang ở tip hoặc rỗng thì `null`.

### Quan sát đồng thuận

- `RoundStatus = {node_id: NodeId, height: uint, committed_height: uint, target_height: uint, consensus_state: ConsensusState, phase: Phase | null, proposal_hash: Hash32 | null, prepare_count: uint, commit_count: uint, is_locked: bool, observed_at_ms: uint}`. `consensus_state`, `phase`, counts, proposal và lock mô tả **height được hỏi**. Với height đã chốt dùng `DECIDED`, `COMMIT`, `prepare_count = 0` nếu không còn bằng chứng PREPARE tại node, `commit_count` bằng số chữ ký certificate và `is_locked = false`.
- `ConsensusView = {round: RoundStatus, proposal: Proposal | null, prepare_voter_ids: NodeId[], commit_voter_ids: NodeId[], certificate: CommitCertificate | null, events: VoteEvent[]}`. Danh sách ID phân biệt, sắp xếp tăng dần, dài đúng count tương ứng. Với height đã chốt, COMMIT IDs lấy từ certificate.
- `VoteEvent = {seq: uint, observed_at_ms: uint, peer_id: NodeId | null, sender_id: NodeId | null, phase: "PREPARE" | "COMMIT", block_hash: Hash32 | null, outcome: "valid" | "invalid" | "duplicate" | "buffered" | "equivocation", reason: string | null}`. `seq` tăng trong một lần chạy, events sắp tăng theo `seq`. Giữ tối đa 100 event mới nhất của round hiện tại trong bộ nhớ. Sau restart hoặc với height đã chốt có thể trả danh sách rỗng. `sender_id` ở event invalid là giá trị khai báo hợp lệ về hình thức nếu parse được. Không hiển thị như validator đã xác minh. Evidence cần giữ bền vững theo interface module.
- Dashboard có thể polling khoảng 1 giây, hiển thị node nguồn và thời điểm quan sát. Sự kiện và số phiếu là dữ liệu tại node. Badge giao dịch chỉ hiển thị committed khi API đọc được bản ghi đã chốt. Kịch bản mock phải có nhãn và không trộn với trạng thái node thật.

### Metrics phục vụ thực nghiệm

`Metrics = {node_id: NodeId, process_started_at_ms: uint, observed_at_ms: uint, transactions: TxCounters, peer: PeerCounters}`. `TxCounters = {submitted: uint, admitted: uint, rejected: uint, committed: uint}`. Đếm mọi lượt POST tới route giao dịch, lượt nhận ID mới vào mempool, lượt POST bị node từ chối và số lần giao dịch lần đầu ghi sổ trong tiến trình (tính cả sync, không tính genesis). Lượt duplicate hợp lệ không tăng admitted/rejected.

`PeerCounters` có bốn key `propose`, `prepare`, `commit`, `finalized`. Mỗi key trả `{sent: uint, received: uint, retry_sent: uint, sent_bytes: uint, received_bytes: uint}`. `sent` đếm từng lần gửi tới một peer kể cả retry, `retry_sent` là tập con. Bytes tính phần body gửi hoặc nhận, không tính header. Workload runner đo latency từ lần gửi giao dịch đến lúc quan sát committed trên cùng đồng hồ đơn điệu của client. TPS tính từ ID giao dịch duy nhất chốt trong cửa sổ đo.

## 3. Endpoint giữa validator

| Method và route | Request | Response | Hành vi |
|---|---|---|---|
| `POST /peer/propose` | `Proposal` | 200 `PeerReceipt` | Chỉ nhận chữ ký leader đúng context, block hợp lệ. Lưu proposal đã xác thực trước khi dùng |
| `POST /peer/prepare` | `Vote` có phase PREPARE | 200 hoặc 202 `PeerReceipt` | Xác thực, chống đếm trùng. Có thể đệm phiếu đến sớm |
| `POST /peer/commit` | `Vote` có phase COMMIT | 200 hoặc 202 `PeerReceipt` | Xác thực, chống đếm trùng. Chỉ chốt khi đủ điều kiện trong đặc tả |
| `POST /peer/finalized` | `FinalizedBlock` | 200 hoặc 202 `PeerReceipt` | Node kiểm chứng proposal, certificate và block. Nếu đến trước quá một height, kích hoạt đồng bộ tuần tự |
| `GET /consensus/proposal?height=H` | `H: uint` lớn hơn 0 | 200 `Proposal` | Trả proposal hợp lệ đã lưu cho round hoặc block đã chốt. Nếu chưa có, 404 `PROPOSAL_NOT_FOUND` |
| `GET /consensus/status?height=H` | `H: uint` lớn hơn 0 | 200 `RoundStatus` | Dùng cho thăm dò khi STALLED. 404 `ROUND_NOT_FOUND` nếu không có round yêu cầu. 404 chỉ là dữ liệu thiếu tại peer |

`PeerReceipt = {node_id: NodeId, height: uint, outcome: "accepted" | "duplicate" | "buffered" | "ignored-stale" | "applied" | "sync-required"}`.

- `accepted` là proposal/vote được nhận để xử lý, `duplicate` là lặp cùng thông điệp, `ignored-stale` là proposal/vote thuộc height cũ, và `applied` xác nhận đã ghi atomically block + certificate + state. Bốn outcome này dùng HTTP 200. Phiếu tới sớm được đệm có giới hạn trả 202 `buffered`. Finalized còn thiếu block trước đó trả 202 `sync-required` sau kiểm tra cấu trúc và chứng cứ tĩnh. Đây là gợi ý để tải block thiếu, không được dùng để nhảy height.
- Wrong chain/version/view/phase trả 409 `CONTEXT_MISMATCH`. Proposal/vote ở height tương lai trả 409 `HEIGHT_AHEAD`; không lưu buffer cho height tương lai. Chỉ giữ tối đa 50 phiếu đến sớm đã qua xác thực cơ bản ở target hiện tại. Nếu phát hiện vote ký hai hash cho cùng context, lưu bằng chứng rồi trả 409 `VOTE_CONFLICT`. Một proposal hợp lệ xung đột lock trả 409 `PROPOSAL_CONFLICT`.
- Với finalized trùng hash ở height đã chốt, kiểm chữ ký và điều kiện proof rồi trả 200 `duplicate`. Nếu có proof hợp lệ cho hai hash khác nhau tại cùng height đã chốt cục bộ, halt, ghi bằng chứng và trả 503 `NODE_HALTED`. Nếu chỉ có lock của proposal chưa chốt, vẫn có thể nhận block đã có proof hợp lệ sau khi kiểm đầy đủ và áp dụng atomically.
- Đồng bộ và retry không cấp quyền ký giá trị mới ở cùng height. Khi STALLED, phát lại phiếu đã lưu theo lịch trong [interface module](module-interfaces.md). Trạng thái/counter nhận qua GET chỉ là gợi ý. Validate lại từng dữ liệu lấy từ peer trước khi nâng committed height.

## 4. Đối chiếu PR protocol và nghiệm thu

Bản này đề xuất giữ `height` trên wire và `target_height` trong trạng thái chạy. Kế thừa định dạng vote/certificate và hai route kéo dữ liệu từ [PR #25](https://github.com/DaoNgocDinh/BlockChain_MiniVoting/pull/25). Theo kế hoạch mục 7.4–7.5, đề xuất ký trọn context PROPOSE và dùng miền ký riêng theo thông điệp. TV1/TV2 cần đồng bộ tài liệu protocol với quy tắc byte chính xác ở đây. TV2/TV3 cần xác nhận phát lại cả PREPARE và COMMIT đã lưu, để phục hồi cả trường hợp các node đang kẹt ở các pha khác nhau. TV3/TV4 cần xác nhận enum và response quan sát dùng được cho wireframe và thực nghiệm.

Khi triển khai, dùng fixture chung để kiểm canonical bytes, hash và chữ ký. Thêm kiểm tra round-trip wire, mã lỗi, retry/idempotency, phân trang, xử lý phiếu sai pha/đến sớm, khởi động lại và sync theo ma trận T01–T30. Bằng chứng tích hợp cần ghi commit, kịch bản và kết quả thực chạy.
