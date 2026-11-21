# Kế hoạch xây dựng blockchain mini có cơ chế voting đồng thuận cho nhóm 4 người

Ngày lập kế hoạch: 18/11/2026. Môn học: Chuỗi khối và công nghệ sổ cái phân tán.

## 1. Quyết định đề xuất

Nhóm xây dựng một **blockchain riêng gồm 4 validator có danh tính cố định**, dùng giao dịch chuyển coin giả lập để minh họa. Mỗi validator chạy bằng một tiến trình độc lập, có khóa ký, cơ sở dữ liệu và thuật toán kiểm tra riêng. Một block chỉ được chốt khi có chứng nhận gồm **ít nhất 3 chữ ký COMMIT hợp lệ từ 4 validator**.

Bản lõi dùng giao thức ba pha do nhóm đặc tả, lấy cảm hứng từ PBFT: **PROPOSE → PREPARE → COMMIT**. Tất cả validator, kể cả leader, có thể phát phiếu PREPARE và COMMIT. Đây là lựa chọn thiết kế cho đồ án; **không phải bản cài đặt PBFT nguyên gốc đầy đủ**. Leader cố định trong bản lõi; việc đổi leader khi đang xử lý một height là phần nâng cao, chỉ làm sau khi có đặc tả an toàn rõ ràng.

Lý do chọn: đủ thể hiện blockchain, sổ cái phân tán, chữ ký, kiểm tra giao dịch, quorum, tính nhất quán và hành vi lỗi; vẫn có thể hoàn thành với 4 sinh viên. Độ tốt của đồ án được thể hiện bằng các quy tắc nhất quán, bằng chứng voting và thực nghiệm có thể chạy lại.

**Giả định lập kế hoạch:** nhóm có 6 tuần, trung bình 10 giờ/người/tuần, tương đương khoảng 240 giờ công. Chưa có deadline, rubric, yêu cầu ngôn ngữ hay yêu cầu PBFT đầy đủ từ giảng viên. Đây là kế hoạch đề xuất, không phải yêu cầu đã được giảng viên xác nhận. Nếu giảng viên bắt buộc tự động đổi leader và tiếp tục chạy khi leader Byzantine, dành thêm 2 tuần và coi phần nâng cao là bắt buộc.

## 2. Tên đề tài và kết quả phải trình bày được

Tên đề xuất: **Xây dựng blockchain mini trong mạng permissioned sử dụng cơ chế voting đồng thuận giữa các validator**.

Mô tả ngắn để đăng ký đề tài:

> Xây dựng hệ thống blockchain mini với bốn validator độc lập. Các giao dịch được ký số, kiểm tra, gom thành block và xác nhận bằng cơ chế voting với ngưỡng ba trên bốn validator. Hệ thống trực quan hóa các pha đồng thuận, phát hiện dữ liệu và phiếu không hợp lệ, hỗ trợ lưu trữ và đồng bộ node, đồng thời đánh giá tính nhất quán và hiệu năng trong một số kịch bản lỗi.

Sau khi hoàn thành, cả nhóm phải giải thích được:

1. Block liên kết với nhau thế nào, sửa dữ liệu bị phát hiện ở đâu.
2. Vì sao hash đơn thuần chưa tạo ra đồng thuận.
3. Ai được bỏ phiếu, làm sao xác thực phiếu và chống đếm lặp.
4. Vì sao chọn 3/4 thay vì 2/4 và vì sao không hạ ngưỡng khi mất node.
5. Khi nào giao dịch đang chờ, đã được đề xuất, hoặc đã chốt.
6. Mỗi node có sổ cái riêng nhưng vẫn thực thi cùng một chuỗi giao dịch như thế nào.
7. Bản lõi giữ được điều gì khi có lỗi, và trường hợp nào có thể ngừng tiến triển.
8. Kết quả thực nghiệm chứng minh được điều gì, chưa chứng minh được điều gì.

**Voting ở đây là validator bỏ phiếu xác nhận block.** Ứng dụng bỏ phiếu bầu cử cho người dùng là một bài toán nghiệp vụ khác. Nếu xây đồng thời cả hai, độ phức tạp tăng mà chưa chắc giúp làm rõ cơ chế đồng thuận.

## 3. Kiến thức cần học và cách hiểu

| Khái niệm | Hiểu đơn giản | Nhóm phải áp dụng được |
|---|---|---|
| Sổ cái phân tán | Nhiều node giữ các bản sao dữ liệu | Mỗi node có database riêng; không dùng một database chung |
| Block | Một lô giao dịch cùng phần thông tin kiểm tra | Header, giao dịch theo thứ tự, hash và chứng nhận commit |
| Hash | Dấu vân tay của dữ liệu | Băm dữ liệu chuẩn hóa bằng SHA-256; sửa dữ liệu thì kiểm tra thất bại |
| Chữ ký số | Bằng chứng ai đã xác nhận một thông điệp | Xác minh giao dịch và phiếu bằng public key đã biết |
| Validator | Node được cấp quyền tham gia đồng thuận | Danh sách 4 validator được cố định trong genesis |
| Leader | Node đề xuất block | Đề xuất không có nghĩa là được tự chốt |
| Quorum | Số phiếu hợp lệ cần thiết | 3 validator khác nhau, cùng phase, height và block hash |
| Finality | Trạng thái block đã được chốt theo giao thức | Có commit certificate hợp lệ; không tự thay bằng chuỗi dài hơn |
| Safety | Không chốt hai block xung đột ở các node trung thực | Kiểm tra fork ở cùng height, lưu khóa chống ký hai lần |
| Liveness | Cuối cùng vẫn chốt được khi điều kiện tiến triển được đáp ứng | Bản lõi cần leader hoạt động và đủ node trung thực liên lạc được |
| Byzantine | Node có thể nói dối, gửi hai nội dung hoặc ký sai | Mô phỏng một validator gửi phiếu xung đột hoặc dữ liệu sai |
| State machine | Cùng trạng thái và cùng lệnh thì cho cùng kết quả | Thực thi giao dịch theo đúng thứ tự trong block |
| Nonce giao dịch | Số thứ tự giao dịch của một tài khoản | Chống phát lại và xác định thứ tự chi tiêu của tài khoản |
| Mempool | Tập giao dịch chưa được chốt | Không được coi giao dịch trong mempool là số dư đã cập nhật |
| Certificate | Tập bằng chứng chữ ký đạt quorum | Node tự kiểm chứng từng chữ ký thay vì tin thông báo của leader |

Đọc nền tảng blockchain ở [R1]; học bài toán Byzantine, state machine replication và view change ở [R2–R4]. Các phần thiết kế, mốc tiến độ, test và tham số trong tài liệu này là đề xuất riêng cho đồ án.

## 4. Chọn phương pháp đồng thuận

| Phương án | Điểm phù hợp | Khó khăn hoặc giới hạn | Vai trò trong đồ án |
|---|---|---|---|
| Một server tự ghi | Dễ làm, có baseline đo overhead | Không thể hiện voting giữa các validator | Chỉ dùng làm baseline thí nghiệm |
| Voting 2/4 tùy ý | Nhìn đơn giản | Hai nhóm 2 node có thể ủng hộ hai block; thiếu cơ sở an toàn | Không chọn |
| Raft | Phân tách bầu leader, nhân bản log; phù hợp lỗi dừng | Raft tiêu chuẩn không xử lý node Byzantine | Tham khảo nếu giảng viên chỉ yêu cầu crash fault |
| PBFT đầy đủ | Tài liệu chuẩn về lỗi Byzantine và đổi leader | View change, recovery, log, checkpoint và timeout cần xử lý cẩn thận | Nền tảng lý thuyết, mục tiêu nâng cao |
| Giao thức ba pha trong tài liệu này | Tự viết, dễ quan sát, quy mô phù hợp | Chủ động giới hạn liveness khi leader lỗi | Phương án lõi đề xuất |
| Dùng engine CometBFT | Tham khảo cách tổ chức consensus và khóa bỏ phiếu | Dùng engine có thể không đáp ứng tiêu chí tự cài thuật toán | Nguồn học nâng cao; chỉ dùng nếu giảng viên cho phép |

PBFT được đề xuất bởi Miguel Castro và Barbara Liskov năm 1999 [R2]. Raft được thiết kế cho mô hình lỗi không Byzantine [R5]. Đừng gọi đồ án là PoS chỉ vì có voting: kế hoạch này không có stake, slashing hay quy tắc lựa chọn theo tài sản. Cũng không cần ghép PoW vào để tạo block.

### 4.1 Vì sao chọn 4 node và 3 phiếu

Trong mô hình PBFT thông dụng, số node n = 3f + 1 để xét tối đa f node Byzantine; với n = 4 thì f = 1 [R2, R4]. Đồ án cố định bốn validator có trọng số bằng nhau và đặt q = 3.

Hai tập phiếu có 3 phần tử trong tập 4 validator phải giao nhau ít nhất:

`|Q1 ∩ Q2| ≥ 3 + 3 − 4 = 2`.

Nếu nhiều nhất 1 validator Byzantine, phần giao chứa ít nhất 1 validator trung thực. Với quy tắc validator trung thực không ký hai giá trị khác nhau cho cùng phase và height, hai chứng nhận xung đột cho cùng phase và height không thể cùng được tạo. Đây là lập luận cơ sở cho thiết kế cố định trong đồ án; không thay thế chứng minh đầy đủ về view change, recovery hay liveness.

Quorum luôn tính trên **danh sách genesis gồm 4 validator**, không tính trên số node đang hiện màu xanh. Chỉ còn 2 node online vẫn cần 3 phiếu, vì vậy hệ thống phải chờ.

### 4.2 Phạm vi bảo đảm phải viết đúng

