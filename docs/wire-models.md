# Mô hình dữ liệu và byte chuẩn MiniVoting v1

Tài liệu này định nghĩa dữ liệu mà ví CLI, core, consensus, storage và HTTP dùng
chung. Xem [hợp đồng HTTP](api-contract.md) về endpoint và mã lỗi. Phạm vi là
mạng bốn validator cố định, leader `node1`, quorum 3 và `view = 0`.

## 1. Kiểu và kiểm tra cơ bản

| Kiểu | Quy tắc v1 |
|---|---|
| `Version` | Số nguyên JSON đúng bằng `1` |
| `ChainId` | ASCII khớp toàn chuỗi với `[a-z0-9][a-z0-9_-]{0,63}`, đúng giá trị trong genesis được tin cậy |
| `NodeId` | Một trong `node1`, `node2`, `node3`, `node4` |
| `UInt` | Số nguyên JSON từ `0` đến `9007199254740991` (`2^53 - 1`), dạng thập phân; từ chối boolean, phân số, số mũ và `-0` |
| `PositiveUInt` | `UInt` từ `1` trở lên |
| `Hash32`, `Address`, `PublicKey32` | Chuỗi đúng 64 ký tự hex thường `[0-9a-f]`, không `0x`; khóa là 32 byte Ed25519 dạng raw |
| `Signature64` | Chuỗi đúng 128 ký tự hex thường `[0-9a-f]`, mã hóa 64 byte chữ ký Ed25519 `R || S` |
| `View` | Số nguyên JSON đúng bằng `0` |

Mọi trường trong các mô hình dưới đây đều bắt buộc và không nhận `null`. Từ chối
trường thừa và khóa JSON lặp ở mọi mức, kể cả khóa lặp sau khi giải mã escape.
Kiểm tra UTF-8 nghiêm ngặt rồi parse đúng một giá trị JSON, không BOM, không
`NaN` hoặc vô cực. Phát hiện khóa lặp và kiểu token số trước khi parser hoặc
schema tự đổi kiểu hay ghi đè giá trị. JSON HTTP có thể có khoảng trắng và thứ tự
khóa khác byte chuẩn.

## 2. Genesis và trạng thái tài khoản

`GenesisRecord` có đúng hai trường `genesis: Genesis` và `genesis_hash: Hash32`.
`Genesis` có các trường sau.

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `protocol_version`, `chain_id` | `Version`, `ChainId` | Dùng cho mọi đối tượng có context của mạng |
| `height`, `prev_hash` | `UInt`, `Hash32` | `0` và 64 ký tự `0` |
| `validators` | Danh sách `{node_id: NodeId, public_key: PublicKey32}` | Đúng bốn mục theo thứ tự `node1` đến `node4`, khóa công khai khác nhau |
| `leader_id`, `quorum` | `NodeId`, `PositiveUInt` | `node1` và `3` |
| `accounts` | Danh sách `AccountState` | Tăng dần theo `address`, mỗi địa chỉ xuất hiện một lần, `nonce = 0`, tổng `balance` không quá `2^53 - 1` |
| `max_block_bytes` | `PositiveUInt` | Giới hạn byte chuẩn của `Block` cho cả mạng, tối đa `262144` byte |
| `max_transactions_per_block` | `PositiveUInt` | Giới hạn số giao dịch trong một block cho cả mạng, tối đa `128` |

`AccountState` có `address: Address`, `balance: UInt`, `nonce: UInt`.
`genesis_hash = sha256_hex(canonical_bytes(genesis))`. TV1 tạo một genesis cho cả
mạng. Mỗi tiến trình so sánh hash tự tính với hash tin cậy do nhóm cấp ngoài
genesis và đối chiếu public key của nó với registry trước khi chạy. Địa chỉ,
cổng, đường dẫn SQLite và private key là cấu hình từng tiến trình. Genesis là
trạng thái đã chốt tại height `0`, không có proposal hoặc certificate. Hash
genesis là `tip_hash` lúc khởi tạo và là `prev_hash` của block height `1`.

