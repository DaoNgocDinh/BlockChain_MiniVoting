# Backlog nhóm 4 người

24 issue, mỗi người sáu đầu việc theo sáu tuần; nguồn: mục 12–17 và 20 của [kế hoạch](ke-hoach.md).
TV4 là @DaoNgocDinh; TV1–TV3 chờ username thật. Không tự đặt deadline.
Bộ khung không thay cho nghiệm thu W1. Phụ thuộc là mốc cần xong trước khi tích hợp; các phần độc lập có thể làm song song.

| Mã | Công việc | Review | Phụ thuộc |
|---|---|---|---|
| TV1-W1 | [TV1][W1] Data model, genesis và canonical bytes | TV2, TV3 | — |
| TV2-W1 | [TV2][W1] Đặc tả protocol, fault model và bất biến | TV1, TV3 | — |
| TV3-W1 | [TV3][W1] Môi trường, API/config và skeleton bốn node | TV1, TV2; TV4 review API | TV1-W1, TV2-W1 |
| TV4-W1 | [TV4][W1] Wireframe, test matrix và khung báo cáo | TV3 (API), TV2 (consensus) | TV1-W1, TV2-W1 |
| TV1-W2 | [TV1][W2] Chữ ký giao dịch, số dư/nonce và validate block | TV2, TV3 | TV1-W1 |
| TV2-W2 | [TV2][W2] State machine và simulation transport | TV1, TV3 | TV2-W1, TV1-W1 |
| TV3-W2 | [TV3][W2] HTTPX transport, peer API và SQLite repos | TV1, TV2 | TV3-W1 |
| TV4-W2 | [TV4][W2] Dashboard mock theo schema và ví demo | TV3, TV2 | TV4-W1, TV3-W1 |
| TV1-W3 | [TV1][W3] Mempool và tích hợp committed state | TV2, TV3 | TV1-W2, TV2-W2, TV3-W2 |
| TV2-W3 | [TV2][W3] Ba pha thật, certificate và durable voting | TV1, TV3 | TV2-W2, TV1-W2, TV3-W2 |
| TV3-W3 | [TV3][W3] Bốn node, atomic commit và end-to-end thật | TV1, TV2 | TV3-W2, TV1-W2, TV2-W2 |
| TV4-W3 | [TV4][W3] Explorer, certificate và vote timeline thật | TV3 (API), TV2 (vote) | TV4-W2, TV1-W3, TV2-W3, TV3-W3 |
| TV1-W4 | [TV1][W4] Double spend, replay, tamper và state recovery | TV3; TV2 về validity | TV1-W3, TV3-W3 |
| TV2-W4 | [TV2][W4] Equivocation, split vote, restart lock và race | TV1, TV3 | TV2-W3, TV3-W3 |
| TV3-W4 | [TV3][W4] Sync/recovery và fault injection transport | TV1, TV2 | TV3-W3, TV2-W3 |
| TV4-W4 | [TV4][W4] Regression và workload runner tái lập | TV3, TV2 | TV4-W3, TV1-W4, TV2-W4, TV3-W4 |
| TV1-W5 | [TV1][W5] Rà core, hỗ trợ benchmark và chương blockchain | TV2, TV4 | TV1-W4 |
| TV2-W5 | [TV2][W5] Phân tích consensus, message count và giới hạn | TV1, TV4 | TV2-W4 |
| TV3-W5 | [TV3][W5] Triển khai máy mới và hướng dẫn vận hành | TV4; TV1/TV2 về recovery | TV3-W4 |
| TV4-W5 | [TV4][W5] Thực nghiệm, CSV, latency/TPS và biểu đồ | TV2 (kết luận), TV3 (môi trường) | TV4-W4, TV1-W5, TV2-W4, TV3-W5 |
| TV1-W6 | [TV1][W6] Nghiệm thu core và demo chuyển coin/tamper | TV2, TV4 | TV1-W5, TV4-W5 |
| TV2-W6 | [TV2][W6] Nghiệm thu consensus và demo quorum/leader lỗi | TV1, TV3, TV4 | TV2-W5, TV4-W5 |
| TV3-W6 | [TV3][W6] Checkout sạch, release và demo restart/sync | TV1, TV2, TV4 | TV3-W5, TV4-W5 |
| TV4-W6 | [TV4][W6] Nghiệm thu cuối, báo cáo/slide/video và demo | Cả nhóm | TV4-W5, TV1-W6, TV2-W6, TV3-W6 |