| Tình huống | Bản lõi dự kiến làm được | Điều kiện và giới hạn |
|---|---|---|
| Cả 4 node trung thực, mạng hoạt động | Tiếp tục chốt block | Giao dịch hợp lệ, không quá tải |
| 1 follower ngừng hoặc từ chối vote | 3 node còn lại có thể chốt | Leader trung thực còn hoạt động; thông điệp giữa 3 node được chuyển tới |
| 1 follower gửi phiếu sai | Loại phiếu sai; các node trung thực vẫn có thể chốt | Tổng số validator Byzantine không vượt 1 |
| Leader không gửi hoặc gửi block không hợp lệ | Không chốt block sai | Bản lõi có thể dừng ở height đó |
| Leader gửi hai block hợp lệ cạnh tranh | Không chốt cả hai | Có thể bị kẹt do phiếu chia; không tự mở khóa |
| Mạng chia 2–2 | Không bên nào đủ quorum | Dừng tiến triển là kết quả mong đợi |
| Mạng chia 3–1 | Nhóm 3 có thể tiếp tục | Nhóm 3 phải có leader và đủ hành vi trung thực phù hợp |
| Node khởi động lại | Giữ quyết định ký cũ và đồng bộ block thiếu | Khóa ký và dữ liệu bền vững còn nguyên |
| 2 validator Byzantine | Ngoài mô hình bảo đảm | Test để minh họa giới hạn, không công bố hệ thống vẫn BFT |

Bản lõi hướng tới safety theo các bất biến đã đặc tả, nhưng **không bảo đảm liveness khi leader hỏng hoặc khi đã chia phiếu cho các đề xuất khác nhau**. Không mô tả chung chung rằng hệ thống luôn tiếp tục chạy khi bất kỳ 1 node nào hỏng. PBFT đầy đủ cần view change để xử lý leader lỗi [R3].

## 5. Phạm vi chức năng

### 5.1 Chức năng bắt buộc

| Mã | Chức năng | Tiêu chí nghiệm thu |
|---|---|---|
| F01 | Nạp cấu hình genesis chung | 4 node có cùng chain ID, genesis hash, danh sách validator và số dư ban đầu |
| F02 | Tạo và ký giao dịch | Có công cụ ví thử nghiệm; node kiểm tra chữ ký và địa chỉ người gửi |
| F03 | Kiểm tra giao dịch | Chặn amount không hợp lệ, sai nonce, sai chain ID, thiếu số dư, trùng giao dịch |
| F04 | Tiếp nhận và chuyển giao dịch | Gửi tới một node rồi chuyển tới leader; API trả trạng thái đang chờ |
| F05 | Mempool và tạo block | Leader gom giao dịch theo thứ tự xác định, không áp dụng số dư vĩnh viễn trước commit |
| F06 | Kiểm tra block | Kiểm tra prev_hash, height, hash giao dịch, state hash, chữ ký và thực thi tuần tự |
| F07 | Voting ba pha | Có thể quan sát PROPOSE, PREPARE, COMMIT và số validator đã ký |
| F08 | Xác minh quorum | Đếm 3 danh tính hợp lệ khác nhau, không đếm số request HTTP |
| F09 | Chốt và lưu bền vững | Ghi block, certificate, số dư và nonce nguyên tử; không áp dụng lặp |
| F10 | Đồng bộ node bị chậm | Tải từng block còn thiếu, kiểm chứng certificate và replay từ trạng thái tin cậy |
| F11 | Phục hồi sau restart | Không quên phiếu đã ký; khôi phục đề xuất còn dở và trạng thái chốt |
| F12 | Trực quan hóa | Dashboard thấy 4 node, block, giao dịch, phiếu, certificate và trạng thái chờ |
| F13 | Mô phỏng lỗi | Có kịch bản dừng follower, chia mạng, phiếu giả, phiếu lặp và leader lỗi |
| F14 | Đánh giá và xuất kết quả | Có script chạy workload, CSV kết quả, biểu đồ và mô tả cấu hình |

### 5.2 Chức năng làm khi còn thời gian

Ưu tiên theo thứ tự: biểu đồ timeline tốt hơn; Merkle tree và Merkle proof; triển khai bốn máy trong LAN; fault injection có seed; kiểm thử sinh chuỗi sự kiện ngẫu nhiên; cuối cùng là view change theo một giao thức đã chọn đầy đủ.

Không đưa vào bản lõi: tiền thật, kết nối mainnet, smart contract VM, staking, mining, NFT, ví trình duyệt phức tạp, đăng nhập đa vai trò, node tham gia tùy ý, thay đổi validator động, Kubernetes. Những phần này làm tăng phạm vi nhưng không cần để chứng minh đề tài.

## 6. Kiến trúc và công nghệ

### 6.1 Stack đề xuất

| Thành phần | Lựa chọn | Lý do và quy tắc |
|---|---|---|
| Ngôn ngữ node | Python 3.13 | Dễ đọc thuật toán; cả nhóm thống nhất một phiên bản phụ đã kiểm tra |
| HTTP API | FastAPI và Uvicorn | Khai báo schema, tài liệu API, dễ kiểm thử [R9] |
| Gửi thông điệp | HTTPX bất đồng bộ | Một lớp transport dùng chung; hỗ trợ timeout, retry và fault injection |
| Schema | Pydantic | Kiểm tra kiểu và giới hạn dữ liệu ngay cửa vào |
| Hash | hashlib SHA-256 | Thư viện chuẩn Python [R6] |
| Chữ ký | Ed25519 bằng cryptography | Dùng API ký và kiểm chứng sẵn có [R8]; không tự viết thuật toán mật mã |
| Lưu trữ | SQLite riêng cho từng node | Không cần dựng DB server; dùng transaction [R10] |
| Giao diện | React với Vite | Phù hợp nếu nhóm đã quen React; polling trước, SSE sau |
| Kiểm thử | pytest, HTTPX, test nhiều tiến trình | Kiểm thử từ hàm thuần đến hệ thống [R11, R12] |
| Chạy local | Script PowerShell mở 4 tiến trình | Cài đặt đơn giản trên Windows; có script dừng đúng tiến trình của đồ án |
| Đóng gói tùy chọn | Docker Compose | Mỗi node một container và volume riêng [R13] |
| Quản lý mã | Git và pull request | Nhánh ngắn theo tính năng, review chéo [R14] |

Đây là lựa chọn phù hợp với quy mô đề xuất, không phải so sánh chứng minh Python nhanh nhất. Chốt phiên bản thư viện thực sự cài được trong tuần 1, lưu lockfile hoặc requirements đã pin; không để các máy tự lấy mọi phiên bản mới nhất.

### 6.2 Tổ chức chạy hệ thống

| Node | Vai trò bản lõi | Cổng local gợi ý | Dữ liệu riêng | Khóa riêng |
|---|---|---|---|---|
| node1 | Leader và validator | 8001 | data/node1/ledger.sqlite | keys/node1.key |
| node2 | Validator | 8002 | data/node2/ledger.sqlite | keys/node2.key |
| node3 | Validator | 8003 | data/node3/ledger.sqlite | keys/node3.key |
| node4 | Validator | 8004 | data/node4/ledger.sqlite | keys/node4.key |

4 thành viên không viết 4 phiên bản node khác nhau. Nhóm viết **một bộ mã node**, chạy với 4 cấu hình. Mỗi người có thể chịu trách nhiệm triển khai một node khi demo trên LAN, nhưng phần việc lập trình chia theo module.

Node giao tiếp trực tiếp với các peer. Dashboard chỉ gửi yêu cầu, đọc API và hiển thị; không giữ private key của validator và không quyết định consensus. Một API gateway cho giao diện là tùy chọn, không phải cơ quan chốt block.

Chạy 4 tiến trình trên một laptop chứng minh sự độc lập logic của node, chưa chứng minh khả năng chống lỗi hạ tầng khi máy tính đó tắt. Thử trên 4 máy là một thí nghiệm triển khai riêng.

## 7. Cấu trúc dữ liệu và hợp đồng dùng chung

Hoàn thành đặc tả ở tuần 1 trước khi từng người mở rộng module. Các trường dưới đây là thiết kế đề xuất, có thể giảm nếu cả nhóm thống nhất bằng tài liệu.

### 7.1 Genesis

Chứa protocol_version, chain_id, danh sách validator theo thứ tự cố định, public key từng validator, leader_id cố định, quorum = 3, danh sách tài khoản và số dư ban đầu, giới hạn kích thước block. Height genesis bằng 0, prev_hash dùng giá trị quy ước cố định.

Tạo genesis một lần rồi phân phối cùng byte/hash cho mọi node. Khi mở node, đối chiếu genesis hash với giá trị tin cậy trong cấu hình. Genesis là điểm tin cậy ban đầu; không tự tải một genesis khác từ peer rồi chấp nhận. Genesis không cần certificate của một height trước nó.

### 7.2 Giao dịch chuyển coin

| Trường | Ý nghĩa | Quy tắc |
|---|---|---|
| protocol_version | Phiên bản giao thức | Khớp phiên bản được node hỗ trợ |
| chain_id | Mạng nhận giao dịch | Khớp genesis để chống dùng giao dịch ở mạng khác |
| sender_public_key | Public key của người gửi | Mã hóa hex thống nhất |
| sender | Địa chỉ người gửi | SHA-256 của public key theo quy ước duy nhất |
| recipient | Địa chỉ nhận | Định dạng địa chỉ hợp lệ; tạo tài khoản số dư 0 khi chưa tồn tại |
| amount | Số coin chuyển | Số nguyên dương theo đơn vị nhỏ nhất |
| nonce | Thứ tự giao dịch của sender | Bằng nonce đã chốt + 1, có xét các giao dịch trước nó trong block |
| signature | Chữ ký người gửi | Ký dữ liệu giao dịch chưa có signature và tx_id, có domain riêng |
| tx_id | Định danh giao dịch | SHA-256 của dữ liệu giao dịch chuẩn hóa chưa có signature và tx_id |

Ví dụ diễn giải: Alice có 100 coin, nonce đã chốt là 0; giao dịch Alice chuyển Bob 20 coin với nonce 1. Chỉ khi block chứa giao dịch được commit, số dư thành Alice 80, Bob tăng 20, nonce Alice thành 1. Gửi lại cùng giao dịch không được trừ Alice thêm lần nữa.

