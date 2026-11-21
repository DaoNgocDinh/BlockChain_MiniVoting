# Thiết lập GitHub của nhóm

## Áp dụng trọn bộ sau khi có quyền GitHub

Bộ khung được lưu ở checkout local. Ngày 21/11/2026, kết nối GitHub từ chối cả
tạo file và tạo issue với HTTP 403 `Resource not accessible by integration`.
Repo remote vẫn trống, chưa có bảo vệ nhánh hay issue được tạo trong lượt setup.

Sau khi cài GitHub CLI, đăng nhập tài khoản có Contents/Issues write và quyền
Administration của repository rồi chạy từ gốc checkout:

```powershell
gh auth login --hostname github.com
powershell -NoProfile -File scripts/setup-github.ps1
```

Script kiểm tra repo/nhánh/working tree, push bình thường (không force), áp dụng
ruleset, tạo 14 nhãn, 6 milestone và 24 issue. Mỗi issue có dependency link, reviewer,
checklist và milestone; sáu issue TV4 gán @DaoNgocDinh. TV1–TV3 chưa gán tài khoản.
Chạy lại tái sử dụng milestone và issue theo mã, không ghi đè tiến độ issue đã có.
Script chưa được thực thi trên GitHub do thiếu quyền; cần kiểm tra kết quả API
sau khi chạy, không coi sự tồn tại script/JSON là bằng chứng setup remote đã xong.

## Bảo vệ main

File `.github/rulesets/protect-main.json` là cấu hình đề xuất, không tự có hiệu lực
khi được commit. Cần chủ repo import hoặc gọi GitHub API bằng quyền Administration.

Vào **Settings → Rules → Rulesets → New ruleset → Import a ruleset**, chọn JSON,
kiểm tra **Active**, target `main`, rồi **Create**. Cấu hình:

- Một review chấp thuận từ người khác; dismiss stale reviews khi thay đổi code.
- Giải quyết các review thread trước merge.
- Chặn force push và xóa `main`; không có actor bypass.

Chỉ sau khi hai job CI đã xanh, thêm **Require status checks to pass** và chọn
`Python lint and tests`, `Frontend lint and build`. Không chọn check chưa xuất
hiện/chưa chạy được. Quy tắc yêu cầu PR/review không thay cho kiểm thử.

Nếu đã đăng nhập GitHub CLI với quyền quản trị, có thể chạy từ gốc repo:

```powershell
gh api --method POST repos/DaoNgocDinh/BlockChain_MiniVoting/rulesets --input .github/rulesets/protect-main.json
gh api repos/DaoNgocDinh/BlockChain_MiniVoting/rules/branches/main
```

Trước khi POST phải kiểm tra ruleset hiện có để tránh tạo trùng.
Lệnh GET cuối phải trả các rule active; một file JSON trong repo không chứng minh
`main` đã được bảo vệ.

## Thành viên và theo dõi công việc

Chủ repo mời ba username thật qua Settings → Collaborators → Add people. Sau khi
họ chấp nhận, gán các issue có nhãn TV1/TV2/TV3 tương ứng. TV4 là @DaoNgocDinh.

Workflow thủ công `Project metadata` tạo/cập nhật nhãn vai trò, module, ưu tiên và sáu
milestone tuần tương đối. Nó chỉ có quyền Issues, không có quyền quản trị nhánh.
Issues là đơn vị theo dõi chính; `docs/backlog.md` giữ danh sách mã và liên kết.
