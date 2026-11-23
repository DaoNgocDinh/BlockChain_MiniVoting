# Hợp đồng API · bản cần nhóm review

Chủ trì TV3; TV1/TV2 review schema nghiệp vụ; TV4 review dữ liệu phục vụ quan sát.
Danh sách dưới đây lấy từ mục 11.1 kế hoạch. Chỉ hai endpoint đầu tiên tồn tại
trong scaffold; nhóm chốt wire schema ở W1 trước khi cài các endpoint còn lại.

| Endpoint | Trạng thái hiện tại / yêu cầu |
|---|---|
| `GET /health` | 200 `{status: "ok", node_id, consensus_ready: false}` trong bản khung |
| `GET /status` | 503 `CONSENSUS_NOT_READY`; sau tích hợp: height, tip hash, phase, sync state |
| `POST /transactions` | Chưa cài; 202 accepted không đồng nghĩa committed |
| `GET /transactions/{tx_id}` | Chưa cài; pending/committed/rejected/local-unknown |
| `GET /accounts/{address}` | Chưa cài; chỉ số dư và nonce đã chốt |
| `GET /blocks`, `GET /blocks/{height}` | Chưa cài; phân trang, block kèm certificate |
| `GET /consensus/{height}` | Chưa cài; proposal, phase, danh tính vote, certificate |
| `POST /peer/propose`, `/peer/prepare`, `/peer/commit`, `/peer/finalized` | Chưa cài; xác minh đầy đủ, giới hạn payload/buffer |
| `GET /metrics` | Chưa cài; chỉ đo lường, không quyết định consensus |

W1 cần thống nhất field/kiểu dữ liệu/version, mã lỗi, timeout, phân trang và payload
mẫu. Schema giao dịch/vote có chain ID và context ký; quy tắc canonical bytes và
test vector dùng chung do TV1/TV2 chốt. Mock của frontend phải được gắn nhãn và
tách khỏi API thật. Dashboard không nạp private key validator hay tự chốt block.