MVP nên giới hạn mỗi tài khoản tối đa một giao dịch chưa chốt để xử lý mempool đơn giản. Khi kiểm thử block có nhiều giao dịch cùng tài khoản, vẫn phải thực thi lần lượt theo nonce. Nếu mở rộng nhận future nonce trong mempool, tách hàng đợi và chỉ đưa vào block khi đã có đủ các nonce trước.

Không có phí và không mint sau genesis thì tổng số dư phải được bảo toàn. Đây là bất biến nghiệp vụ hữu ích để tìm lỗi áp dụng hai lần hoặc thiếu cập nhật.

### 7.3 Block và certificate

Header đề xuất gồm protocol_version, chain_id, height, prev_hash, proposer_id, timestamp_ms, tx_list_hash, state_hash. Body chứa danh sách giao dịch đầy đủ theo thứ tự. block_hash là SHA-256 của header chuẩn hóa; tx_list_hash cam kết toàn bộ danh sách giao dịch và thứ tự. Chữ ký proposal của leader tham chiếu block_hash.

state_hash được tính sau khi chạy thử toàn bộ giao dịch trên bản sao trạng thái. Trạng thái băm chứa các tài khoản được sắp xếp theo địa chỉ, mỗi tài khoản có balance và nonce. Node tự tính lại, không tin state_hash leader gửi.

**Commit certificate nằm ngoài phần được băm để tạo block_hash**. Nó chứa ít nhất 3 COMMIT có chữ ký hợp lệ, cùng chain ID, height, view = 0 và block hash, từ 3 validator khác nhau. Một số node có thể lưu 3 chữ ký, node khác lưu 4 chữ ký; điều này không làm block_hash khác nhau. Nếu băm certificate vào chính block mà certificate xác nhận, sẽ tạo phụ thuộc vòng.

MVP dùng hash cả danh sách giao dịch thay cho Merkle root để giảm việc. Báo cáo ghi đúng lựa chọn này. Nếu có Merkle tree, phải bổ sung quy tắc thứ tự lá, trường hợp số lá lẻ và cách kiểm Merkle proof.

### 7.4 Thông điệp đồng thuận

Phần message được ký gồm protocol_version, chain_id, phase, height, view, block_hash, sender_id. Phase thuộc PROPOSE, PREPARE, COMMIT. view luôn bằng 0 trong bản lõi và mọi view khác bị từ chối.

Các attachment như block, proposal có chữ ký hoặc prepared certificate đi kèm được kiểm tra riêng dựa trên hash và từng chữ ký. Một attachment không được tự nhiên coi là tin cậy chỉ vì đi cùng request từ peer.

Danh tính sender_id phải ánh xạ tới public key trong genesis. Mỗi validator trung thực chỉ được ký một block_hash cho một cặp height và phase, đồng thời không được đổi block đã khóa tại height đó. Khóa chống ký hai lần phải được lưu bền vững.

### 7.5 Chuẩn hóa trước khi hash và ký

1. Chỉ một hàm serialization dùng chung cho mọi node, ví và test.
2. Quy định UTF-8, key JSON sắp xếp, không khoảng trắng dư; dữ liệu lõi chỉ dùng chuỗi định dạng cố định và số nguyên.
3. Từ chối duplicate keys khi parse, unknown fields nếu schema không cho phép, bool giả làm int, NaN, Infinity và float cho amount/nonce.
4. Giới hạn số nguyên trong phạm vi đã thống nhất; nếu giao diện dùng JavaScript Number thì không vượt 2^53 − 1. Nếu cần lớn hơn, truyền dạng chuỗi số có quy tắc riêng.
5. Không ký trường signature, không băm block_hash vào chính dữ liệu tạo block_hash.
6. Dùng domain khác nhau cho TX, PROPOSE, PREPARE và COMMIT để không tái sử dụng chữ ký sai ngữ cảnh.
7. timestamp do proposer đưa vào block, chỉ để hiển thị trong MVP; không lấy giờ máy từng node để tính kết quả thực thi.
8. Có test vector cố định: dữ liệu vào, byte chuẩn hóa, tx_id, block_hash và chữ ký mẫu để các module kiểm chứng cùng kết quả.

Các tùy chọn sort_keys và separators có trong thư viện json [R7], nhưng gọi json.dumps không tự động giải quyết toàn bộ vấn đề canonical JSON giữa các ngôn ngữ. Bản lõi dùng Python thống nhất để giảm khác biệt; frontend không tự tính hash theo một quy tắc khác.

## 8. Giao thức voting bản lõi

### 8.1 Luồng xử lý bình thường

1. Client tạo giao dịch, ký và gửi tới một node. Node xác minh cơ bản, chống trùng, đưa vào mempool và chuyển tới leader nếu cần.
2. Leader chọn giao dịch, thực thi thử trên bản sao trạng thái, tạo block tại height kế tiếp. Leader lưu bền vững nội dung proposal trước khi phát; restart phải gửi lại chính proposal này.
3. Leader gửi PROPOSE có chữ ký kèm block cho cả mạng.
4. Mỗi node kiểm tra leader, chain ID, height, prev_hash, hash dữ liệu, chữ ký giao dịch và trạng thái sau thực thi.
5. Nếu hợp lệ và chưa khóa giá trị khác tại height, node lưu quyết định ký PREPARE rồi phát PREPARE cho mọi validator. Leader cũng tự kiểm tra và PREPARE như một validator.
6. Khi node thu đủ 3 PREPARE hợp lệ, khác danh tính, cùng block, node tạo prepared certificate. Nó lưu quyết định ký COMMIT rồi phát COMMIT cho mọi validator.
7. Khi thu đủ 3 COMMIT hợp lệ, node tạo commit certificate. Sau khi xác minh block, proposal và certificate, node chốt block và cập nhật trạng thái bằng một transaction database.
8. Node phát thông báo đã chốt kèm bằng chứng, gỡ các giao dịch đã chốt khỏi mempool và bắt đầu height tiếp theo. Peer nhận thông báo vẫn tự xác minh trước khi ghi.
9. Client tra trạng thái giao dịch. HTTP 202 chỉ có nghĩa đã tiếp nhận; chỉ hiển thị đã chốt khi kiểm tra được block/certificate tương ứng.

Không dùng một hàm trong leader chạy bốn lần rồi tự gán phiếu cho bốn validator. Phiếu phải thực sự xuất phát từ tiến trình có private key tương ứng.

### 8.2 Quy tắc chấp nhận thông điệp

| Kiểm tra | Kết quả khi không đạt |
|---|---|
| Đúng protocol_version và chain_id | Loại và ghi lý do |
| sender là validator được cấp quyền | Loại; public key tự khai trong request không tạo quyền vote |
| Chữ ký khớp toàn bộ nội dung chuẩn hóa | Loại |
| PROPOSE do leader cấu hình ký | Loại nếu sender không phải leader |
| Đúng height; không trộn phiếu giữa các height | Phiếu cũ không thay đổi quyết định; phiếu tương lai chỉ buffer có giới hạn |
| Đúng view = 0 | Loại trong MVP |
| Block đúng prev_hash và chạy ra state_hash đúng | Không PREPARE nếu sai |
| Chưa ký hash khác cho height đó | Không ký giá trị xung đột, kể cả sau restart |
| Mỗi sender được tính một lần mỗi phase | Duplicate không tăng số phiếu |
| COMMIT được phát khi có prepared certificate | Node trung thực chỉ phát sau kiểm tra 3 PREPARE |
| Commit certificate gồm đủ 3 chữ ký | Không append khi thiếu hoặc có chữ ký không hợp lệ |

Phiếu COMMIT tới trước PROPOSE hoặc PREPARE do mạng đảo thứ tự không được lập tức dùng để ghi sổ. Node có thể giữ trong bộ đệm giới hạn và yêu cầu block/proof còn thiếu; sau khi dữ liệu đủ mới xác minh và tiến trạng thái. Giới hạn kích thước body và buffer để tránh peer gửi vô hạn dữ liệu.

### 8.3 Bỏ phiếu phản đối và timeout

Node gặp block sai ghi sự kiện REJECT kèm mã lỗi. REJECT không phải phiếu COMMIT, không cộng vào quorum; không cần thêm phép đếm đa số phiếu NO để kết luận an toàn.

Timeout ban đầu gợi ý: 3–5 giây cho cảnh báo chờ, request timeout khoảng 1 giây trong local test, retry có backoff và giới hạn tần suất. Đây là tham số khởi đầu để đo, không phải điều kiện chứng minh safety.

Timeout **không** cho phép hạ quorum, tự chốt, xóa khóa ký, thay block khác ở cùng height hoặc tự đổi leader. Hiển thị WAITING_QUORUM hoặc LEADER_UNAVAILABLE và tiếp tục retry đúng nội dung đã lưu. Khi lỗi được khắc phục, hoàn thành cùng giá trị nếu giao thức cho phép; nếu đã chia phiếu và không thể đủ quorum, bản lõi dừng thay vì cố mở khóa.

Nếu muốn chạy lại một thí nghiệm từ đầu, tạo mạng thử nghiệm mới với chain ID/genesis mới bằng script có chủ đích. Không xóa lock của một node rồi cho nó tái tham gia cùng chuỗi như chưa từng ký.

### 8.4 Pseudocode để cả nhóm thống nhất

```text
on_proposal(proposal, block):
    verify_leader_signature_and_context(proposal)
    validate_block_against_committed_state(block)
    if durable_height_lock_conflicts(block.height, block.hash):
        reject_and_record_evidence()
        return
    persist_lock_and_own_prepare_before_sending(block)
    broadcast_or_resend_own_prepare(block.hash)

on_prepare(vote):
    verify_context_signature_and_sender(vote)
    store_without_double_counting(vote)
    if have_valid_block_and_3_matching_prepares(vote.height, vote.block_hash):
        persist_prepared_certificate()
        persist_own_commit_before_sending()
        broadcast_or_resend_own_commit()

on_commit(vote):
    verify_context_signature_and_sender(vote)
    store_without_double_counting(vote)
    if have_3_matching_commits():
        obtain_and_verify_block_proposal_and_commit_certificate()
        append_block_and_apply_state_atomically_once()
        broadcast_finalized_block_with_certificate()
```

