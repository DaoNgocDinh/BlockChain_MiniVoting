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

Yêu cầu Python 3.13 (phiên bản mục tiêu của CI), Git và PowerShell. Python 3.14
được chấp nhận trong metadata, nhưng cả nhóm nên thống nhất 3.13 trước khi thêm
thư viện. Các lệnh dưới đây chạy tại thư mục gốc repository:

```powershell
git clone https://github.com/DaoNgocDinh/BlockChain_MiniVoting.git
cd BlockChain_MiniVoting
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
powershell -NoProfile -File scripts/run-node.ps1 -NodeId node1
```

Mở http://127.0.0.1:8001/health hoặc http://127.0.0.1:8001/docs.
Mở thêm ba terminal và đổi `-NodeId` thành node2, node3, node4; cổng tương ứng
8002, 8003, 8004. Ctrl+C tại từng terminal để dừng. Mỗi terminal chạy cùng một
bộ source; không sao chép thành bốn phiên bản node.

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
