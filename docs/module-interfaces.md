# Hợp đồng giao tiếp giữa các module MiniVoting v1

Đề xuất W1 để TV1, TV2, TV3 và TV4 review. Kiểu dữ liệu trao đổi và quy tắc ký nằm trong [mô hình wire](wire-models.md). Method, URL, schema HTTP và mã lỗi nằm trong [hợp đồng API](api-contract.md). Các chữ ký hàm bên dưới là giao diện đề xuất cho phần triển khai sau W1.

## 1. Trách nhiệm và cách gọi

| Chủ trì | Module | Trách nhiệm và giới hạn |
|---|---|---|
| TV1 | `src/core` | Chuẩn hóa, băm, xác minh chữ ký, kiểm và thực thi giao dịch hoặc block trên snapshot chỉ đọc. Hàm thuần, không đọc đồng hồ, DB hay mạng. |
| TV2 | `src/consensus` | Xử lý sự kiện tuần tự, kiểm context, gom vote, tạo và kiểm certificate, ra quyết định lưu trước khi gửi. Dùng đồng hồ đơn điệu cho timeout và nhận thời gian hiển thị từ tầng ngoài. |
| TV3 | `src/storage` | Snapshot nhất quán, giao dịch SQLite nguyên tử, kiểm tra điều kiện ghi, chỉ mục giao dịch và phục hồi. Mỗi node dùng đường dẫn DB riêng. |
| TV3 | `src/network`, `src/api` | Parse và giới hạn request, xác thực theo genesis, chuyển vào consensus hoặc truy vấn snapshot, chuyển kết quả/lỗi thành HTTP. Client peer dùng registry trong cấu hình, không suy diễn danh tính từ IP hay dữ liệu tự khai. |
| TV4 | `frontend`, `tests/integration`, `experiments` | Đọc DTO công khai và ghi nhận node nguồn của trạng thái. Chỉ số, mô phỏng giao diện và việc gửi lại của client không tạo vote hay thay đổi sổ cái. |

`ChainContext` chứa genesis đã kiểm, `genesis_hash`, `protocol_version = 1`, `chain_id`, public key của đúng bốn validator và leader cố định `node1`. `LedgerSnapshot` chứa `committed_height`, `tip_hash`, `state_hash` và `accounts`, đọc trong cùng một snapshot. Khối tiếp theo có `target_height = committed_height + 1`. Tên trường chiều cao trong thông điệp ký là `height`, còn `target_height` dùng để kiểm khớp vòng đang xử lý. `view` luôn bằng `0`.

Các hàm thuần có thể trả `ValidationError(code)` với lý do ổn định từ hợp đồng API. Các điều kiện cạnh tranh hợp lệ được trả thành kết quả có kiểu như `DUPLICATE`, `STALE`, `CONFLICT` hoặc `APPLIED`. Lỗi I/O là `StorageUnavailable`, độc lập với lỗi dữ liệu nghiệp vụ. Transport phân biệt timeout/lỗi kết nối với phản hồi ứng dụng của peer để biết khi nào được thử lại. Chỉ trả dữ liệu công khai ra HTTP. Log cục bộ có node, height, phase, mã lý do và hash liên quan.

## 2. Giao diện Core và Consensus

```python
# TV1 · src/core
canonical_bytes(value: WireObject) -> bytes
hash_transaction(tx: Transaction) -> Hash32
verify_signature(public_key: PublicKey32, message_bytes: bytes, signature: Signature64) -> bool
verify_transaction(tx: Transaction, context: ChainContext) -> None
execute_block(snapshot: LedgerSnapshot, transactions: Sequence[Transaction],
              context: ChainContext) -> ExecutionResult
validate_block(block: Block, snapshot: LedgerSnapshot,
               context: ChainContext) -> ExecutionResult

# TV2 · src/consensus
verify_proposal(proposal: Proposal, context: ChainContext) -> None
verify_vote(vote: Vote, context: ChainContext, *, expected_height: int,
            expected_phase: VotePhase) -> None
build_certificate(votes: Sequence[Vote], context: ChainContext, *, height: int,
                  phase: VotePhase, block_hash: Hash32) -> Certificate
verify_certificate(cert: Certificate, context: ChainContext, *, height: int,
                   phase: VotePhase, block_hash: Hash32) -> None
on_proposal(proposal: Proposal) -> IngressResult
on_vote(vote: Vote) -> IngressResult
on_finalized(finalized: FinalizedBlock) -> IngressResult
on_timer(token: TimerToken) -> None
```