Đây là pseudocode định hướng; phải bổ sung quản lý thứ tự thông điệp, truy xuất dữ liệu thiếu, lưu trữ, lỗi I/O và xử lý đồng thời trong mã thật.

## 9. Bất biến an toàn và lỗi triển khai cần tránh

1. Mỗi height đã chốt có đúng một block_hash trong một node trung thực.
2. Hai node trung thực đã chốt cùng height phải có cùng block_hash.
3. Không node nào tự ghi block chỉ dựa trên lời nói của leader.
4. Phiếu có cùng sender dù gửi 100 lần vẫn chỉ được tính một lần.
5. Không dùng lại chữ ký PREPARE làm COMMIT hoặc vote của mạng/height khác.
6. Mỗi giao dịch được áp dụng tối đa một lần vào trạng thái đã chốt.
7. Mọi account balance không âm, nonce tăng đúng quy tắc; tổng số dư không đổi khi không có phí/mint.
8. Block chưa chốt không làm thay đổi trạng thái số dư chính thức.
9. Restart không cho validator ký một hash khác tại height đã khóa.
10. Mỗi node dùng storage riêng và chỉ private key riêng của nó để bỏ phiếu.
11. Callback xử lý đồng thời không được tạo hai own vote xung đột; cần hàng đợi sự kiện hoặc khóa/transaction phù hợp.
12. Node đồng bộ phải kiểm tra liên kết hash, chữ ký, certificate và thực thi lại; không chọn chuỗi chỉ vì dài hơn.

Lập luận quorum phụ thuộc vào giả định private key không bị chiếm quá một validator, genesis được phân phối đúng, hàm hash và chữ ký hoạt động theo giả định mật mã. Kết quả test không thay thế chứng minh hình thức cho mọi lịch thông điệp.

## 10. Lưu trữ và phục hồi

### 10.1 Các bảng gợi ý

| Bảng | Dữ liệu chính | Ràng buộc cần có |
|---|---|---|
| blocks | height, hash, prev_hash, header, body | UNIQUE(height), UNIQUE(hash) |
| committed_transactions | tx_id, block_height, thứ tự trong block | UNIQUE(tx_id) |
| accounts | address, balance, nonce | UNIQUE(address), balance không âm |
| own_votes | chain_id, height, phase, block_hash, signed_bytes | UNIQUE(chain_id, height, phase) và kiểm tra lock theo height |
| height_locks | chain_id, height, block_hash | UNIQUE(chain_id, height) |
| received_votes | context, sender_id, signature | Chỉ một phiếu được đếm theo sender và phase; giữ bằng chứng xung đột riêng |
| certificates | height, block_hash, phase, tập chữ ký | Kiểm chứng trước khi dùng |
| pending_proposals | height, block bytes, proposal signature | Leader không tạo nội dung khác sau restart |
| node_metadata | chain/genesis hash, committed height, schema version | Không ghi đè genesis khi không khớp |

Đây là thiết kế logic; có thể gộp bảng nếu vẫn giữ được ràng buộc. Lưu JSON canonical cần thiết để replay, không chỉ lưu số đếm vote.

### 10.2 Điểm ghi nguyên tử

Trước khi gửi phiếu của mình: ghi bền vững lock và nội dung đã ký. Nếu ghi thất bại, không gửi phiếu. Chọn cấu hình SQLite hỗ trợ mức bền vững đã công bố; kiểm tra crash test thay vì mặc định mọi file đã được flush.

Khi commit: ghi block, commit certificate, applied transaction IDs, balances, nonces và committed height trong một transaction. Crash phải dẫn tới toàn bộ thay đổi đã được áp dụng hoặc chưa được áp dụng, không ở trạng thái trừ tiền rồi chưa ghi block.

Khi restart: kiểm tra genesis; đọc committed state và own votes; kiểm tra nhất quán local; gửi lại phiếu đã lưu nếu cần; đồng bộ các height thiếu. Nếu phát hiện dữ liệu local bị sửa, đưa node vào trạng thái không bỏ phiếu để replay/phục hồi từ genesis và certificate tin cậy; giữ bằng chứng và dữ liệu chống ký hai lần.

### 10.3 Đồng bộ node

1. Node nhận biết đang chậm qua committed height/hash từ các peer.
2. Yêu cầu block tại height kế tiếp cùng commit certificate; số height peer công bố chỉ là gợi ý.
3. Kiểm tra genesis/chain ID, proposer, prev_hash, quorum và chữ ký.
4. Thực thi lại giao dịch trên trạng thái local, kiểm tra state_hash rồi ghi nguyên tử.
5. Lặp đến khi theo kịp; giới hạn lô và kích thước dữ liệu.
6. Nếu gặp hai certificate xung đột đều có vẻ hợp lệ, dừng và báo sự cố vượt giả định; không tự chọn chuỗi dài nhất.

## 11. API và cấu trúc mã nguồn đề xuất

### 11.1 API dùng chung

| Method và đường dẫn | Mục đích | Lưu ý |
|---|---|---|
| GET /health | Tiến trình còn phản hồi | Khác với node đã đồng bộ hoặc còn đủ quorum |
| GET /status | node_id, leader, height, tip hash, phase, sync state | Dùng cho dashboard và script |
| POST /transactions | Nhận giao dịch đã ký | Trả tx_id và trạng thái; 202 chưa phải committed |
| GET /transactions/{tx_id} | Tra pending/committed/rejected/local-unknown | Nêu block height nếu đã chốt |
| GET /accounts/{address} | Số dư và nonce đã chốt | Không cộng số dư đang chờ |
| GET /blocks | Phân trang block đã chốt | Giới hạn page size |
| GET /blocks/{height} | Block và certificate | Dùng cho explorer và sync |
| GET /consensus/{height} | Proposal, phase, vote IDs và chứng nhận | Chỉ dữ liệu quan sát; không có nút gán phiếu |
| POST /peer/propose | Nhận đề xuất | Kiểm chữ ký leader và block |
| POST /peer/prepare | Nhận PREPARE | Xác minh và chống duplicate |
| POST /peer/commit | Nhận COMMIT | Chưa đủ dữ liệu thì buffer có giới hạn |
| POST /peer/finalized | Nhận block đã chốt cùng bằng chứng | Tự kiểm chứng, không append mù |
| GET /metrics | Xuất thống kê phục vụ thí nghiệm | Không tham gia quyết định đồng thuận |

Fault injection được điều khiển bằng script/config test riêng, mặc định tắt. Không để nút sửa sổ cái hoặc bỏ qua chữ ký trong API thông thường. Có thể bổ sung event endpoint khi polling không đủ.

### 11.2 Bố cục module

| Thư mục | Nội dung | Chủ trì |
|---|---|---|
| src/core/ | transaction, block, state, validation, serialization, crypto wrappers | Thành viên 1 |
| src/consensus/ | state machine, vote rules, certificates, lock rules, timeout policy | Thành viên 2 |
| src/network/ | transport, peer client, retry, buffer, sync | Thành viên 3 |
| src/storage/ | SQLite repositories, transaction commit, recovery | Thành viên 3 phối hợp 1 và 2 |
| src/api/ | Routes và wire schemas | Thành viên 3; từng chủ module review schema |
| frontend/ | Dashboard, explorer, gửi giao dịch đã ký qua ví demo | Thành viên 4 |
| tests/ | unit, consensus simulation, integration, fault scenarios | Mỗi người viết test phần mình; thành viên 4 điều phối |
| scripts/ | Generate genesis/keys, start/stop, workload, fault injection | Thành viên 3 và 4 |
| config/ | Mẫu config và genesis public | Thành viên 1 và 3 |
| docs/ | Đặc tả, thiết kế, báo cáo, hướng dẫn demo | Cả 4 người |
| experiments/ | Kịch bản, CSV, biểu đồ, mô tả môi trường | Thành viên 4 và 2 |

Các hàm cốt lõi nên thống nhất sớm: canonical_bytes, hash_transaction, verify_transaction, execute_block, validate_block, verify_vote, build_certificate, apply_committed_block, get_own_signed_vote, sync_to_height. Hàm execute_block nhận trạng thái và danh sách giao dịch, trả trạng thái mới hoặc lỗi; không tự gọi API hay đọc giờ hệ thống.

## 12. Phân công đầy đủ cho 4 thành viên

Thay Thành viên 1–4 bằng tên thật sau khi nhóm họp. Có thể hoán đổi theo năng lực, nhưng giữ người chịu trách nhiệm cuối cùng cho mỗi module.

### 12.1 Thành viên 1 phụ trách lõi blockchain và nghiệp vụ

**Nhiệm vụ lập trình**

- Đặc tả Transaction, Block, Genesis và quy tắc serialization.
- Wrapper SHA-256, ký và kiểm chứng Ed25519; test vector chung.
- Quy tắc số dư, nonce, chống phát lại, địa chỉ và conservation of supply.
- Mempool tối thiểu và bộ chọn giao dịch phối hợp với leader.
- Thực thi thử block, tính tx_list_hash/state_hash, kiểm tra chuỗi.
- Phối hợp thành viên 3 để commit state nguyên tử và replay dữ liệu.

**Bàn giao:** src/core, test vector, unit tests nghiệp vụ, genesis mẫu, ví CLI demo, chương cấu trúc blockchain và giao dịch, phần demo chuyển coin/sửa dữ liệu.

**Nghiệm thu:** sửa amount làm chữ ký/hash không hợp lệ; nonce cũ bị chặn; hai giao dịch chi vượt số dư không cùng được áp dụng; replay cùng chuỗi tạo cùng state hash; không đổi số dư trước commit.

**Người review:** thành viên 2 review phần hash ảnh hưởng consensus; thành viên 3 review phần persistence interface.

### 12.2 Thành viên 2 phụ trách đồng thuận