## TV1-W1 · [TV1][W1] Data model, genesis và canonical bytes

Phụ trách: TV1. Review: TV2, TV3. Mốc W1.
Bàn giao: src/core, config, docs/data-model.md. Phụ thuộc: không.

- Đặc tả Transaction/Block/Genesis, amount nguyên, nonce, địa chỉ, canonical bytes và context ký.
- Sinh public genesis mẫu/test vector; registry bốn validator, leader cố định và quorum 3.

Tiêu chí nghiệm thu:

- [ ] T01: đổi thứ tự key không đổi canonical bytes/hash.
- [ ] Bốn node có cùng genesis hash; không commit private key.
- [ ] TV2/TV3 review hợp đồng trước tích hợp.

## TV2-W1 · [TV2][W1] Đặc tả protocol, fault model và bất biến

Phụ trách: TV2. Review: TV1, TV3. Mốc W1.
Bàn giao: docs/protocol.md, docs/consensus-state-machine.md. Phụ thuộc: không.

- Đặc tả PROPOSE/PREPARE/COMMIT, mọi validator kể cả leader bỏ phiếu.
- Chốt n=4, q=3, tối đa một Byzantine; lock/persist-before-send và timeout/retry.
- Giải thích giao quorum, fixed leader và giới hạn safety/liveness.

Tiêu chí nghiệm thu:

- [ ] Nhóm giải thích được quorum 3/4 và quy tắc không ký hai giá trị cùng context.
- [ ] Tài liệu ghi rõ leader lỗi/split vote có thể stall; không gọi PBFT đầy đủ.
- [ ] TV1/TV3 thống nhất schema và persistence interface.

## TV3-W1 · [TV3][W1] Môi trường, API/config và skeleton bốn node

Phụ trách: TV3. Review: TV1, TV2; TV4 review API. Mốc W1.
Bàn giao: src/api, config, scripts, docs/api-contract.md. Phụ thuộc: TV1-W1, TV2-W1.

- Chốt Python/dependency và lockfile backend, API/schema/timeout/payload limits.
- Hoàn thiện config, health, registry và đường dẫn bốn DB/keys riêng; phối hợp sinh genesis.
- Bổ sung chạy/dừng đúng tiến trình của đồ án.

Tiêu chí nghiệm thu:

- [x] Bốn /health trả đúng node ID; health không có nghĩa đủ quorum/đã sync.
- [x] Cài từ dependency lock trên máy khác; schema được chủ module review.
- [x] Bốn node không dùng chung DB/private key; script không kill process ngoài repo.

## TV4-W1 · [TV4][W1] Wireframe, test matrix và khung báo cáo

Phụ trách: TV4 · @DaoNgocDinh. Review: TV3 (API), TV2 (consensus). Mốc W1.
Bàn giao: frontend, docs/test-matrix.md, docs/report/outline.md. Phụ thuộc: TV1-W1, TV2-W1.

- Chốt wireframe node/transaction/account/block/certificate/timeline và trạng thái với TV3.
- Ma trận T01–T30, chủ trì/review/bằng chứng và khung chương báo cáo.
- Chốt Node, commit package-lock.json và chuyển CI sang npm ci.

Tiêu chí nghiệm thu:

- [ ] Wireframe được TV2/TV3 review; UI không giữ key validator hay chốt block.
- [ ] Đủ T01–T30, chưa chạy ghi Not run; mỗi người có chương báo cáo riêng.
- [ ] Frontend cài/build từ lockfile; mock tách khỏi dữ liệu thật.

## TV1-W2 · [TV1][W2] Chữ ký giao dịch, số dư/nonce và validate block

