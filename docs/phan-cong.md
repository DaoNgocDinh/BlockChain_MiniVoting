# Phân công nhóm 4 người

Theo mục 12–14 của [kế hoạch](ke-hoach.md). Username đối chiếu từ issue #26:
TV1 `@CaoDucDao`, TV2 `@germnguyen`, TV3 `@pvduc05`.
Chủ repo `@DaoNgocDinh` là TV4 và nhóm trưởng.

| Vai trò | Phụ trách chính | Bàn giao | Review |
|---|---|---|---|
| TV1 | Lõi blockchain, giao dịch, hash/chữ ký, state | `src/core`, test vector, ví CLI, chương core | TV2; TV3 về persistence |
| TV2 | Đặc tả và cài đặt đồng thuận, certificate, locks | `src/consensus`, protocol, simulation, chương consensus | TV1 và TV3 |
| TV3 | Mạng, API, SQLite, recovery, triển khai | `src/network`, `src/storage`, `src/api`, config/scripts | TV1 và TV2 |
| TV4 · @DaoNgocDinh | Dashboard, điều phối test, workload và thực nghiệm | `frontend`, `experiments`, test report, tổng hợp slide/demo | TV3 về API; TV2 về consensus |

Mỗi người có sáu issue theo sáu tuần, tương ứng khoảng 60 giờ theo ước lượng gốc.
Nhóm trưởng điều phối schema, review và cổng nghiệm thu; từng người chịu trách
nhiệm cuối cùng cho module, test và tài liệu của mình.

| Mốc | Kết quả cần có |
|---|---|
| W1 | Chốt schema/protocol/API; bốn health API; wireframe/test matrix |
| W2 | Transaction/block validation, simulation, transport/storage skeleton, dashboard mock |
| W3 | Một giao dịch thật qua 3/4 COMMIT; bốn ledger giống nhau; explorer/timeline thật |
| W4 | Fault, persistent locks, crash/restart, sync, regression/workload |
| W5 | Thực nghiệm có seed/config/commit SHA, CSV, biểu đồ và chương báo cáo |
| W6 | Freeze tính năng; máy mới cài chạy; release/báo cáo/slide/video; hai lần tổng duyệt |

Chưa có ngày bắt đầu và deadline chính thức, nên milestone dùng tuần tương đối,
không tự gán ngày hết hạn. View change, Merkle proof, Docker và triển khai LAN là
phần nâng cao; không trộn vào backlog bắt buộc trước khi đạt cổng nghiệm thu lõi.
