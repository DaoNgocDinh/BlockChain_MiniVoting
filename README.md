# BlockChain MiniVoting

Đồ án Chuỗi khối và công nghệ sổ cái phân tán, nhóm 4 thành viên.
Xây dựng blockchain permissioned với bốn validator cố định, giao dịch chuyển coin
giả lập và giao thức ba pha PROPOSE → PREPARE → COMMIT; ngưỡng chốt là 3/4 chữ ký
COMMIT hợp lệ từ các validator khác nhau.

Đây là thiết kế lấy cảm hứng từ PBFT, không phải PBFT đầy đủ. Bản lõi có leader
cố định; leader lỗi hoặc chia phiếu có thể làm hệ thống dừng tiến triển. Voting ở
đây là xác nhận block giữa validator, không phải ứng dụng bầu cử cho người dùng.

## Trạng thái hiện tại

Bộ khung ban đầu có cấu trúc module, API `/health`, cấu hình topology bốn node,
khung React đọc health thật, kiểm tra CI và backlog cho sáu tuần. Consensus,
genesis, chữ ký, SQLite, đồng bộ và benchmark chưa được cài đặt. `/status` trả
503 `CONSENSUS_NOT_READY` để không tạo nhầm dữ liệu sổ cái.

## Cài và chạy backend trên Windows

Yêu cầu Python 3.12+ (hỗ trợ 3.12–3.14, mục tiêu CI 3.13), Git và PowerShell.
Các lệnh dưới đây chạy tại thư mục gốc repository:

```powershell
git clone https://github.com/DaoNgocDinh/BlockChain_MiniVoting.git
cd BlockChain_MiniVoting
py -3.12 -m venv .venv
# Cài đặt từ lockfile tái lập của nhóm:
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

### Chạy và quản lý 4 node

Khởi chạy cả 4 validator cùng lúc ở background và kiểm tra `/health`:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-all-nodes.ps1
```

Kiểm tra trạng thái các node (PID, tiến trình sống/chết và phản hồi HTTP):
```powershell
powershell -ExecutionPolicy Bypass -File scripts/status-nodes.ps1
```

Dừng an toàn cả 4 tiến trình (chỉ dừng tiến trình thuộc repo, không kill ngoài):
```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop-all-nodes.ps1
```

Để chạy đơn lẻ 1 node ở foreground phục vụ debug:
```powershell
powershell -NoProfile -File scripts/run-node.ps1 -NodeId node1
```
Mở http://127.0.0.1:8001/health hoặc http://127.0.0.1:8001/docs.
Đổi `-NodeId` thành node2, node3, node4 tương ứng các cổng 8002, 8003, 8004. Ctrl+C để dừng.
Mỗi node chạy cùng một bộ source, sở hữu thư mục database và khóa riêng biệt (`data/nodeX/`, `keys/nodeX.key`).

Trên Linux/macOS, tạo `.venv` bằng `python3.13 -m venv .venv`, cài requirements,
rồi chạy `NODE_ID=node1 .venv/bin/python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8001`.

## Chạy frontend

Node.js 22.12+; nhóm nên thống nhất Node.js 24 LTS.

```powershell
cd frontend
npm install
npm run dev
```

Mở URL Vite hiển thị. Dev proxy kết nối bốn API local; không cần lưu khóa validator
trên frontend. Chi tiết và phần lockfile cần chốt tại [frontend/README.md](frontend/README.md).

## Kiểm tra trước khi mở pull request

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m pytest
cd frontend
npm run lint
npm run build
```

GitHub Actions chạy cùng các kiểm tra trên push `main` và pull request.
Dependency trực tiếp được pin; TV3/TV4 chốt lockfile đầy đủ trong tuần 1, cập nhật
CI sang cài từ lockfile và ghi lại phiên bản thực tế trên máy nhóm.

## Tài liệu và công việc

- [Kế hoạch gốc](docs/ke-hoach.md): phạm vi, protocol đề xuất, 30 kịch bản test,
  phương pháp đo và tiến độ sáu tuần.
- [Phân công và review](docs/phan-cong.md).
- [Quy trình Git và Definition of Done](CONTRIBUTING.md).
- [API và schema cần thống nhất](docs/api-contract.md).
- [Backlog theo tuần](docs/backlog.md).
- [Thiết lập bảo vệ main](docs/github-setup.md).
- [Issues](https://github.com/DaoNgocDinh/BlockChain_MiniVoting/issues).

Private keys, `.env`, môi trường ảo, `node_modules`, DB và log local được bỏ qua
bởi `.gitignore`. Khóa/genesis demo sẽ được sinh bằng script; chưa có private key
hay genesis hợp lệ trong bản khung.