Phụ trách: TV1. Review: TV2, TV3. Mốc W2.
Bàn giao: src/core, tests/unit, ví CLI demo. Phụ thuộc: TV1-W1.

- Wrapper SHA-256/Ed25519, ví CLI tạo/ký giao dịch.
- Kiểm amount/chain/signature/nonce/balance, execute_block tuần tự thuần.
- Tính tx_list_hash/state_hash và validate prev_hash/height.

Tiêu chí nghiệm thu:

- [ ] T02–T04, T06–T09 đạt; sai chữ ký/nonce/chain/state hash bị chặn.
- [ ] Amount 0/âm/float/bool/quá giới hạn và chi vượt số dư bị loại.
- [ ] Không cập nhật state bền vững trước COMMIT.

## TV2-W2 · [TV2][W2] State machine và simulation transport

Phụ trách: TV2. Review: TV1, TV3. Mốc W2.
Bàn giao: src/consensus, tests/simulation. Phụ thuộc: TV2-W1, TV1-W1.

- State machine tách HTTP/DB; transport giả điều khiển trễ/lặp/đảo thứ tự.
- Verify sender/signature/phase/height/chain/hash; unique sender, bounded buffer.

Tiêu chí nghiệm thu:

- [ ] T10/T12: hai phiếu không chốt; 100 request một sender chỉ tính một danh tính.
- [ ] T13/T14: sender giả, chữ ký sai, trộn phase/context không tăng quorum.
- [ ] T15: đảo thứ tự không tạo COMMIT sai điều kiện.

## TV3-W2 · [TV3][W2] HTTPX transport, peer API và SQLite repos

Phụ trách: TV3. Review: TV1, TV2. Mốc W2.
Bàn giao: src/network, src/storage, src/api, tests/integration. Phụ thuộc: TV3-W1.

- Transport async dùng chung, timeout/retry/idempotency và buffer giới hạn.
- Schema blocks/accounts/own_votes/locks/certificates/pending proposals.
- Interface atomic commit và persist own vote; không giữ DB transaction khi chờ HTTP.

Tiêu chí nghiệm thu:

- [ ] Peer timeout không làm node crash; lỗi có node/context.
- [ ] Constraints chống duplicate apply và own votes/locks xung đột.
- [ ] Integration HTTP/DB thật; guard payload/future height (T30).

## TV4-W2 · [TV4][W2] Dashboard mock theo schema và ví demo

Phụ trách: TV4 · @DaoNgocDinh. Review: TV3, TV2. Mốc W2.
Bàn giao: frontend, docs/ui.md. Phụ thuộc: TV4-W1, TV3-W1.

- Trang node/status, transaction/account/block/certificate theo hợp đồng.
- Mock có nhãn, tách API adapter thật; kết nối ví/API của TV1.
- Loading/error/offline và accepted/committed/rejected/local-unknown/stalled.

Tiêu chí nghiệm thu:

- [ ] Responsive, lint/build đạt; TV3 xác nhận schema.
- [ ] 202 accepted không hiển thị đã chốt; số dư lấy committed state.
- [ ] Không trình bày mock/số liệu giả như trạng thái mạng thật.

## TV1-W3 · [TV1][W3] Mempool và tích hợp committed state

Phụ trách: TV1. Review: TV2, TV3. Mốc W3.
Bàn giao: src/core, tests/integration. Phụ thuộc: TV1-W2, TV2-W2, TV3-W2.

- Mempool chống trùng, chọn thứ tự xác định; kết nối proposer.
- Tích hợp execute/validate với consensus và atomic commit storage.

Tiêu chí nghiệm thu:

- [ ] T05/T11: giao dịch áp dụng tối đa một lần sau commit.
- [ ] Replay cùng chuỗi cho cùng state hash/balances/nonces.
- [ ] Không thay số dư từ accepted/mempool; retry không double apply.

## TV2-W3 · [TV2][W3] Ba pha thật, certificate và durable voting

Phụ trách: TV2. Review: TV1, TV3. Mốc W3.
Bàn giao: src/consensus, tests/integration. Phụ thuộc: TV2-W2, TV1-W2, TV3-W2.