`verify_transaction` xác minh phần tĩnh của giao dịch. `execute_block` áp dụng theo thứ tự danh sách trên bản sao snapshot và trả `ExecutionResult` gồm `state_hash`, tài khoản thay đổi và `tx_id` theo thứ tự. Mỗi giao dịch được kiểm số dư, nonce, giới hạn và quy tắc bảo toàn tổng cung trên trạng thái sau các giao dịch trước nó. `validate_block` chạy lại phép tính, kiểm `height`, `prev_hash`, `block_hash`, `tx_list_hash`, `state_hash` và giới hạn. API không tự áp dụng giao dịch. Chỉ đường commit ở mục 3 được ghi số dư và nonce chính thức.

`verify_proposal` kiểm chữ ký của leader, context và khớp dữ liệu block đính kèm. Gọi tiếp `validate_block` với snapshot đã chốt thích hợp trước khi PREPARE hay ghi sổ. `verify_vote` kiểm version, chain, height, view, phase, validator trong genesis và chữ ký trước khi lưu đệm hoặc đưa vào `VoteSet`. Mỗi `VoteSet` có `block_hash` mục tiêu và chỉ đếm tối đa một phiếu khớp trên mỗi `sender_id`. `verify_certificate` dựng lại thông điệp ký từ từng signer và context, kiểm mỗi chữ ký hiện diện, tối thiểu ba signer khác nhau, cùng hash và pha mong đợi. Certificate không tham gia tính `block_hash`.