**Nhiệm vụ lập trình**

- Viết đặc tả protocol, state machine và các bất biến.
- Cài PROPOSE/PREPARE/COMMIT; ngưỡng 3, phân biệt phase/height/chain.
- Certificate builder/verifier, chống duplicate và phát hiện equivocation.
- Quy tắc lock bền vững và hành vi retry không ký lại giá trị khác.
- Simulation transport để thử thông điệp trễ, lặp và đảo thứ tự trước khi chạy mạng thật.
- Log timeline, tính số thông điệp, phối hợp phân tích thí nghiệm.

**Bàn giao:** src/consensus, protocol.md, consensus tests, sơ đồ trạng thái, giải thích quorum và giới hạn liveness, chương đồng thuận, phần demo vote/quorum/leader lỗi.

**Nghiệm thu:** 2 phiếu không chốt; 3 phiếu đúng chốt; 100 bản sao của một phiếu không đủ quorum; hai đề xuất cạnh tranh không tạo hai block chốt trên node trung thực; restart không xóa lock.

**Người review:** thành viên 1 review validity; thành viên 3 review lưu lock trước khi gửi.

### 12.3 Thành viên 3 phụ trách mạng và lưu trữ phân tán

**Nhiệm vụ lập trình**

- Khởi động node theo config, public key registry và peer list.
- API giữa peer, HTTPX transport, timeout, retry và idempotency.
- SQLite mỗi node; transaction commit block/state; own vote persistence.
- Sync qua block/certificate; restart và phát lại thông điệp đã lưu.
- Script PowerShell chạy/dừng đúng 4 tiến trình; Docker Compose nếu cần.
- Fault injection ở tầng transport: drop, delay, duplicate, partition.

**Bàn giao:** src/network, src/storage, src/api, config, script chạy, integration tests mạng và recovery, chương triển khai, hướng dẫn cài trên máy mới, phần demo dừng/khôi phục node.

**Nghiệm thu:** một lệnh khởi động được 4 node; database/keys tách biệt; mất follower không làm leader crash; follower quay lại tải đủ block; retry không làm áp dụng lại giao dịch; không giữ DB transaction khi đang đợi HTTP.

**Người review:** thành viên 2 review thứ tự ghi-vote; thành viên 1 review atomic state update.

### 12.4 Thành viên 4 phụ trách giao diện và đánh giá thực nghiệm

**Nhiệm vụ lập trình**

- Dashboard bốn node: online, sync state, height, tip hash và phase.
- Màn giao dịch, account, block explorer, chi tiết certificate.
- Timeline vote với sender/phase/hash để nhìn thấy cơ chế thật.
- Viết workload generator và trình chạy kịch bản tích hợp phối hợp thành viên 3.
- Thu CSV, tính latency/TPS, vẽ biểu đồ bằng công cụ plotting thông thường.
- Tổ chức test matrix, regression, đóng gói README và tài liệu demo; tổng hợp báo cáo và slide.

**Bàn giao:** frontend, workload runner, kết quả thí nghiệm có metadata, biểu đồ, test report, slide và video demo dự phòng, chương thực nghiệm và đánh giá.

**Nghiệm thu:** UI đọc trạng thái thật từ các node; phân biệt accepted/committed/stalled; xem được 3 chữ ký tạo certificate; chạy lại cùng kịch bản tạo được dữ liệu thô để đối chiếu; giao diện không tham gia chốt block.

**Người review:** thành viên 3 review API; thành viên 2 review cách hiển thị consensus và kết luận thí nghiệm.

### 12.5 Cân bằng khối lượng dự kiến

| Thành viên | Thiết kế và đọc tài liệu | Cài đặt | Kiểm thử và tích hợp | Báo cáo và demo | Tổng |
|---|---:|---:|---:|---:|---:|
| 1 | 10h | 25h | 15h | 10h | 60h |
| 2 | 14h | 23h | 15h | 8h | 60h |
| 3 | 10h | 26h | 16h | 8h | 60h |
| 4 | 8h | 24h | 18h | 10h | 60h |

Đây là ước lượng ban đầu. Sau tuần 2 cập nhật theo việc thật; không biến thành thước đo đóng góp duy nhất. Người hoàn thành sớm hỗ trợ test và review module có rủi ro cao. Mỗi người viết chương báo cáo phần mình; người 4 tổng hợp định dạng, không phải làm toàn bộ tài liệu thay nhóm.

## 13. Lịch thực hiện 6 tuần

### 13.1 Mốc chung

| Tuần | Mục tiêu | Sản phẩm phải chạy hoặc review được | Cổng nghiệm thu |
|---|---|---|---|
| 1 | Chốt phạm vi và hợp đồng | Đặc tả, schema, test vector mẫu, skeleton 4 node | Cả nhóm giải thích cùng một quy tắc; 4 /health phản hồi |
| 2 | Lõi hợp lệ và giao tiếp tối thiểu | Một node kiểm tra giao dịch/block; các node trao đổi proposal giả lập | Không dùng UI để thay thế logic; test core và wire schema đạt |
| 3 | Đồng thuận hoàn chỉnh ở trường hợp bình thường | Gửi giao dịch → 3/4 COMMIT → 4 sổ cái cùng kết quả | Kiểm certificate và chuỗi hash trên 4 tiến trình |
| 4 | Lỗi, persistence và sync | Duplicate, forged vote, follower down, restart, partition | Không fork hoặc double apply trong test matrix bắt buộc |
| 5 | Hoàn thiện quan sát và đo lường | Dashboard ổn định, workload runner, CSV, biểu đồ | Kết quả đo có seed/config/commit ID; test trọng yếu không còn lỗi |
| 6 | Đóng băng tính năng và bảo vệ | Bản release, README, báo cáo, slide, video | Máy khác cài chạy được; 2 lần tổng duyệt đạt |

### 13.2 Công việc cụ thể theo người và tuần

| Tuần | Thành viên 1 | Thành viên 2 | Thành viên 3 | Thành viên 4 |
|---|---|---|---|---|
| 1 | Data model, genesis, canonical bytes | Fault model, quorum, protocol và invariants | Config, API skeleton, tách 4 DB | Wireframe, test matrix, khung báo cáo |
| 2 | Ký tx, balance/nonce, execute/validate block | State machine trong simulation, duplicate tests | Peer transport, SQLite repos, integration skeleton | Dashboard mock theo schema, ví demo kết nối CLI/API |
| 3 | Kết nối mempool/proposer và state update | Kết nối 3 phase, tạo/kiểm certificate | Chạy 4 tiến trình, route message, commit transaction | Explorer và timeline dữ liệu thật, smoke test end-to-end |
| 4 | Double spend, replay, tamper và state recovery tests | Equivocation, split vote, restart lock, quorum tests | Sync, fault injection, crash/restart tests | Điều phối regression, UI pending/stalled, workload runner |
| 5 | Rà lại core, hỗ trợ benchmark, viết chương core | Phân tích consensus, giới hạn và số thông điệp | Kiểm triển khai máy khác, script ổn định | Chạy thí nghiệm, CSV, biểu đồ, chương đánh giá |
| 6 | Sửa lỗi cuối, review báo cáo và luyện vấn đáp | Review claim lý thuyết, chứng minh quorum | Release, README, backup demo | Tổng hợp báo cáo/slide/video, chạy nghiệm thu |

### 13.3 Mốc kiểm tra trong tuần

Đầu tuần chọn đầu việc và acceptance criteria; giữa tuần demo nhỏ bằng CLI/API hoặc test; cuối tuần merge và demo bản chung. Họp khoảng 20–30 phút, hai lần/tuần; cập nhật ngắn khi có blocker. Lỗi API/schema ảnh hưởng người khác phải thông báo ngay, không chờ cuối tuần.

**Đường găng:** schema và genesis → core validation → consensus simulation → mạng thật và durable votes → fault tests → thực nghiệm và báo cáo. Frontend và khung báo cáo làm song song với lõi; không đợi giao diện xong mới kiểm thuật toán.

Nếu hết tuần 3 chưa chốt được block trên 4 tiến trình, ngừng các tính năng đẹp, Merkle tree và Docker; cả nhóm ưu tiên đường đi từ giao dịch tới commit trước.

## 14. Quy trình làm hiệu quả

### 14.1 Làm một đường đi hoàn chỉnh nhỏ trước

Trong nửa đầu dự án, mục tiêu là một giao dịch thật đi qua đủ 4 node và tạo ra cùng block/state hash. Sau đó mới mở rộng số giao dịch, UI và số kịch bản. Cách này phát hiện sớm sự không tương thích giữa module.

Tách thuật toán khỏi HTTP và database qua interface. Consensus simulation có thể dùng transport giả; khi logic đúng mới thay bằng transport HTTP. Các hàm hash, verify và execute nên thuần để kiểm thử dễ.

### 14.2 Quản lý Git và review

- Dùng một repository và một cấu trúc module thống nhất.
- main luôn chạy được; nhánh tính năng ngắn như feat/core-validation, feat/prepare-commit, feat/node-sync, feat/dashboard.
- Mỗi pull request nêu: hành vi thay đổi, test đã chạy, ảnh hưởng schema và giới hạn nếu có.
- Tối thiểu một người review; phần quorum, signature, locks và commit transaction cần người có module liên quan kiểm tra.
- Không commit private key dùng ngoài demo, database chạy thật, node_modules hoặc môi trường ảo. Khóa demo tạo bằng script; nếu có fixture key thì ghi rõ chỉ để test.
- Chạy formatting/lint đã thống nhất và test phù hợp trên mỗi PR; full integration suite trước khi merge thay đổi consensus/storage.
- Tag các mốc như v0.1-core, v0.2-consensus, v0.3-fault-tests, v1.0-demo.

### 14.3 Definition of Done cho mỗi đầu việc

Mã chạy được với config chung; có test chứng minh tiêu chí chính; không phá test đã có; log đủ truy nguyên; schema/docs được cập nhật; được review; đã tích hợp và demo trong bản nhóm. Việc chỉ chạy trong máy cá nhân chưa được coi là hoàn tất.