## 3. Giao dịch và block

| Trường `Transaction` | Kiểu | Quy tắc |
|---|---|---|
| `protocol_version`, `chain_id` | `Version`, `ChainId` | Phải khớp genesis |
| `sender_public_key`, `sender` | `PublicKey32`, `Address` | `sender = sha256_hex(hex_decode(sender_public_key))`, tính trên 32 byte raw |
| `recipient` | `Address` | Địa chỉ nhận, được tạo với balance và nonce ban đầu bằng `0` khi áp dụng lần đầu |
| `amount`, `nonce` | `PositiveUInt`, `PositiveUInt` | Amount theo đơn vị coin nhỏ nhất; nonce bằng nonce gần nhất của sender cộng `1` |
| `tx_id`, `signature` | `Hash32`, `Signature64` | Tính bằng các phép ở mục 6 |

Nhận giao dịch vào mempool không đổi state. Khi thực thi block, kiểm tra chữ ký,
`tx_id`, số dư, nonce và trùng `tx_id`, rồi áp dụng lần lượt trên bản sao của
state tại `prev_hash`. Một giao dịch chuyển về cùng địa chỉ vẫn cần đủ số dư và
tăng nonce, với số dư ròng giữ nguyên. Mỗi giao dịch chỉ được áp dụng một lần,
không có phí hoặc phát hành coin sau genesis. Nonce phải liên tiếp kể cả khi
block chứa nhiều giao dịch của cùng sender. Giới hạn tiếp nhận tạm thời của
mempool không phải điều kiện hợp lệ của block.

`Block` có `header: BlockHeader`, `transactions: Transaction[]` và
`block_hash: Hash32`. Danh sách có từ 1 đến `max_transactions_per_block` mục. Tuân
thủ `max_block_bytes` trên byte chuẩn của toàn bộ `Block`.

| Trường `BlockHeader` | Kiểu | Quy tắc |
|---|---|---|
| `protocol_version`, `chain_id` | `Version`, `ChainId` | Phải khớp genesis |
| `height`, `prev_hash` | `PositiveUInt`, `Hash32` | Chiều cao khối trước cộng `1` và hash khối trước đã xác minh |
| `proposer_id` | `NodeId` | Bằng `leader_id` trong genesis |
| `timestamp_ms` | `UInt` | Unix epoch tính bằng mili giây, do leader điền để quan sát; không dùng giờ máy khi tái thực thi |
| `tx_list_hash`, `state_hash` | `Hash32`, `Hash32` | Tự tính lại theo mục 6, giữ thứ tự transaction |

## 4. Proposal, vote và certificate

`SignedContext` là phần chung của proposal và vote.

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `protocol_version`, `chain_id` | `Version`, `ChainId` | Phải khớp genesis |
| `height`, `view` | `PositiveUInt`, `View` | `height` là tên trường trên wire; vòng đang xử lý dùng `target_height = committed_height + 1` |
| `phase` | Enum | `PROPOSE`, `PREPARE` hoặc `COMMIT` tùy loại thông điệp |
| `block_hash` | `Hash32` | Hash của block được đề xuất hoặc bỏ phiếu |
| `sender_id` | `NodeId` | Tra khóa trong registry genesis, không lấy khóa tự khai trong thông điệp |

- `Proposal` là `SignedContext` với `phase = PROPOSE`, thêm `signature: Signature64`
  và `block: Block` ở cùng cấp. `sender_id` bằng leader và `header.proposer_id`.
  `protocol_version`, `chain_id`, `height` và `block_hash` phải khớp các trường
  tương ứng trong block. Chữ ký bao phủ context đầy đủ, còn `block_hash` cam kết
  header và nội dung qua các phép băm ở mục 6. Bên nhận xác minh cả hai. Khi ký
  hoặc xác minh, lấy đúng bảy trường `SignedContext`; trường `block` và
  `signature` cùng cấp thuộc envelope. Mục 6 có phép chiếu trường cụ thể.