- Kết nối core validation, transport và own vote persistence.
- Tạo/verify certificate ba COMMIT khác danh tính, cùng context.
- Ghi lock/vote trước send; events phục vụ timeline.

Tiêu chí nghiệm thu:

- [ ] T11: ba COMMIT đúng tạo certificate và chốt tối đa một lần.
- [ ] Node tự verify certificate, không tin count từ leader.
- [ ] Một giao dịch thật trên bốn process cho cùng block/state hash.

## TV3-W3 · [TV3][W3] Bốn node, atomic commit và end-to-end thật

Phụ trách: TV3. Review: TV1, TV2. Mốc W3.
Bàn giao: src/network, src/storage, src/api, scripts. Phụ thuộc: TV3-W2, TV1-W2, TV2-W2.

- Route propose/prepare/commit/finalized; nối core/consensus/storage.
- Atomic write block/certificate/state/applied IDs/height.
- API quan sát thật và script chạy/dừng nhóm node.

Tiêu chí nghiệm thu:

- [ ] Quy trình chung chạy bốn node với DB/keys tách biệt.
- [ ] Giao dịch thật đạt 3/4 COMMIT và bốn ledger/state giống nhau.
- [ ] Retry không double apply; accepted/committed phản ánh đúng thời điểm.

## TV4-W3 · [TV4][W3] Explorer, certificate và vote timeline thật

Phụ trách: TV4 · @DaoNgocDinh. Review: TV3 (API), TV2 (vote). Mốc W3.
Bàn giao: frontend, tests/integration, docs/demo. Phụ thuộc: TV4-W2, TV1-W3, TV2-W3, TV3-W3.

- Kết nối bốn node: height/tip/phase/sync và trạng thái API.
- Explorer transaction/account/block/certificate; timeline sender/phase/height/hash/time.
- Smoke test từ giao dịch đến commit.

Tiêu chí nghiệm thu:

- [ ] Mất API không giữ online giả; số liệu có nguồn node rõ.
- [ ] Xem được ba danh tính/chữ ký tạo certificate, đối chiếu log thật.
- [ ] T27/T28: bốn ledger nhất quán; UI không nhầm accepted với committed.

## TV1-W4 · [TV1][W4] Double spend, replay, tamper và state recovery

Phụ trách: TV1. Review: TV3; TV2 về validity. Mốc W4.
Bàn giao: src/core, tests/unit, tests/fault. Phụ thuộc: TV1-W3, TV3-W3.

- Bổ sung double spend/replay/tamper và thứ tự thực thi.
- Crash trước/trong/sau transaction; replay và phát hiện local corruption.

Tiêu chí nghiệm thu:

- [ ] T02–T09, T23, T26 có bằng chứng chạy lại.
- [ ] Không tạo trạng thái trừ tiền nhưng thiếu block, không double apply.
- [ ] Replay cho cùng state hash; dữ liệu bị sửa không tiếp tục vote mù.

## TV2-W4 · [TV2][W4] Equivocation, split vote, restart lock và race

Phụ trách: TV2. Review: TV1, TV3. Mốc W4.
Bàn giao: src/consensus, tests/simulation, tests/fault. Phụ thuộc: TV2-W3, TV3-W3.

- Hai proposal cạnh tranh, follower double-sign và phiếu đảo thứ tự.
- Restart giữ own vote/lock; retry đúng bytes cũ, không tự mở khóa.
- Race hai request cố tạo own vote khác hash.

Tiêu chí nghiệm thu:

- [ ] T10–T17, T19, T22, T29 đạt với seed/log/config.
- [ ] Không hai block chốt xung đột ở honest nodes trong mô hình.
- [ ] Restart/race không làm ký hai giá trị; fixed leader lỗi báo stall.

## TV3-W4 · [TV3][W4] Sync/recovery và fault injection transport

Phụ trách: TV3. Review: TV1, TV2. Mốc W4.
Bàn giao: src/network, src/storage, scripts, tests/fault. Phụ thuộc: TV3-W3, TV2-W3.