### 14.4 Dùng AI hỗ trợ đúng chỗ

Dùng AI giải thích paper, gợi ý test, rà schema và viết phần mã lặp. Mỗi thay đổi giao thức phải được nhóm kiểm lại bằng quy tắc và tình huống phản ví dụ. Yêu cầu AI sửa một module nhỏ với acceptance criteria, sau đó chạy test. Không giao một prompt tạo toàn bộ blockchain rồi chấp nhận mọi khẳng định BFT. Thành viên phải tự giải thích được mã do mình nhận trách nhiệm.

## 15. Kế hoạch kiểm thử

### 15.1 Các lớp kiểm thử

1. Unit: canonical bytes, hash, chữ ký, nonce, số dư, block validation, certificate verification.
2. Simulation: nhiều node trong bộ giả lập thông điệp để điều khiển trễ, lặp, thiếu và đảo thứ tự.
3. Integration: 4 tiến trình thật, HTTP thật, DB riêng; kiểm tra trạng thái sau commit.
4. Fault/recovery: dừng đúng tiến trình, partition ở transport, restart giữa các điểm ghi, khôi phục follower.
5. Acceptance: người khác theo README từ checkout sạch và chạy được demo.

### 15.2 Ma trận test bắt buộc

| ID | Tình huống | Kết quả mong đợi | Chủ trì |
|---|---|---|---|
| T01 | Cùng dữ liệu, thứ tự key đầu vào khác | Cùng canonical bytes và hash | 1 |
| T02 | Sửa amount sau khi ký | Signature verification thất bại | 1 |
| T03 | Amount âm, 0, float, bool hoặc quá giới hạn | Không vào block hợp lệ | 1 |
| T04 | Giao dịch sai chain ID | Bị từ chối | 1 |
| T05 | Gửi lại tx đã chốt | Không trừ số dư lần hai | 1 và 3 |
| T06 | Sai nonce hoặc thiếu số dư | Không được áp dụng | 1 |
| T07 | Hai giao dịch cộng lại vượt số dư | Không thể cùng được thực thi hợp lệ | 1 |
| T08 | Sai prev_hash hoặc height | Không PREPARE | 1 và 2 |
| T09 | Leader khai state_hash sai | Node tự tính và từ chối | 1 |
| T10 | Chỉ có 2 PREPARE hoặc 2 COMMIT | Không chốt | 2 |
| T11 | 3 COMMIT đúng cùng block | Có certificate; chốt tối đa một lần | 2 và 3 |
| T12 | Một sender phát lặp 100 lần | Chỉ tính một danh tính | 2 |
| T13 | Sender giả hoặc signature sai | Không tăng quorum | 2 |
| T14 | Dùng PREPARE làm COMMIT; trộn height/chain | Không được dùng cho certificate | 2 |
| T15 | Phiếu tới trễ hoặc đảo thứ tự | Buffer/đòi dữ liệu đúng, không chốt sai | 2 và 3 |
| T16 | Leader ký hai proposal cạnh tranh | Không có hai block chốt xung đột ở honest nodes; có thể stall | 2 |
| T17 | Một Byzantine follower double-sign | Lưu bằng chứng; không fork với các giả định còn đúng | 2 |
| T18 | Tắt một follower | Leader và 2 honest follower còn lại tiếp tục | 3 |
| T19 | Tắt leader | Bản lõi báo chờ; không tự bầu mới hoặc hạ ngưỡng | 2 và 3 |
| T20 | Partition 2–2 | Không nhóm nào commit height mới | 3 |
| T21 | Partition 3–1 có leader trong nhóm 3 | Nhóm 3 có thể chốt; node lẻ đồng bộ sau nối lại | 3 |
| T22 | Restart sau khi lưu PREPARE/COMMIT nhưng chưa hoàn tất | Không ký hash khác; có thể gửi lại phiếu cũ | 2 và 3 |
| T23 | Crash trước/trong/sau transaction áp dụng block | Không mất nửa cập nhật hoặc double apply | 1 và 3 |
| T24 | Follower bỏ lỡ nhiều block rồi quay lại | Tải, xác minh và đạt cùng state hash | 3 |
| T25 | Peer đưa chuỗi dài nhưng certificate giả | Không chấp nhận vì chiều dài | 3 |
| T26 | Sửa DB/body local hoặc block tải về | Phát hiện kiểm tra thất bại; node không tiếp tục vote mù | 1 và 3 |
| T27 | 4 node hoàn thành cùng workload | Cùng hash tại từng height chung, cùng balances/nonces | 4 |
| T28 | Dashboard thấy API nhận giao dịch nhưng chưa commit | Hiển thị pending, không báo thành công cuối cùng | 4 |
| T29 | Hai request đồng thời cố tạo own vote khác nhau | Storage/state machine giữ một lock và một own vote nhất quán | 2 và 3 |
| T30 | Gửi payload quá lớn hoặc future height quá xa | Từ chối/giới hạn buffer, không chiếm bộ nhớ vô hạn | 3 |

Mỗi test hệ thống cần ghi seed, trạng thái ban đầu, sự kiện lỗi, hash theo từng node và log/certificate. Test asynchronous chờ điều kiện có deadline thay vì sleep một con số tùy ý. Không chữa lỗi safety bằng cách cho test chạy lại nhiều lần đến khi tình cờ pass.

## 16. Thiết kế thực nghiệm và chỉ số đánh giá

### 16.1 Chỉ số

| Chỉ số | Cách đo | Ý nghĩa và giới hạn |
|---|---|---|
| Submitted | Số yêu cầu giao dịch gửi | Có thể gồm giao dịch sai hoặc request lặp |
| Admitted | Số tx_id hợp lệ được tiếp nhận | Chưa phản ánh giao dịch đã chốt |
| Committed unique | Số tx_id khác nhau nằm trong block đã chốt | Tránh đếm một tx trên 4 node thành 4 tx |
| Committed throughput | Unique committed tx trong cửa sổ đo / thời lượng giây | Nêu rõ offered load và thời gian drain |
| End-to-end latency | Thời điểm client thấy certificate − thời điểm gửi đầu tiên | Đo bằng đồng hồ monotonic của cùng client |
| Consensus latency | Thời điểm quan sát certificate − thời điểm proposal | Định nghĩa observer cố định; tránh trừ giờ hai máy chưa đồng bộ |
| p50, p95 latency | Phân vị từ mẫu đã commit | Báo cả số pending/timeout để tránh thiên lệch chỉ nhìn tx thành công |
| Commit ratio | Tx hợp lệ duy nhất đã commit / tx hợp lệ duy nhất đã gửi | Nêu cửa sổ chờ và tx chưa hoàn tất |
| Fork violations | Số cặp honest node có hash khác nhau ở cùng height đã chốt | Trong test thuộc mô hình, mục tiêu bằng 0 |
| State divergence | Số height chung có state_hash khác giữa honest nodes | Bắt lỗi thực thi và persistence |
| Message count/bytes | Lượng gửi giữa peer theo phase, có tách retry | Đánh giá overhead consensus |
| Catch-up time | Từ khi follower nối lại đến khi theo kịp mốc height định sẵn | Mốc cố định để tránh đuổi một tip tăng mãi |
| CPU/RAM tùy chọn | Theo từng tiến trình cùng thời điểm workload | Hữu ích khi chạy một laptop; không thay cho chỉ số correctness |

Không hứa trước số TPS cụ thể. Ngưỡng latency cho demo chỉ chốt sau khi đo trên máy nhóm. Zero safety violations trong test là điều kiện nghiệm thu; không kết luận từ đó rằng mọi lỗi Byzantine trong mọi lịch mạng đã được chứng minh xử lý.

### 16.2 Các thí nghiệm nên làm

| Nhóm thí nghiệm | Cấu hình | Câu hỏi cần trả lời |
|---|---|---|
| E1 Bình thường | 4 node, batch 1/10/50, block timeout cố định | Gom nhiều tx ảnh hưởng latency và throughput ra sao? |
| E2 Trễ mạng | Batch 10, delay 0/100/300 ms ở transport với seed | Độ trễ ảnh hưởng các pha vote và retry thế nào? |
| E3 Follower lỗi | 4 node so với 1 follower offline | Với leader còn tốt, 3 node có thể commit và đồng bộ lại không? |
| E4 Partition | 2–2 và 3–1 có leader ở nhóm 3 | Quorum cố định bảo vệ safety bằng cách nào? |
| E5 Hành vi sai | 1 follower gửi sai chữ ký, lặp hoặc double-sign | Sai lệch bị loại và ghi bằng chứng ra sao? |
| E6 Baseline tùy chọn | Một writer nhận cùng nghiệp vụ, bỏ voting | Overhead thêm bởi replication/consensus là bao nhiêu? |

Baseline một writer không có mức chịu lỗi tương đương; chỉ dùng so chi phí, không kết luận nó tốt hơn hoặc kém hơn về tổng thể. Không cần cài PoW hoặc một thuật toán đồng thuận thứ hai chỉ để có biểu đồ so sánh.

### 16.3 Quy trình đo có thể chạy lại

1. Lưu mã phiên bản, cấu hình, môi trường CPU/RAM/OS, cách chạy local/LAN, phiên bản thư viện và seed.
2. Tạo genesis cho một lần chạy độc lập; dùng tài khoản thử và số dư đủ. Tách run_id và chain_id giữa các thí nghiệm reset trạng thái.
3. Warm-up trước cửa sổ đo; dùng workload có cùng cách phân phối sender/recipient và cùng số tx hợp lệ.
4. Khởi đầu 500 giao dịch/lần với offered load phù hợp như 10 tx/s; đây là tham số thử, điều chỉnh sau pilot. Dùng nhiều sender và mỗi sender chỉ có một tx outstanding nếu MVP áp dụng giới hạn đó.
5. Với workload tương đương, mỗi cấu hình đo ít nhất 3 lần; báo median hoặc mean và độ phân tán, không chọn lần đẹp nhất.
6. Định nghĩa cửa sổ đo và thời gian drain trước khi chạy; tách tx pending, rejected và timed out. Trong partition, việc không commit là kết quả cần báo.
7. Xuất CSV cấp giao dịch và CSV cấp lần chạy; log thời điểm fault injection.
8. Sau mỗi lần, kiểm tra toàn chuỗi và trạng thái ở honest nodes rồi mới dùng số hiệu năng.
9. Vẽ throughput/latency theo batch, latency theo delay, timeline số node hoạt động/quorum và bảng correctness từng fault case.

