# Dashboard · TV4 W1

Node.js **24.21.0** (`.nvmrc`), dòng Node 24.x; máy bàn giao dùng npm **12.2.1**.
`package-lock.json` v3 pin cây phụ thuộc. CI dùng Node từ `.nvmrc` và `npm ci`.

```powershell
cd frontend
npm ci
npm run dev
```

Mở URL Vite in ra, mặc định http://127.0.0.1:5173. Proxy chuyển `/api/node1`…
`/api/node4` tới cổng 8001…8004. Dev proxy không phải cấu hình production.
Nếu dùng nvm, chạy `nvm install 24.21.0` và `nvm use 24.21.0` theo công cụ của bạn.

## Review W1

- **Kết nối thật** mặc định: màn mạng đọc GET health/status thật, timeout 3 giây,
  có node nguồn/thời điểm và nút kiểm tra lại. Chưa polling tự động ở W1.
  Health không suy ra quorum; status 503 vẫn để health phản hồi độc lập.
- **Wireframe mẫu**: sáu màn node, giao dịch, tài khoản, block, certificate, timeline;
  nhãn mẫu luôn hiện. Chọn round/tx status để review bố cục. Không gọi API ở chế độ này.
- Lỗi API không chuyển sang mẫu. Màn ledger thật chưa tích hợp có empty state rõ.
  Không nhập/lưu validator key, ký phiếu, gửi transaction hoặc tự commit block.
- Chi tiết schema, trạng thái và checklist cho TV2/TV3 tại [docs/ui.md](../docs/ui.md).
  Đây là wireframe W1; dashboard dữ liệu thật và ví thuộc W2/W3.

```powershell
npm run lint
npm test
npm run build
```

`npm test` dùng Node test runner để kiểm ranh giới adapter: health vẫn hoạt động
khi status 503, giữ mã lỗi ở envelope hiện tại/đề xuất, sai node/JSON/mạng không tạo
dữ liệu thật, chặn đường dẫn node tùy ý. Không coi các test này là T27/T28 hoặc test consensus.

Khi đổi dependency, dùng `npm install` có chủ đích, commit cả package/lockfile,
rồi kiểm lại `npm ci`, lint/test/build. Không dùng `npm install` thay `npm ci` trong CI.