- Sync từng block/certificate, replay từ trạng thái tin cậy.
- Restart giữ vote/lock; fault drop/delay/duplicate/partition mặc định tắt.
- Crash test và guard buffer/payload/future-height.

Tiêu chí nghiệm thu:

- [ ] T18–T26/T30 tái hiện được; T22/T23 phối hợp chủ module.
- [ ] Partition 2–2 không chốt; nhóm 3 có leader có thể tiến triển; node lẻ sync sau nối lại.
- [ ] Certificate giả không được chấp nhận vì chuỗi dài; state hash follower khớp sau sync.

## TV4-W4 · [TV4][W4] Regression và workload runner tái lập

Phụ trách: TV4 · @DaoNgocDinh. Review: TV3, TV2. Mốc W4.
Bàn giao: scripts, tests/integration, tests/fault, frontend. Phụ thuộc: TV4-W3, TV1-W4, TV2-W4, TV3-W4.

- Workload có seed/config/tải/mốc thời gian, ký tx hợp lệ phối hợp TV1.
- Điều phối T01–T30 với pass/fail/not-run, log và commit SHA.
- UI pending/stalled/sync/offline phản ánh fault thật.

Tiêu chí nghiệm thu:

- [ ] Cùng seed/config tái tạo được workload đầu vào và metadata.
- [ ] T27: hash mọi height chung, balances/nonces của bốn node khớp.
- [ ] T28: accepted không là committed; không dùng UI tự chốt/bỏ qua lỗi.

## TV1-W5 · [TV1][W5] Rà core, hỗ trợ benchmark và chương blockchain

Phụ trách: TV1. Review: TV2, TV4. Mốc W5.
Bàn giao: src/core, test vectors, docs/report/core.md. Phụ thuộc: TV1-W4.

- Rà lỗi core; hỗ trợ workload hợp lệ và kiểm số dư/nonce.
- Bàn giao test vectors/ví dụ và viết chương blockchain/giao dịch.

Tiêu chí nghiệm thu:

- [ ] Benchmark phân biệt invalid input với lỗi hệ thống.
- [ ] Regression core đạt ở commit báo cáo.
- [ ] Tài liệu hash/signature/state khớp source và ví dụ tái hiện.

## TV2-W5 · [TV2][W5] Phân tích consensus, message count và giới hạn

Phụ trách: TV2. Review: TV1, TV4. Mốc W5.
Bàn giao: experiments, docs/report/consensus.md. Phụ thuộc: TV2-W4.

- Rà safety/liveness theo source; chương consensus/state diagram.
- Phối hợp TV4 đếm messages theo phase, phân tích quorum/latency/fault.

Tiêu chí nghiệm thu:

- [ ] Message count và timeline đối chiếu được log thô.
- [ ] Báo cáo phân biệt safety/liveness và ghi rõ fixed leader stall.
- [ ] Không tuyên bố chống hai Byzantine/auto leader recovery khi chưa cài.

## TV3-W5 · [TV3][W5] Triển khai máy mới và hướng dẫn vận hành

Phụ trách: TV3. Review: TV4; TV1/TV2 về recovery. Mốc W5.
Bàn giao: scripts, config, docs/deployment.md, docs/report/deployment.md. Phụ thuộc: TV3-W4.

- Checkout sạch trên máy khác; ổn định start/stop/log/config.
- Hỗ trợ workload/fault và metadata môi trường/commit.
- Chương triển khai/recovery; Docker/LAN chỉ sau khi lõi đạt.

Tiêu chí nghiệm thu:

- [ ] Người khác theo README chạy bốn node/test không phụ thuộc path tác giả.
- [ ] Không kill process ngoài repo hay xóa DB/keys âm thầm.
- [ ] Docs ghi topology, dữ liệu tách biệt và giới hạn cùng laptop.

## TV4-W5 · [TV4][W5] Thực nghiệm, CSV, latency/TPS và biểu đồ

Phụ trách: TV4 · @DaoNgocDinh. Review: TV2 (kết luận), TV3 (môi trường). Mốc W5.
Bàn giao: experiments, scripts, docs/report/evaluation.md. Phụ thuộc: TV4-W4, TV1-W5, TV2-W4, TV3-W5.