- `Vote` là `SignedContext` với `phase = PREPARE` hoặc `COMMIT`, thêm
  `signature: Signature64` ở cùng cấp. Gửi trực tiếp trong body của endpoint pha
  tương ứng. Validator kiểm đầy đủ context, danh tính và chữ ký trước khi đưa vote
  vào quorum. Khi gặp hai vote hợp lệ có cùng context và người ký nhưng khác
  `block_hash`, lưu cả cặp vote có chữ ký làm bằng chứng.
- `PreparedCertificate` và `CommitCertificate` có cùng cấu trúc gồm
  `protocol_version: Version`, `chain_id: ChainId`, `height: PositiveUInt`,
  `view: View`, `block_hash: Hash32` và `signatures: object<NodeId, Signature64>`.
  Cần 3 hoặc 4 khóa khác nhau trong registry. Với từng mục, dựng lại
  `SignedContext` từ các trường của certificate, lấy `sender_id` theo khóa map,
  ấn định `phase = PREPARE` cho `PreparedCertificate` hoặc `phase = COMMIT` cho
  `CommitCertificate`, rồi xác minh chữ ký tương ứng. Tất cả mục đều phải hợp lệ,
  cả khi đã có đủ ba mục. Loại certificate nếu thiếu quorum, sai context hoặc có
  khóa hay chữ ký không hợp lệ. Danh tính dùng để đếm là `NodeId`, không phải
  chuỗi chữ ký hay số lượt gửi.

`FinalizedBlock` có `proposal: Proposal` và `certificate: CommitCertificate`.
Mọi trường context chung của certificate phải khớp proposal. Ghi hoặc đồng bộ
block chỉ sau khi xác minh proposal, liên kết hash, thực thi lại và xác minh
certificate. `PreparedCertificate` là điều kiện để validator tự ký COMMIT.
Peer đồng bộ xác minh `FinalizedBlock` bằng `CommitCertificate`. Certificate
đứng ngoài `Block` và không tham gia `block_hash`. Hai certificate hợp lệ với
tập chữ ký khác nhau vẫn có thể chứng nhận cùng block.

