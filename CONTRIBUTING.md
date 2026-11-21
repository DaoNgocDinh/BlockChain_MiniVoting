# Quy trình làm việc của nhóm

## Nhánh và pull request

`main` là bản tích hợp chung. Mỗi đầu việc dùng nhánh ngắn, ví dụ
`feat/core-validation`, `feat/prepare-commit`, `feat/node-sync`, `feat/dashboard`.
Tên người có thể ghi trong issue; không dùng nhánh cá nhân tồn tại suốt dự án.

```powershell
git switch main
git pull --ff-only origin main
git switch -c feat/ten-tinh-nang
# Sửa code, chạy test phù hợp, kiểm tra git diff và git status.
git add <cac-file-cua-dau-viec>
git commit -m "feat: mo ta hanh vi thay doi"
git push -u origin feat/ten-tinh-nang
```

Mở PR vào `main`, liên kết issue bằng `Closes #N`, ghi kết quả test và ảnh hưởng
schema. Ít nhất một người khác review. Nhóm ưu tiên Squash and merge cho PR nhỏ;
xóa nhánh sau merge và tạo nhánh mới từ `main` cho việc tiếp theo.
Không force-push `main`, không tự duyệt PR của mình và không merge lịch sử không
liên quan để xử lý xung đột. Giải quyết xung đột trên nhánh tính năng rồi chạy lại test.

## Review theo trách nhiệm

| Phần thay đổi | Người review cần có |
|---|---|
| Hash, validity, serialization | TV2; TV3 nếu đổi persistence interface |
| Quorum, vote, locks, certificate | TV1 và/hoặc TV3 theo điểm thay đổi |
| Atomic commit, recovery, own vote persistence | TV1/TV2 |
| API và wire schema | TV3 cùng chủ module liên quan |
| Dashboard và số liệu | TV3 review API; TV2 review diễn giải consensus |

Các thay đổi API/genesis/schema phải thống nhất trước, ghi trong tài liệu và cập
nhật test vector cùng lúc. Chạy full integration suite khi đã có suite và thay
đổi consensus/storage; không dùng việc build UI thành công thay cho test đồng thuận.

## Definition of Done

- Đạt tiêu chí nghiệm thu của issue, chạy được với cấu hình nhóm.
- Có kiểm tra hành vi phù hợp; các kiểm tra cũ vẫn đạt.
- Log và tài liệu đủ để tái hiện; không chứa private key/.env/DB local.
- Được review, giải quyết trao đổi, merge và demo trong bản chung.
- Kết quả còn giới hạn được ghi rõ; accepted không được báo thành committed.

Mỗi người viết chương báo cáo và kịch bản demo phần mình. TV4 tổng hợp tài liệu,
không viết thay toàn bộ nhóm. Chỉ tag release khi đã đạt cổng nghiệm thu của kế hoạch.