- Chạy baseline và kịch bản mục 16–17 kế hoạch, workload/warm-up/lặp có cấu hình.
- Raw CSV + seed/config/commit/OS/CPU/RAM/version; committed/rejected/unfinished.
- Tính TPS, latency p50/p95/p99, consistency, message count; plotting và chương đánh giá.

Tiêu chí nghiệm thu:

- [ ] Công thức, mốc đo, đơn vị/thời lượng rõ; accepted không tính committed.
- [ ] Báo cả unfinished/rejected/run lỗi, không loại để làm đẹp latency/TPS.
- [ ] Dữ liệu thô/script/config đối chiếu được; TV2 review claim safety/liveness.

## TV1-W6 · [TV1][W6] Nghiệm thu core và demo chuyển coin/tamper

Phụ trách: TV1. Review: TV2, TV4. Mốc W6.
Bàn giao: src/core, docs/report, docs/demo. Phụ thuộc: TV1-W5, TV4-W5.

- Sửa lỗi core chặn release; chương core/bảng đóng góp/test evidence.
- Demo chuyển coin/tamper và luyện giải thích hash/signature/nonce/atomic apply.

Tiêu chí nghiệm thu:

- [ ] Regression core đạt trên commit release.
- [ ] Demo có bằng chứng thật; chương core tích hợp báo cáo.
- [ ] Tham gia hai lần tổng duyệt; không còn lỗi core chặn nghiệm thu.

## TV2-W6 · [TV2][W6] Nghiệm thu consensus và demo quorum/leader lỗi

Phụ trách: TV2. Review: TV1, TV3, TV4. Mốc W6.
Bàn giao: src/consensus, docs/report, docs/demo. Phụ thuộc: TV2-W5, TV4-W5.

- Review claim report/slide; sửa lỗi consensus chặn release.
- Demo 2 phiếu chờ, 3 phiếu chốt, duplicate và leader lỗi; luyện vấn đáp.

Tiêu chí nghiệm thu:

- [ ] Consensus/fault regression đạt trên commit release.
- [ ] Vote/certificate demo bằng chữ ký/log thật.
- [ ] Slide ghi đúng fixed leader/giới hạn; hai lần tổng duyệt đạt.

## TV3-W6 · [TV3][W6] Checkout sạch, release và demo restart/sync

Phụ trách: TV3. Review: TV1, TV2, TV4. Mốc W6.
Bàn giao: README, scripts, config, docs/deployment.md. Phụ thuộc: TV3-W5, TV4-W5.

- Chốt hướng dẫn cài/chạy/test/dừng/sinh keys/genesis và sửa lỗi cuối.
- Đóng gói/tag sau cổng nghiệm thu toàn nhóm; demo follower restart/sync.

Tiêu chí nghiệm thu:

- [ ] Checkout sạch chạy/test thành công và có commit SHA bằng chứng.
- [ ] Release/config không chứa private key/.env/DB thật.
- [ ] Checklist release đầy đủ, backup demo và hai lần tổng duyệt đạt.

## TV4-W6 · [TV4][W6] Nghiệm thu cuối, báo cáo/slide/video và demo

Phụ trách: TV4 · @DaoNgocDinh. Review: Cả nhóm. Mốc W6.
Bàn giao: docs/report, docs/demo, test report, slides/video. Phụ thuộc: TV4-W5, TV1-W6, TV2-W6, TV3-W6.

- Tổng hợp chương từng người viết, bảng đóng góp/test report/release.
- Slide, demo khoảng 10 phút, video dự phòng, hướng dẫn máy mới.
- Điều phối freeze/nghiệm thu/hai lần tổng duyệt, ghi phần chưa đạt.

Tiêu chí nghiệm thu:

- [ ] Bộ bàn giao mục 20.2 đủ và khớp source/dữ liệu thật.
- [ ] Test bắt buộc có bằng chứng, lỗi chặn được sửa hoặc báo rõ.
- [ ] Hai lần tổng duyệt đạt; không tuyên bố PBFT/view change chưa kiểm chứng.