Một node trung thực ghi và gửi own COMMIT sau khi có `PreparedCertificate` hợp lệ từ ba PREPARE. Nhánh đồng thuận cục bộ đệm COMMIT đến sớm cho đến khi có block hợp lệ và đã ghi own COMMIT. Đường nhập `FinalizedBlock` từ peer hoặc sync luôn tự xác minh cả proposal, block và certificate. Node có thể nhập kết quả đã chốt hợp lệ mà không cần tạo own vote hay có `PreparedCertificate` cục bộ. Dùng chung đường `apply_committed_block` sau khi kiểm trên snapshot của parent. Với block kế tiếp, trình tự là đọc snapshot → xác minh và thực thi ngoài transaction ghi → mở transaction ngắn, so lại base và ghi nguyên tử → trả `applied`. Nếu cần lấy parent từ peer, hoàn tất tải và xác minh từng height trước. Nếu base đã đổi, đọc lại và kiểm lại. Toàn bộ quy tắc phân loại height ở [đường nhận block đã chốt](api-contract.md#nhận-block-đã-chốt).

Mọi sự kiện thay đổi quyết định consensus đi qua một vòng xử lý tuần tự trên mỗi node. Timer mang `height`, `view` và pha, bị bỏ qua khi vòng đã đổi. Đường leader tạo block chọn giao dịch theo thứ tự ổn định trong mempool cục bộ, thực thi thử, ký bằng khóa riêng `node1` và phải giữ nguyên proposal đã lưu cho height đó sau restart. Nhiều node có thể có mempool khác nhau. Tính tất định được kiểm trên chuỗi block và thứ tự giao dịch trong block, cùng một genesis.

### Nhận và chuyển tiếp giao dịch

`admit_transaction(tx: Transaction) -> AdmissionResult` kiểm payload và chữ ký, tính lại `tx_id` rồi đối chiếu chỉ mục giao dịch đã chốt và mempool. Gọi `execute_block(snapshot, [tx], context)` để kiểm tra giao dịch mới đối với trạng thái đã chốt. Việc kiểm tra và giữ chỗ trong mempool dùng cùng điểm điều phối để hai request đồng thời không nhận hai `tx_id` cạnh tranh cho cùng sender. MVP giữ tối đa một giao dịch pending trên mỗi sender. Gửi lại cùng `tx_id` hợp lệ truy xuất kết quả hiện có.

Mọi node có thể nhận vào mempool cục bộ trong bộ nhớ. Node follower lên lịch chuyển tiếp bất đồng bộ cùng transaction đã ký tới `POST /transactions` của `node1`, giữ nguyên payload khi gửi lại. Leader là điểm cuối. Hàng đợi, backoff và các lỗi được phép retry theo hợp đồng HTTP. `202` báo đã nhận cục bộ. Sau restart, mempool trống và client có thể gửi lại đúng giao dịch. Việc chuyển tiếp thất bại là kết quả quan sát cục bộ. Sau mỗi block đã commit, rà lại các giao dịch pending với snapshot mới, cập nhật trạng thái quan sát theo hợp đồng HTTP và loại giao dịch không còn hợp lệ khỏi danh sách có thể đề xuất.

### Vote trùng và equivocation

- Lưu phiếu đầu tiên đã xác thực theo `(protocol_version, chain_id, height, view, phase, sender_id)` ngay cả khi hash khác giá trị đang theo. Tập này tách với tập đếm quorum. Một lần gửi lặp cùng giá trị không tăng đếm. Khi thấy phiếu đã xác thực thứ hai ký hash khác, ghi hai phiếu kèm chữ ký thành một cặp bằng chứng, dù nhận theo thứ tự nào.
- Khi phát hiện equivocation, loại signer đó khỏi tập dựng quorum cục bộ ở context liên quan. Một certificate từ peer vẫn được xác minh bằng quy tắc chữ ký và số signer từ genesis ở trên. Hai node có thể đã quan sát các bằng chứng khác nhau khi certificate được dựng.
- Giới hạn một cặp bằng chứng đầy đủ trên mỗi context/sender. Lưu theo thứ tự xác định của hai phiếu và dùng khóa duy nhất cho context/sender để việc gửi lại không phình DB. Sau khi dựng proof hợp lệ, việc phát hiện thêm bằng chứng không đảo ngược kết quả đã chốt.

## 3. Giao diện SQLite và biên nguyên tử

```python
# TV3 · src/storage
load_snapshot() -> LedgerSnapshot
load_recovery_state() -> RecoveryState
get_proposal(height: int) -> Proposal | None
get_own_signed_vote(height: int, phase: VotePhase) -> Vote | None
get_finalized(height: int) -> FinalizedBlock | None
persist_leader_proposal(proposal: Proposal, base: LedgerSnapshot) -> Proposal
persist_prepare(proposal: Proposal, own_vote: Vote, base: LedgerSnapshot) -> Vote
persist_commit(prepared: PreparedCertificate, own_vote: Vote, base: LedgerSnapshot) -> Vote
save_equivocation_evidence(vote_a: Vote, vote_b: Vote) -> None
apply_committed_block(finalized: FinalizedBlock, base: LedgerSnapshot,
                      result: ExecutionResult) -> ApplyResult
```

| Thao tác | Dữ liệu và điều kiện trong cùng giao dịch |
|---|---|
| Lưu proposal của leader | Kiểm tip/height hiện hành, ghi proposal nguyên bản cho vòng. Nếu có cùng giá trị thì trả bản đã lưu. Từ chối proposal hash khác cùng vòng. Gửi `PROPOSE` sau khi giao dịch đã commit. |
| Lưu PREPARE | Kiểm tip và `target_height`, khóa trùng hash hoặc chưa có lock. Ghi cùng lúc proposal đã kiểm, khóa bền vững và đúng own PREPARE. Lần gọi lặp trả phiếu đã lưu. Leader cũng đi qua quy tắc này. |
| Lưu COMMIT | Đòi lock và own PREPARE cùng hash, prepared certificate đã kiểm và đúng base. Ghi proof và own COMMIT trong cùng giao dịch. Chỉ sau khi commit mới đưa own vote vào bộ gom và gửi ra mạng. |
| Ghi block đã chốt | So sánh `base.committed_height`, `base.tip_hash` và `base.state_hash` với bản đang lưu. Ghi block/proposal, certificate, chỉ mục `tx_id` duy nhất, balances/nonces, `state_hash`, `committed_height` và dọn lock/proposal đang xử lý trong cùng giao dịch. Giao dịch rollback toàn bộ nếu điều kiện hoặc ghi thất bại. Chỉ sau commit DB mới công bố block, dọn mempool, chuyển height hay trả `committed`. |

Khóa duy nhất tối thiểu gồm `(chain_id, height)` và `(chain_id, block_hash)` cho block, `(chain_id, tx_id)` cho giao dịch đã áp dụng, `(chain_id, height, view)` cho durable lock và `(chain_id, height, view, phase)` cho own vote của DB node đó. Bản đã ký phải được lưu đủ để phát lại cùng thông điệp và chữ ký. Ghi đồng thời dùng transaction lấy quyền ghi trước khi kiểm điều kiện và ghi quyết định, cùng ràng buộc duy nhất ở DB. Lock xung đột trả lỗi trước khi gửi phiếu. Không giữ transaction SQLite lúc `await` HTTP. Với own proposal, PREPARE và COMMIT, hoàn tất transaction ghi trước khi gửi thông điệp dựa trên quyết định đó.

`apply_committed_block` trả `APPLIED` cho lần ghi mới, `DUPLICATE` nếu height đã có đúng `block_hash` (kể cả một certificate hợp lệ khác cho cùng block), hoặc `STALE_SNAPSHOT` nếu base đổi trong lúc xác minh và cần đọc lại. Với cùng height mà hash khác, chỉ chuyển sang dừng an toàn nếu proof cạnh tranh đã được xác minh độc lập, gồm thực thi trên snapshot của parent tương ứng. Mọi phản hồi chứa proof không hợp lệ bị từ chối, trong khi bản đã chốt giữ nguyên.

Không xóa own vote và bằng chứng chỉ vì hết timeout hoặc đổi phase. Sau khi height chốt, giữ lịch sử chữ ký để kiểm tra phục hồi. Các height `<= committed_height` không được ký mới. Lỗi ghi bền vững ngăn mọi gửi mới dựa trên bản ghi chưa commit.

### Cấu hình bền vững của validator

TV3 dùng `journal_mode=WAL` và `synchronous=FULL` cho DB validator. Sau khi mở mỗi connection ghi, thiết lập và đọc lại hai PRAGMA trước khi cho phép lưu quyết định ký. Việc đọc lại là cần thiết vì `synchronous` là thiết lập của connection. Kiểm tra crash/restart phải bao gồm lock và own vote đã broadcast.

WAL hỗ trợ đọc và ghi đồng thời. `synchronous=FULL` thêm đồng bộ WAL sau từng transaction commit. Với `NORMAL`, transaction đã commit có thể mất sau mất điện hoặc lỗi hệ điều hành. Nếu own vote/lock đã mất mà phiếu đã phát vẫn tồn tại ở peer, node khởi động lại có thể ký giá trị xung đột. Hợp đồng giữ `FULL` để đáp ứng persist-before-send trong mô hình phục hồi của dự án, với giả định hệ điều hành và thiết bị lưu trữ thực hiện đúng thao tác đồng bộ. [Tài liệu SQLite về synchronous](https://www.sqlite.org/pragma.html#pragma_synchronous).

WAL vẫn có các trường hợp trả `SQLITE_BUSY`. Dùng snapshot đọc ngắn và busy handler có deadline theo ngân sách request. Khi hết thời gian chờ khóa mà chưa ghi thành công, trả `503 STORAGE_BUSY` và giữ nguyên quyết định ký. Thử lại phải đọc lại bản đã lưu để xử lý idempotency. Nếu lỗi I/O làm kết quả ghi chưa xác định, dừng gửi, chuyển `SAFETY_HALT` và kiểm tra phục hồi trước khi ký tiếp. [Tài liệu SQLite về SQLITE_BUSY trong WAL](https://www.sqlite.org/wal.html#sometimes_queries_return_sqlite_busy_in_wal_mode).

## 4. Transport, timeout và trạng thái công khai

```python
# TV3 · src/network
async def send_proposal(peer_id: NodeId, proposal: Proposal) -> PeerResult: ...
async def send_vote(peer_id: NodeId, vote: Vote) -> PeerResult: ...
async def send_finalized(peer_id: NodeId, finalized: FinalizedBlock) -> PeerResult: ...
async def fetch_proposal(peer_id: NodeId, height: int) -> Proposal | None: ...
async def fetch_peer_status(peer_id: NodeId, height: int) -> PeerStatus: ...
async def fetch_finalized(peer_id: NodeId, height: int) -> FinalizedBlock | None: ...
async def forward_transaction(tx: Transaction) -> PeerResult: ...
async def sync_to_height(hint_height: int) -> SyncResult: ...
```

`send_vote` chọn `/peer/prepare` hoặc `/peer/commit` theo `phase`. Phát tới ba peer còn lại. Own vote đi vào bộ gom cục bộ duy nhất một lần sau khi đã lưu. `fetch_proposal` dùng `GET /consensus/proposal?height=…` và xác minh chữ ký leader dù proposal đến từ follower. `fetch_peer_status` dùng `GET /consensus/status?height=…` để nhận gợi ý. `fetch_finalized` lấy proof đầy đủ tại `GET /blocks/{height}`. Chỉ fan-out có giới hạn và chỉ để một yêu cầu lấy proposal đang xử lý cho mỗi `(peer, target_height)`.

| Điều kiện | Tham số mặc định cho bốn node local và cách xử lý |
|---|---|
| Kích thước `POST` | Giới hạn body JSON 4 KiB cho transaction/vote, 512 KiB cho proposal/finalized. Block chuẩn hóa tối đa 256 KiB và 128 giao dịch. Dùng giới hạn trước parse và khi đọc dữ liệu từ peer để tránh nhận toàn bộ dữ liệu lớn vào bộ nhớ. |
| HTTP peer | 1 giây cho một lần thử tính từ khi bắt đầu request tới khi đọc và kiểm giới hạn response. Tránh retry lồng nhau trong HTTP client và timer consensus. Timeout, mất kết nối và lỗi tạm thời có thể thử lại theo nhịp của vòng. Lỗi schema, chữ ký, context hoặc giới hạn không được retry nguyên request. |
| Chờ proposal | 5 giây rồi hỏi leader. Khi leader không phản hồi hoặc không trả dữ liệu hợp lệ, có thể báo `LEADER_UNAVAILABLE` và tiếp tục dò có giới hạn. Leader phản hồi chưa có proposal là trạng thái chờ bình thường. Sau khi lấy proposal hợp lệ cho vòng đang xét, tiếp tục xác minh và PREPARE. |
| Chờ PREPARE hoặc COMMIT | Mỗi 2 giây phát lại phiếu đã lưu của pha đang chờ. Tối đa năm lần phát lại nhanh trên mỗi pha, ngoài lần gửi đầu. Đổi pha reset timer của pha mới và vô hiệu timer pha cũ. |
| `STALLED` | Dò và phát lại chậm mặc định `10 ± 2` giây. Phát lại own PREPARE **và** own COMMIT nếu cả hai đã lưu, theo cùng byte/chữ ký. Peer còn kẹt PREPARE cần các phiếu PREPARE của peer đã sang COMMIT. Đồng thời tiếp tục nhận phiếu/proof, dò proposal còn thiếu hoặc hỏi tip peer. Chỉ có status/count không thay thế phiếu đã ký. |
| Vote tới sớm hoặc đảo thứ tự | Giữ tối đa 50 vote khác nhau tổng cộng cho `target_height`, đã qua xác thực, được khử trùng theo context/sender/hash và chỉ giữ tối đa hai hash mỗi sender/pha để lưu chứng cứ. Khi hết chỗ trả lỗi giới hạn và ghi log. Khi có proposal hợp lệ, xử lý PREPARE trước. Chỉ mở phần đệm COMMIT sau khi own COMMIT đã lưu hoặc đi đường proof đã chốt. |
| Height cũ hoặc tương lai | Height cũ không làm thay đổi vòng. Vote hoặc proposal mới hơn `target_height` không giữ trong buffer. Với thông báo finalized ở height xa hơn, chỉ lên lịch một lần sync theo gợi ý đã kiểm được phần chữ ký/context. Không xếp hàng block tương lai chưa kiểm chuỗi. |

Các thông số thời gian chỉ là mặc định vận hành. Timeout không thay đổi leader, khóa, view hay ngưỡng ba chữ ký. Nếu sau nối mạng có đủ phiếu cho cùng block thì node đang `STALLED` có thể tiến triển tiếp. Với phiếu đã chia cho các proposal khác nhau hoặc leader thực sự mất, có thể tiếp tục chờ. `STALLED` vì thiếu PREPARE đi qua `PREPARED` và lưu own COMMIT trước khi gửi. Khi có proof hợp lệ từ peer, node luôn có thể đi đường nhập proof sau đầy đủ kiểm tra.

### Cấu hình thời gian vận hành

Khi triển khai W2, phần `runtime` trong cấu hình từng node hỗ trợ các key bên dưới. Biến môi trường có độ ưu tiên cao hơn file config, sau đó đến mặc định trong bảng. Giá trị tính bằng giây và là số hữu hạn dương, riêng jitter cho phép `0`.

| Key trong `runtime` | Biến môi trường | Mặc định (giây) |
|---|---|---|
| `peer_request_timeout_s` | `MINIVOTING_PEER_REQUEST_TIMEOUT_S` | 1 |
| `proposal_timeout_s` | `MINIVOTING_PROPOSAL_TIMEOUT_S` | 5 |
| `prepare_timeout_s` | `MINIVOTING_PREPARE_TIMEOUT_S` | 2 |
| `commit_timeout_s` | `MINIVOTING_COMMIT_TIMEOUT_S` | 2 |
| `stalled_probe_interval_s` | `MINIVOTING_STALLED_PROBE_INTERVAL_S` | 10 |
| `stalled_probe_jitter_s` | `MINIVOTING_STALLED_PROBE_JITTER_S` | 2 |

Jitter phải nhỏ hơn interval. Mỗi lần probe lấy độ lệch trong khoảng `[-jitter, +jitter]`. Validate toàn bộ cấu hình trước khi node sẵn sàng. Giá trị sai làm khởi động thất bại với lý do rõ ràng. Ghi bộ giá trị hiệu lực vào log và metadata của mỗi lần thực nghiệm để chạy lại. Timer dùng đồng hồ đơn điệu, chốt giá trị khi khởi động và có thể khác giữa các node. Số fast retry vẫn là 5 lần mỗi pha. Các giá trị này chỉ điều khiển lịch gửi lại và cảnh báo. Các giới hạn dữ liệu wire và tham số genesis giữ theo mô hình dữ liệu chung. Scaffold hiện tại chưa có parser cho phần `runtime` này.

Tên trạng thái runtime dùng thống nhất với API ở mức biểu diễn đã mô tả tại [hợp đồng API](api-contract.md). `INITIALIZING` xác minh cấu hình và DB. `WAIT_PROPOSAL` chờ block mới, `VALIDATING_PROPOSAL` chạy core, `PREPARING` gom PREPARE, `PREPARED` đã đủ PREPARE, `COMMITTING` gom COMMIT, `DECIDED` ghi quyết định đã đủ bằng chứng. `LEADER_UNAVAILABLE` và `STALLED` là cảnh báo tiến triển của node. `SYNCING` đang xác minh và ghi các block đã chốt từ peer. `DECIDED` nội bộ chỉ trở thành block `committed` sau khi transaction SQLite thành công. Khi có lỗi an toàn hoặc lỗi lưu trữ khiến node chưa thể tham gia, dùng `SAFETY_HALT` nội bộ, dừng ký và báo chưa sẵn sàng. `sync_state` là `SYNCED` hoặc `SYNCING` khi API sẵn sàng. `SYNCED` nghĩa là node hiện chưa biết proof hợp lệ cho tip cao hơn, không xác nhận tip toàn mạng. Frontend dùng `committed_height` và proof để hiển thị height đã chốt, không dùng số phiếu hay nhãn pha làm bằng chứng ghi sổ.

## 5. Phục hồi và đồng bộ

1. **Khởi động.** Đối chiếu genesis hash đã ghim trong cấu hình, chain ID và node ID/key tương ứng registry. Kiểm tra metadata, tip, dữ liệu ký còn giữ và tính nguyên vẹn của ledger. Khi khởi động theo đường phục hồi, replay chuỗi từ genesis và so sánh hash/state. Nếu phát hiện mâu thuẫn, báo chưa sẵn sàng và dừng ký. Giữ dữ liệu own vote, lock và bằng chứng để chẩn đoán. Việc cài lại DB trống chỉ được xem là khởi tạo lần đầu cho validator chưa từng tham gia hoặc trên chain thử nghiệm khác. Mất dữ liệu khóa của validator cũ cần phục hồi journal/backup đáng tin trước khi dùng lại khóa ký.
2. **Khôi phục vòng.** Đọc proposal, lock, own PREPARE/COMMIT và prepared proof ở `target_height` trong một snapshot. Nếu đã có own vote thì kiểm chữ ký/context, kiểm lại proposal với tip hiện hành rồi phát lại bản đã lưu. Nếu có PREPARE nhưng chưa có COMMIT, tiếp tục gom PREPARE hoặc phục hồi từ prepared proof đã xác minh. Nếu leader đã lưu proposal mà chưa PREPARE, phát lại đúng proposal đó và tiếp tục xử lý như vòng hiện tại. Không tạo proposal/vote khác do mất timer hay mempool.
3. **Tìm peer đi trước.** `peer_committed_height > local_committed_height` từ status là gợi ý chưa ký để lên lịch lấy proof có giới hạn, kể cả khi bằng `local_target_height`. Không đổi tip, không khóa hay dừng bỏ phiếu vì riêng tín hiệu này. Chỉ đồng bộ qua các peer đã cấu hình. Nếu một peer khai height cao nhưng không có dữ liệu/proof hợp lệ tại height cần, thử peer khác và backoff theo nhịp chậm. Dữ liệu đã chốt cục bộ tiếp tục phục vụ truy vấn từ snapshot nhất quán nếu storage còn sẵn sàng.
4. **Tải nối tiếp.** Tạm dừng tạo proposal/vote mới trong lúc nhập block đã kiểm. Tải tối đa một block mỗi request và một lượt đồng bộ trên mỗi node. Kiểm từng bước `height = local_committed_height + 1`, `prev_hash = local_tip_hash`, context, leader, proposal, certificate, `tx_id` chưa được áp dụng trước đó và kết quả thực thi. Ghi nguyên tử từng block. Chỉ tăng height sau ghi thành công. Mỗi lần lặp có giới hạn request và deadline. Khởi động lại sync đọc từ tip đã commit.
5. **Giải quyết lock và proof.** Một `FinalizedBlock` hợp lệ cho height chưa chốt có thể khác proposal mà node đã PREPARE và khóa cục bộ. Node nhập block duy nhất có proof sau khi xác minh đầy đủ, trong khi không ký phiếu mới cho hash xung đột. Dọn lock chỉ trong transaction ghi block. Nếu có hai proof finalized hợp lệ cho hai hash khác nhau ở cùng height, dừng ký, cảnh báo và giữ bằng chứng để nhóm kiểm tra. Không tự chọn theo chiều dài hoặc số phản hồi peer.

## 6. Tiêu chí kiểm tra khi triển khai

| Nhóm kiểm tra theo [kế hoạch](ke-hoach.md#152-ma-trận-test-bắt-buộc) | Bằng chứng cần giữ |
|---|---|
| T08–T11, T14–T17 | Transcript và chữ ký/proof với block sai, hai phiếu, ba phiếu, vote đến trước proposal/pha, gửi lặp và equivocation theo cả hai thứ tự. |
| T11, T23–T26 | Follower chưa có own vote hoặc prepared certificate nhận finalized kế tiếp hợp lệ rồi ghi đúng một lần. Kiểm riêng proposal hợp lệ nhưng attachment bị sửa, certificate thiếu quorum/sai chữ ký, base đổi lúc kiểm, finalized đến xa và retry sau khi block đã ghi. |
| T20–T22 và E4 | Với mạng chia 2–2, kiểm tra không đủ ba chữ ký chỉ từ hai node. Cho một phía chờ PREPARE và phía kia đã phát COMMIT từ trước phân vùng. Khi kết nối trở lại, quan sát phát lại cả hai pha và sự tiến triển nếu có đủ vote cùng hash. Kiểm node restart phát lại đúng proposal và bản vote đã lưu. |
| T23–T26, T29–T30 | SQLite crash ở các điểm ghi, hai yêu cầu cạnh tranh ký, follower bắt kịp, proof giả hoặc DB sai, lock cục bộ khác hash có proof hợp lệ, giới hạn body/height/buffer và không giữ DB transaction qua HTTP. |
| Vận hành W2 | Chạy với timeout mặc định và timeout ghi đè qua config/env, kiểm thứ tự ưu tiên và từ chối giá trị sai. Xác nhận PRAGMA trên từng connection ghi. Tạo tranh chấp khóa DB để kiểm deadline, `STORAGE_BUSY` và gửi lại idempotent. |
| T27–T28 | Bốn node có tip/state nhất quán tại height chung, dashboard phân biệt API online, accepted/pending và block đã chốt. |

Các mục trên là điều kiện nghiệm thu khi đã có module chạy và script thử nghiệm. Bản đặc tả này không ghi nhận chúng là kết quả test hệ thống.