Đường nhận `POST /peer/finalized` và đồng bộ dùng cùng điều kiện xác minh. Với
block kế tiếp tip, node được ghi kết quả sau khi đã kiểm đầy đủ proposal, hash,
chữ ký giao dịch, thực thi lại trên committed state và commit certificate,
kể cả khi node chưa có own vote hoặc prepared certificate. Điều kiện ghi nguyên
tử và phân loại height nằm trong [hợp đồng HTTP](api-contract.md#nhận-block-đã-chốt).

## 5. Chuẩn hóa byte JSON

`canonical_bytes(value)` nhận giá trị đã kiểm kiểu. Từ chối dữ liệu sai schema
trước khi băm hay ký. Duyệt đệ quy và sắp khóa object tăng dần theo thứ tự byte
ASCII. Giữ thứ tự array. Encoder dùng UTF-8 không BOM, `,` và `:` không kèm
khoảng trắng, không chèn khoảng trắng hay newline đầu/cuối. Số nguyên ở dạng
thập phân ngắn nhất và dạng `0` cho số không. Kiểu chuỗi của các đối tượng băm
và ký đều dùng tập ký tự ASCII xác định tại mục 1–4. Ví dụ Python cho dữ liệu đã
qua validate.

```python
json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
```

Bên nhận ký hoặc xác minh trên byte chuẩn được dựng lại từ dữ liệu đã kiểm,
không dùng chuỗi HTTP thô. Core, transport, storage và công cụ ví dùng cùng quy
tắc serialize và xác minh. Dashboard đọc dữ liệu quan sát từ API.

## 6. Quy tắc băm và ký

`sha256_hex(data)` là SHA-256 trên chuỗi byte `data`, kết quả thành chuỗi hex
thường. `TxFields` gồm đúng `protocol_version`, `chain_id`, `sender_public_key`,
`sender`, `recipient`, `amount` và `nonce`. `SignedContext` là đúng bảy trường
ở mục 4.

| Giá trị | Tính trên dữ liệu |
|---|---|
| `tx_id` | `sha256_hex(canonical_bytes(TxFields))` |
| `tx_list_hash` | `sha256_hex(canonical_bytes(transactions))`, gồm transaction đầy đủ với `tx_id` và `signature` |
| `state_hash` | `sha256_hex(canonical_bytes(accounts))`, danh sách toàn bộ `AccountState` sau thực thi, tăng dần theo `address`, gồm cả tài khoản số dư `0` còn trong state |
| `block_hash` | `sha256_hex(canonical_bytes(header))` |

Chuỗi byte cần ký là `ASCII("MINIVOTING-V1/" + domain) || 0x00 || canonical_bytes(fields)`.
`0x00` là đúng một byte NUL. Domain `TX` dùng `TxFields`. Các domain `PROPOSE`,
`PREPARE`, `COMMIT` dùng `SignedContext` có `phase` cùng tên. `signature` và
`tx_id` không nằm trong `TxFields`. `signature` và phần `block` đính kèm không nằm
trong `SignedContext`. Dùng Ed25519 theo [RFC 8032 §5.1](https://www.rfc-editor.org/rfc/rfc8032.html#section-5.1)
trên toàn bộ chuỗi byte này, truyền thẳng vào API signer/verifier của thư viện
trong chế độ Ed25519 thông thường. Dùng khóa của sender cho TX và khóa validator
trong genesis cho các pha đồng thuận.

Phép chiếu cho Proposal đã qua kiểm tra toàn bộ schema được xác định như sau.

```python
context_fields = (
    "protocol_version", "chain_id", "height", "view",
    "phase", "block_hash", "sender_id",
)
fields = {name: proposal[name] for name in context_fields}
message_bytes = b"MINIVOTING-V1/PROPOSE\x00" + canonical_bytes(fields)
```

Phần `block` được kiểm riêng bằng cách tính lại `tx_list_hash`, `state_hash` và
`block_hash`, rồi so với SignedContext và certificate. Chữ ký context hợp lệ
cùng một attachment bị sửa vẫn phải bị loại khi kiểm dữ liệu block. Fixture và
script kiểm chứng có tình huống này, đồng thời kiểm việc đưa cả attachment vào
bytes ký sẽ không khớp chữ ký mẫu.

Quy tắc này cụ thể hóa yêu cầu ký full context và phân tách domain trong
[kế hoạch §7.4–7.5](ke-hoach.md#74-thông-điệp-đồng-thuận). Khi duyệt
[PR #25](https://github.com/DaoNgocDinh/BlockChain_MiniVoting/pull/25), cần đồng bộ
ví dụ ký `PROPOSE` chỉ trên `block_hash` và `Vote` trên JSON không có tiền tố
domain với quy tắc trên. Cấu trúc vote và map chữ ký certificate giữ theo PR đó.

## 7. Dữ liệu kiểm chứng liên module

[Fixture wire-v1](fixtures/wire-v1.json) có genesis public, giao dịch ký sẵn,
trạng thái sau khi thực thi, đề xuất block, phiếu, certificate, byte chuẩn và byte
ký tham chiếu. Bộ này dùng cho kiểm tra tương thích, không dùng làm genesis triển
khai. Chạy `node scripts/verify-wire-v1.mjs` từ thư mục gốc để đối chiếu byte, hash
và chữ ký bằng thư viện chuẩn Node. TV1 và TV2 dùng cùng fixture để kiểm tra đổi
thứ tự khóa (T01) và ngăn tái sử dụng chữ ký giữa phase, height, view, chain hoặc
version (T14).