Quy mô hợp lý là khoảng 8–10 cấu hình chính, mỗi cấu hình 3 lần; không bắt buộc chạy tích Descartes của mọi tham số. Nếu thay tham số sau pilot, ghi rõ và giữ bộ cấu hình chính nhất quán.

## 17. Thiết kế dashboard phục vụ giải thích

Màn tổng quan có 4 thẻ node, thể hiện node_id, kết nối, sync state, committed height, tip hash và vai trò. Màu xanh chỉ nói node đang phản hồi; không được suy ra node trung thực hoặc đủ quorum.

Màn đồng thuận ở một height cần có block hash, proposer, PREPARE theo sender, COMMIT theo sender, quorum mục tiêu 3, certificate và timeline. Mỗi hàng phiếu hiển thị valid/invalid/duplicate kèm lý do. Có thể rút gọn hash trên thẻ nhưng cho sao chép/xem đầy đủ.

Màn giao dịch phân biệt pending, proposed, committed, rejected và local-unknown. Khi node chưa biết một giao dịch, đừng tự kết luận giao dịch đã bị cả mạng từ chối. Nếu lỗi quorum kéo dài, hiển thị đang chờ thay vì báo đã chốt.

Màn explorer cho xem header, tx list, prev_hash, state_hash và danh tính các validator trong commit certificate. Ví demo ký tại CLI hoặc một thành phần tách biệt; dashboard không chứa khóa validator để làm đẹp thao tác.

MVP dùng polling khoảng 1 giây là đủ cho demo. Khi đo latency, dùng workload runner và đồng hồ đo riêng, không lấy tốc độ refresh UI làm hiệu năng consensus.

## 18. Mở rộng đổi leader an toàn

Nếu có thêm 2 tuần hoặc yêu cầu môn học bắt buộc, nhóm chọn một đặc tả PBFT hoặc Tendermint/CometBFT nhất quán và học trọn quy tắc. Không ghép tùy ý tên phase PBFT với quy tắc unlock của thuật toán khác. Đọc [R3, R15, R16].

Các nội dung cần bổ sung gồm:

- View hoặc round tăng đơn điệu, leader mới được xác định rõ.
- Timeout tạo yêu cầu đổi view thay vì tự đổi theo nhận định của một node.
- VIEW-CHANGE chứa bằng chứng prepared/locked cần thiết theo giao thức đã chọn.
- NEW-VIEW hoặc đề xuất round mới có chứng cứ đủ quorum và quy tắc chọn lại giá trị an toàn.
- Node xác minh chứng cứ trước khi chấp nhận view mới, giữ lại những giá trị cần bảo toàn.
- Persistence của view, locks và phiếu; chống replay thông điệp view cũ.
- Retransmission, catch-up và state transfer không phá ràng buộc đã ký.
- Test leader chết ở từng pha, leader mới Byzantine, nhiều timeout liên tiếp và partition rồi nối lại.

**Tuần 7:** chốt giao thức chuẩn, đặc tả chuyển view và làm simulation; người 2 chủ trì, người 1 review chứng cứ/giá trị, người 3 triển khai persistence/transport, người 4 mở rộng test.

**Tuần 8:** tích hợp trên 4 tiến trình, kiểm thử đối kháng và chạy lại thí nghiệm; cập nhật dashboard, tài liệu và claim về liveness sau khi kiểm chứng.

Không chỉ thêm `leader = next_node` khi timeout. Với bản lõi khóa cứng theo height, quy tắc chuyển view cần được thiết kế lại có chứng cứ; tự xóa khóa làm mất cơ sở an toàn. Nếu không đủ thời gian kiểm tra phần nâng cao, trình bày giới hạn bản lõi và hướng phát triển trung thực.

## 19. Rủi ro và cách xử lý

| Rủi ro | Dấu hiệu | Cách xử lý |
|---|---|---|
| Nhầm voting ứng dụng với consensus | Chỉ có form bầu chọn và một server ghi | Quay lại luồng validator ký proposal/prepare/commit |
| Mỗi module hiểu hash khác nhau | Cùng giao dịch sinh tx_id khác | Một canonical serializer và test vector chung |
| Leader giữ mọi private key | Leader có thể tự tạo đủ chữ ký | Mỗi tiến trình chỉ nạp khóa riêng; registry chỉ giữ public keys |
| Đếm request thay vì danh tính | Spam request làm đạt quorum | Unique key theo sender/phase/context, kiểm chữ ký |
| Hạ quorum khi node mất | 2 node vẫn chốt | Quorum cố định trong genesis; test partition bắt buộc |
| Quên vote sau restart | Ký lại block khác cùng height | Durable lock/own vote trước network send |
| HTTP callback race | Hai own votes khác hash | Hàng đợi consensus hoặc serialization + ràng buộc DB |
| Mọi thứ nằm trong RAM | Restart mất chain/state | SQLite riêng, transaction và recovery tests |
| Chỉ làm UI đến cuối mới tích hợp | Tuần 3 chưa commit được block thật | Cắt tính năng phụ, làm đường đi hoàn chỉnh |
| Thử nghiệm chậm hoặc sai số đo | TPS đếm 4 bản sao, bỏ tx timeout | Dedupe tx_id, định nghĩa cửa sổ và observer |
| Máy demo không có mạng Internet | Cài phụ thuộc hoặc CDN không chạy | Chuẩn bị build local, lockfile, video và gói cài hướng dẫn |
| Ôm PBFT đầy đủ quá sớm | View change chiếm toàn bộ thời gian | Đóng băng bản lõi trước; tách 2 tuần nâng cao |

## 20. Báo cáo và sản phẩm bàn giao

### 20.1 Nội dung báo cáo đề xuất

| Chương | Nội dung cần viết | Chủ trì |
|---|---|---|
| 1 Giới thiệu | Bài toán, mục tiêu, phạm vi, phương pháp, phân công | Cả nhóm; 4 tổng hợp |
| 2 Cơ sở lý thuyết | Blockchain, DLT, hash, ký số, replicated state machine, Byzantine, quorum; so sánh Raft/PBFT vừa đủ | 1 và 2 |
| 3 Phân tích và thiết kế | Yêu cầu, mô hình lỗi, kiến trúc, dữ liệu, API, state machine và persistence | 1, 2, 3 |
| 4 Cài đặt | Cấu trúc module, điểm khó, luồng tx → commit, sync/recovery, dashboard | Mỗi người phần mình |
| 5 Kiểm thử và thực nghiệm | Test matrix, workload, môi trường, số liệu, biểu đồ, giới hạn kết quả | 4 cùng 2 và 3 |
| 6 Kết luận | Mục tiêu đạt, giới hạn bản lõi, bài học, hướng mở rộng view change | Cả nhóm |
| Phụ lục | Hướng dẫn chạy, config, API, test vector, bảng đóng góp, link repository | 3 và 4 |

Độ dài tham khảo: khoảng 25–40 trang nội dung chính nếu giảng viên không có mẫu khác. Ưu tiên giải thích thiết kế và bằng chứng thay vì chép nhiều trang source code. Dùng sơ đồ kiến trúc, luồng consensus, trạng thái node, bảng dữ liệu và biểu đồ có đơn vị rõ.

### 20.2 Bộ bàn giao cuối cùng

1. Repository có tag release và lịch sử đóng góp.
2. README cài đặt, sinh genesis/keys, chạy 4 node, test, demo và dừng ứng dụng.
3. Protocol specification ghi rõ các pha, quorum, lock và giới hạn.
4. Source node, frontend và scripts; config mẫu không chứa bí mật ngoài demo.
5. Test suite và test report có kết quả, log và bằng chứng certificate.
6. Dữ liệu thí nghiệm thô, cấu hình, seed, script tạo biểu đồ và hình đã xuất.
7. Báo cáo, slide, video demo ngắn và kịch bản dự phòng.
8. Bảng phân công và đóng góp thực tế theo module/PR/test/tài liệu.

## 21. Kịch bản demo khoảng 10 phút

| Thời gian | Nội dung | Người trình bày | Bằng chứng cần hiện |
|---|---|---|---|
| 0:00–1:00 | Kiến trúc 4 node và ngưỡng 3 | 1 | Node IDs, genesis hash, DB tách biệt |
| 1:00–3:00 | Gửi giao dịch hợp lệ và theo dõi vote | 2 | PROPOSE/PREPARE/COMMIT, 3 chữ ký, cùng tip hash |
| 3:00–4:00 | Giao dịch sai chữ ký, replay hoặc thiếu tiền | 1 | Mã lỗi, số dư không đổi |
| 4:00–5:30 | Dừng follower rồi tiếp tục commit | 3 | 3 node còn lại chốt, quorum vẫn là 3 |
| 5:30–6:30 | Khởi động follower và catch-up | 3 | Tải block, certificate hợp lệ, state hash bằng nhau |
| 6:30–8:00 | Partition 2–2 hoặc chỉ còn 2 validator | 2 và 4 | Không commit height mới; UI đang chờ |
| 8:00–9:00 | Phiếu lặp/giả và giới hạn khi leader lỗi | 2 | Phiếu bị loại; timeout không tạo commit giả |
| 9:00–10:00 | Thí nghiệm, kết quả và hạn chế | 4 | CSV/biểu đồ, zero violation trong test, claim liveness đúng phạm vi |

Các tình huống cố ý làm bản lõi kẹt được chạy cuối hoặc trong mạng thí nghiệm riêng. Không xóa lock để cứu demo trên cùng chain. Chuẩn bị video của bản release và log/certificate thật làm dự phòng; nói rõ nếu đang phát video.

