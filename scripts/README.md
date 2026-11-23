# Bộ script vận hành và phát triển MiniVoting

Thư mục này chứa các script PowerShell và Python phục vụ khởi chạy, dừng an toàn, kiểm tra trạng thái và thiết lập môi trường cho 4 validator nodes.

## Danh sách scripts

| Script | Ngôn ngữ | Chức năng | Lưu ý an toàn |
|---|---|---|---|
| `scripts/run-node.ps1` | PowerShell | Khởi chạy 1 node ở foreground (`-NodeId node1..node4`) | Phù hợp debug đơn lẻ; Ctrl+C để dừng |
| `scripts/start-all-nodes.ps1` | PowerShell | Khởi chạy cùng lúc 4 node ở background, lưu PID vào `.run/nodes.json`, thăm dò `/health` | Chờ 4 node phản hồi 200 OK |
| `scripts/stop-all-nodes.ps1` | PowerShell | Dừng an toàn 4 tiến trình node theo PID | **Kiểm tra quyền sở hữu và CommandLine**, kiên quyết không kill tiến trình ngoài repo |
| `scripts/status-nodes.ps1` | PowerShell | Báo cáo trạng thái sống/chết (PID) và kết quả `/health` của 4 node | Dùng theo dõi cụm node nhanh |
| `scripts/generate-dev-keys.py` | Python | Khởi tạo 4 thư mục dữ liệu độc lập và placeholder khóa | Thư mục `data/` và `keys/` được `.gitignore` bảo vệ |
| `scripts/setup-github.ps1` | PowerShell | Thiết lập labels, milestones và protection rules trên GitHub | Dùng cho nhóm trưởng khi khởi tạo repo |

## Hướng dẫn sử dụng

### 1. Chuẩn bị môi trường và thư mục độc lập
```powershell
.\.venv\Scripts\python.exe scripts/generate-dev-keys.py
```

### 2. Khởi chạy toàn bộ 4 node
```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-all-nodes.ps1
```

### 3. Kiểm tra trạng thái cụm
```powershell
powershell -ExecutionPolicy Bypass -File scripts/status-nodes.ps1
```

### 4. Dừng an toàn toàn bộ cụm
```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop-all-nodes.ps1
```

## Nguyên tắc thiết kế (Design Guidelines)
- Không kill tiến trình chung theo tên `python`. Mọi thao tác dừng đều dựa trên PID được lưu tại `.run/nodes.json` kết hợp kiểm tra đường dẫn thực thi.
- 4 validator sở hữu 4 thư mục cơ sở dữ liệu (`data/node1/` .. `data/node4/`) và khóa riêng biệt (`keys/node1.key` .. `keys/node4.key`), tuyệt đối không chia sẻ bộ nhớ hoặc database.
