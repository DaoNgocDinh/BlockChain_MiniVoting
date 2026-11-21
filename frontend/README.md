# Dashboard · TV4

Node.js 22.12+; khuyến nghị cùng dùng Node.js 24 LTS.

```powershell
npm install
npm run dev
```

Mở URL Vite in ra; mặc định là http://localhost:5173. Dev proxy chuyển
`/api/node1`…`/api/node4` tới cổng 8001…8004 để không cần mở CORS rộng.
Trang khung đọc `/health` thật khi tải trang; không giả số block hay vote.
Polling, status, explorer, ví và timeline sẽ được làm trong các issue TV4.

```powershell
npm run lint
npm run build
```

TV4 chốt và commit `package-lock.json` sau khi cài trên môi trường nhóm; sau đó chuyển
CI sang `npm ci`. Bản khung pin phiên bản trực tiếp trong `package.json`.
Vite proxy chỉ phục vụ development; khi triển khai cần cấu hình reverse proxy riêng.
