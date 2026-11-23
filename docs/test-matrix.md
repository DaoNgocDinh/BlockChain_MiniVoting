# Ma trận kiểm thử T01–T30

Nguồn: [kế hoạch mục 15](ke-hoach.md#15-kế-hoạch-kiểm-thử), issue #4.
TV4 điều phối; mỗi chủ trì triển khai và lưu bằng chứng cho phần mình.
**Tất cả đang Not run**: ma trận W1 là kế hoạch kiểm thử, không phải kết quả test.
Lint/build, test adapter và demo wireframe không đủ chứng minh T01–T30 đạt.

## Quy ước thực thi và bằng chứng

- `Not run`: chưa chạy kịch bản trên commit được ghi. `Pass`: tất cả assertion đạt;
  `Fail`: có assertion sai hoặc run lỗi. Không đổi sang Pass chỉ vì review tài liệu.
- Mỗi run lưu `run_id`, T-ID, commit SHA, người chạy, thời gian/múi giờ, OS/CPU/RAM,
  Python/Node/dependency versions, topology, public genesis hash, config/fault plan,
  seed, lệnh tái hiện, đầu vào, expected/actual, trạng thái và liên kết log/artifact.
- Bằng chứng bắt buộc theo dòng dưới đây **chưa tồn tại** (—). Khi chạy, thêm link
  repo/artifact vào bản ghi run và ma trận, ghi cả lỗi, rejected, unfinished. Không
  commit private keys, DB thật hoặc thông tin bí mật.
- Unit dùng dữ liệu công khai/fixture của TV1; simulation dùng clock/transport có điều
  khiển của TV2; integration/fault dùng bốn node và DB/keys tách biệt của TV3.
  Sau lỗi kiểm ledger/hash/balances/nonces và invariants, không chỉ kiểm HTTP 200.
- Với test chống chốt, ghi cửa sổ quan sát theo timeout/fault config thực tế,
  kiểm height/state không đổi và không có proof hợp lệ bị bỏ sót. Không dùng sleep
  tùy ý làm bằng chứng safety. TV2 review giới hạn kết luận.

## Kịch bản, trách nhiệm và tiêu chí

| ID | Lớp / mốc | Thiết lập và thao tác | Kết quả bắt buộc | Chủ trì | Review | Bằng chứng cần lưu | Kết quả / link |
|---|---|---|---|---|---|---|---|
| T01 | Unit / W1 | Serialize cùng dữ liệu với thứ tự key khác nhau, cả object lồng | Cùng canonical bytes và hash | TV1 | TV2, TV3 | Public vector, bytes/hash và output assertion | Not run / — |
| T02 | Unit / W2 | Ký giao dịch rồi sửa amount | Verify chữ ký thất bại, không áp dụng | TV1 | TV2 | Tx trước/sau và lỗi verify | Not run / — |
| T03 | Unit / W2 | Amount âm, 0, float, bool, vượt giới hạn | Tất cả bị loại khỏi block hợp lệ | TV1 | TV3 | Bảng input và mã lỗi | Not run / — |
| T04 | Unit / W2 | Giao dịch ký cho chain khác | Từ chối; state không đổi | TV1 | TV2 | Context, lỗi và snapshot | Not run / — |
| T05 | Integration / W3 | Gửi lại cùng tx đã chốt, kể cả retry | Không trừ tiền/nonce lần hai | TV1, TV3 | TV4 | Tx ID, hai response, chỉ mục và state trước/sau | Not run / — |
| T06 | Unit / W2 | Sai nonce hoặc chi vượt balance | Không áp dụng; state không đổi | TV1 | TV3 | Input, lỗi, state trước/sau | Not run / — |
| T07 | Unit / W4 | Hai tx riêng lẻ có vẻ đủ nhưng tổng vượt balance; thử thứ tự | Không thể cùng thực thi hợp lệ | TV1 | TV2 | Thứ tự tx, từng bước balance/nonce | Not run / — |
| T08 | Unit + simulation / W2 | Proposal sai prev_hash hoặc height | Không tạo PREPARE | TV1, TV2 | TV3 | Proposal, lỗi validity và own-vote log | Not run / — |
| T09 | Unit / W2 | Leader khai state_hash khác kết quả replay | Validator tự tính và từ chối | TV1 | TV2 | State hash tính lại/khai báo | Not run / — |
| T10 | Simulation / W2 | Chỉ 2 PREPARE; ca riêng đủ PREPARE nhưng chỉ 2 COMMIT | Không chốt, không tạo COMMIT sớm | TV2 | TV1 | Message schedule, votes và state transitions | Not run / — |
| T11 | Integration / W3 | 3 COMMIT hợp lệ khác sender cùng block, gửi lặp proof | Có certificate, apply tối đa một lần | TV2, TV3 | TV1, TV4 | Certificate/chữ ký, commit log và state 4 node | Not run / — |
| T12 | Simulation / W2 | Một sender gửi 100 bản cùng vote | Chỉ tính 1 danh tính | TV2 | TV3 | 100 deliveries và unique counts | Not run / — |
| T13 | Simulation / W2 | Sender không thuộc genesis hoặc chữ ký sai | Không tăng quorum | TV2 | TV1 | Public keys, input và lỗi/unique counts | Not run / — |
| T14 | Simulation / W2 | Trộn PREPARE với COMMIT, height/chain/view/version sai | Không dùng cho certificate | TV2 | TV1, TV3 | Context matrix và proof rejection | Not run / — |
| T15 | Simulation + integration / W2–W4 | Phiếu đến trước proposal/prepared, đảo thứ tự và tới trễ | Buffer/đòi dữ liệu đúng; không chốt sai | TV2, TV3 | TV1 | Seed/schedule, buffer bounds và transitions | Not run / — |
| T16 | Fault / W4 | Leader ký hai proposal khác hash cùng context | Honest nodes không chốt xung đột; có thể stall | TV2 | TV1, TV3 | Hai proposal, evidence, locks và ledger honest nodes | Not run / — |
| T17 | Fault / W4 | Một Byzantine follower double-sign | Lưu evidence, không fork với giả định còn đúng | TV2 | TV1 | Vote cạnh tranh, evidence và certificate/ledger | Not run / — |
| T18 | Integration fault / W4 | Dừng một follower, gửi workload hợp lệ | Leader + 2 honest follower còn lại có thể tiếp tục | TV3 | TV2, TV4 | PID/node tắt, committed IDs và ledger ba node | Not run / — |
| T19 | Fault / W4 | Dừng leader cố định | Chờ/stall, không bầu mới hoặc hạ quorum | TV2, TV3 | TV4 | Leader ID, timeouts, counts và height trước/sau | Not run / — |
| T20 | Fault / W4 | Chia mạng 2–2, gửi tx ở mỗi nhóm | Không nhóm nào chốt height mới | TV3 | TV2 | Partition map, trace và ledger cả bốn node | Not run / — |
| T21 | Fault / W4 | Chia 3–1, leader trong nhóm 3 rồi nối lại | Nhóm 3 có thể chốt; node lẻ sync sau nối | TV3 | TV2, TV1 | Fault timeline, certificate và hash/state sau sync | Not run / — |
| T22 | Crash/restart / W4 | Crash sau lưu own PREPARE hoặc COMMIT, trước gửi/hoàn tất | Không ký hash mới; có thể phát lại đúng bytes cũ | TV2, TV3 | TV1 | Crash point, durable vote/lock và bytes phát lại | Not run / — |
| T23 | Crash/SQLite / W4 | Crash trước/trong/sau atomic apply block | Không nửa cập nhật hoặc double apply | TV1, TV3 | TV2 | Inject point, block/cert/index/state/height sau reopen | Not run / — |
| T24 | Recovery / W4 | Follower bỏ lỡ nhiều block rồi chạy lại | Tải, kiểm từng block/proof, đạt cùng state hash | TV3 | TV1, TV2 | Height thiếu, sync trace và state comparison | Not run / — |
| T25 | Fault sync / W4 | Peer phục vụ chuỗi dài có certificate giả | Không chấp nhận chỉ vì dài hơn | TV3 | TV2, TV1 | Chuỗi/proof công khai, lỗi và tip không đổi | Not run / — |
| T26 | Corruption / W4 | Sửa DB/body local hoặc block tải về | Phát hiện lỗi, không tiếp tục vote mù | TV1, TV3 | TV2 | Vị trí sửa, replay/check failure và halt evidence | Not run / — |
| T27 | End-to-end / W4 | 4 node hoàn thành cùng workload seed cố định | Cùng hash mọi height chung và balances/nonces | TV4 | TV1, TV3, TV2 | Workload, từng height/hash/state của 4 node | Not run / — |
| T28 | UI + integration / W3–W4 | API nhận tx nhưng cố giữ dưới quorum; sau đó cho chốt | Pending/proposed trước commit; chỉ báo committed khi API có bản ghi | TV4 | TV3, TV2 | HTTP 202, lookup/ledger theo thời gian và ảnh UI | Not run / — |
| T29 | Concurrency / W4 | Barrier cho 2 request tạo own vote khác hash đồng thời | Một lock/own vote nhất quán, không double-sign | TV2, TV3 | TV1 | Race schedule, constraints, bytes ký và DB sau reopen | Not run / — |
| T30 | Limits / W2–W4 | Body quá lớn; vote future-height xa; spam early votes | Từ chối/giới hạn buffer, bộ nhớ hữu hạn | TV3 | TV2, TV4 | Giới hạn có hiệu lực, response, buffer/memory evidence | Not run / — |

## Mẫu một bản ghi run

```text
run_id: <duy-nhat>
test_id: Txx
commit: <full-SHA>
runner / reviewed_by: <GitHub-user> / <cho-review>
started_at / ended_at: <ISO-8601 co timezone>
environment / versions: <artifact>
public_genesis_hash / topology / effective_config / seed: <artifact>
command / input / fault_schedule: <lenh va artifact>
expected / actual: <assertion va ket qua thuc>
result: Not run | Pass | Fail
evidence: <log, public proof, snapshot, anh; khong private key>
limitations / related_issue: <ghi ro>
```

TV4 tổng hợp kết quả khi có run, chủ trì giải thích lỗi, reviewer xác nhận kết luận.
Không đánh dấu hoàn tất #4 trước review; không coi ma trận W1 là nghiệm thu consensus.