## 22. Câu hỏi bảo vệ nên luyện

| Câu hỏi | Ý chính cần trả lời |
|---|---|
| Blockchain khác danh sách block lưu JSON ở đâu? | Có kiểm chứng giao dịch, chữ ký, liên kết hash, nhiều bản sao độc lập và quy tắc đồng thuận |
| Vì sao băm lại cả chuỗi vẫn chưa đủ? | Người sửa có thể tính hash mới; honest node còn kiểm certificate từ validator và trạng thái tin cậy |
| Tại sao 3/4? | Hai quorum 3 giao nhau ít nhất 2; với tối đa 1 Byzantine còn honest node không ký xung đột |
| Chữ ký chứng minh điều gì? | Chủ khóa ký đúng thông điệp; không tự chứng minh nội dung nghiệp vụ hợp lệ |
| Leader có quyền tự quyết không? | Chỉ đề xuất; node tự kiểm block và cần quorum ký |
| PREPARE khác COMMIT thế nào? | PREPARE thể hiện chấp nhận giá trị; COMMIT được honest node phát sau prepared certificate; finality yêu cầu commit certificate |
| Có phải PBFT đầy đủ không? | Bản lõi là giao thức giáo dục lấy cảm hứng PBFT; không có đầy đủ view change/checkpoint/recovery của PBFT chuẩn |
| Một node hỏng thì có chạy không? | Follower hỏng, leader tốt và đủ liên lạc thì có thể; leader hỏng bản lõi có thể dừng |
| Vì sao restart phải nhớ vote? | Quên vote sẽ cho một honest process ký hai giá trị qua hai lần chạy, phá giả định quorum |
| Đồng bộ chọn chuỗi nào? | Từ genesis tin cậy, kiểm từng block/certificate và replay; không chỉ chọn dài nhất |
| 4 node một máy có phân tán không? | Mô phỏng các node độc lập ở tầng tiến trình; vẫn chung miền lỗi vật lý của laptop |
| Test pass có chứng minh an toàn tuyệt đối? | Không; chỉ chứng minh các kịch bản đã chạy, kèm lập luận và giả định rõ ràng |

## 23. Checklist nghiệm thu cuối

- [ ] 4 tiến trình thật, mỗi tiến trình một cấu hình, khóa và database.
- [ ] Mọi node cùng genesis và public key registry.
- [ ] Giao dịch có chữ ký, chain ID, amount nguyên và nonce.
- [ ] Các node tự thực thi và kiểm block trước khi ký.
- [ ] 3 chữ ký COMMIT hợp lệ mới tạo finality.
- [ ] Duplicate, forged sender, wrong phase/height/chain không tăng quorum.
- [ ] own votes và locks được ghi bền vững trước khi phát.
- [ ] Block/state/certificate được commit nguyên tử và idempotent.
- [ ] Partition 2–2 không tạo block mới; không hạ quorum.
- [ ] Không có fork/state divergence trong các test thuộc mô hình.
- [ ] Restart và catch-up hoạt động mà không xóa lịch sử ký.
- [ ] Dashboard phản ánh dữ liệu thật và phân biệt accepted với committed.
- [ ] Báo cáo mô tả chính xác giới hạn leader và view change.
- [ ] Kết quả đo có cấu hình, seed, commit ID và dữ liệu thô.
- [ ] Người khác cài chạy theo README được.
- [ ] Cả 4 thành viên giải thích được luồng tx → consensus → ledger.

## 24. Nếu thời gian thực tế ngắn hơn

| Quỹ thời gian | Phạm vi nên giữ | Cách giảm phạm vi |
|---|---|---|
| 2–3 tuần | 4 node, tx ký, block hợp lệ, quorum 3, lock bền vững, test chính | CLI hoặc UI tối giản; không benchmark nhiều cấu hình, không Merkle, không đổi leader |
| 4 tuần | Bản lõi, persistence, sync, 4–6 fault cases, dashboard đơn giản | Giảm trang UI và số biểu đồ, làm báo cáo song song |
| 6 tuần | Toàn bộ bản lõi trong kế hoạch này | Mốc đề xuất chính |
| 8 tuần trở lên | Bản lõi ổn định rồi view change có đặc tả và test | Chỉ nâng claim liveness sau khi hoàn thành phần này |

Không giảm kiểm tra chữ ký, quorum, chống duplicate, durable lock hoặc test safety để đổi lấy giao diện đẹp. Nếu giảng viên bắt buộc một nội dung, ưu tiên rubric trước các đề xuất tùy chọn ở đây.

## 25. Những việc làm ngay trong buổi đầu

1. Ghi nhận rubric, deadline và yêu cầu tự cài thuật toán từ giảng viên; xác định voting là xác nhận block.
2. Gán tên thật vào 4 vai trò, chọn một người điều phối mốc nhưng không dồn code cho người đó.
3. Chốt stack và cài cùng phiên bản; thống nhất quy tắc chạy trên Windows.
4. Chốt phạm vi leader cố định của bản lõi, ngưỡng 3 và mô hình tối đa 1 Byzantine.
5. Tạo repository, nhánh main, khung module và issue cho các đầu việc tuần 1.
6. Viết schema Genesis/Transaction/Block/Vote, quy tắc canonical bytes và một test vector.
7. Tạo bốn cấu hình và bốn public key; khởi động bốn /health.
8. Chọn ngày demo đầu tiên cho một giao dịch đi đủ vòng consensus.

## 26. Tài liệu tham khảo và thứ tự đọc

Các nguồn sau là paper gốc hoặc tài liệu chính thức đã kiểm tra ngày 18/11/2026. Link tài liệu stable/main có thể tiếp tục thay đổi; khi trích báo cáo, ghi ngày truy cập và pin phiên bản/commit cụ thể nếu dùng làm cơ sở cài đặt.

| Mã | Tài liệu và liên kết | Cần đọc gì | Ai đọc trước |
|---|---|---|---|
| R1 | Satoshi Nakamoto, 2008, [Bitcoin A Peer to Peer Electronic Cash System](https://bitcoin.org/bitcoin.pdf) | Transactions, chuỗi hash, Merkle tree; phân biệt PoW của Bitcoin với voting trong đồ án | 1 và cả nhóm đọc nền tảng |
| R2 | Miguel Castro và Barbara Liskov, 1999, [Practical Byzantine Fault Tolerance](https://www.usenix.org/conference/osdi-99/practical-byzantine-fault-tolerance) | Bài toán, mô hình, ý tưởng normal case và view change | 2; cả nhóm đọc tóm tắt |
| R3 | Castro và Liskov, [The Algorithm](https://www.usenix.org/legacy/publications/library/proceedings/osdi99/full_papers/castro/castro_html/node4.html) | Các pha, prepared/committed, safety và view change | 2 và 3 |
| R4 | Castro và Liskov, [System Model](https://www.usenix.org/legacy/publications/library/proceedings/osdi99/full_papers/castro/castro_html/node2.html) và [Service Properties](https://static.usenix.org/publications/library/proceedings/osdi99/full_papers/castro/castro_html/node3.html) | Byzantine, thông điệp trễ/lặp/đảo thứ tự, giả định và n = 3f + 1 | 2 và 3 |
| R5 | Diego Ongaro và John Ousterhout, 2014, [In Search of an Understandable Consensus Algorithm](https://raft.github.io/raft.pdf) | Replicated log, mô hình lỗi dừng, bầu leader; chỉ ra khác biệt với Byzantine | 2 và 3 |
| R6 | Python, [hashlib](https://docs.python.org/3.13/library/hashlib.html) | SHA-256, bytes và digest | 1 |
| R7 | Python, [json](https://docs.python.org/3.13/library/json.html) | Serialization, sort_keys, separators, parse và giới hạn dữ liệu | 1 và 3 |
| R8 | cryptography, [Ed25519 signing](https://cryptography.io/en/stable/hazmat/primitives/asymmetric/ed25519/) | Generate, sign, verify và serialize keys | 1 và 2 |
| R9 | FastAPI, [Tutorial User Guide](https://fastapi.tiangolo.com/tutorial/) | Request body, validation, response models, errors, CORS | 3 và 4 |
| R10 | Python, [sqlite3](https://docs.python.org/3/library/sqlite3.html) | Transaction control, commit/rollback và sử dụng connection | 3 |
| R11 | FastAPI, [Testing](https://fastapi.tiangolo.com/tutorial/testing/) | TestClient và HTTPX; phân biệt test route với test nhiều node thật | 3 và 4 |
| R12 | pytest, [Documentation](https://docs.pytest.org/en/stable/contents.html) | Fixtures, parametrization, temporary paths, monkeypatch và integration practices | Cả nhóm |
| R13 | Docker, [Compose](https://docs.docker.com/compose/) | Services, network và volume; chỉ dùng khi cần đóng gói container | 3 |
| R14 | Pro Git, [Contributing to a Project](https://git-scm.com/book/en/v2/GitHub-Contributing-to-a-Project) | Nhánh tính năng, pull request, trao đổi và review | Cả nhóm |
| R15 | CometBFT, [Consensus specification](https://github.com/cometbft/cometbft/blob/main/spec/consensus/consensus.md) | Propose, prevote, precommit, round và khóa; nguồn nâng cao, không đồng nhất với PBFT | 2 nếu mở rộng |
| R16 | CometBFT, [Signing specification](https://github.com/cometbft/cometbft/blob/main/spec/consensus/signing.md) | Quy tắc ký và chống double signing | 2 và 3 nếu mở rộng |

Thứ tự học gợi ý: buổi 1 đọc R1 và cùng giải thích một giao dịch; buổi 2 đọc R2–R4 rồi mô phỏng 4 validator trên giấy; buổi 3 làm hash/signature/test vector theo R6–R8; sau đó mỗi người đọc nguồn cho module của mình. Chỉ đọc R15–R16 sau khi hiểu sự khác biệt giữa an toàn trong một view và an toàn qua nhiều view.
