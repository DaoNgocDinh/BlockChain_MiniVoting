# Cấu hình development

`nodes.json` chỉ mô tả topology local để nhóm thống nhất cổng và đường dẫn.
Đây chưa phải genesis hợp lệ: chưa có public key hay số dư ban đầu đã ký/chốt.
TV1 và TV3 triển khai script sinh key/genesis; mỗi node chỉ nạp private key riêng.

- Bốn validator cố định; quorum luôn là 3/4, không đổi theo số node online.
- Database và khóa của từng node phải độc lập.
- `keys/`, `data/`, `logs/` không đưa vào Git.
- Các cổng hiện chỉ bind loopback; triển khai LAN là một bước riêng có tài liệu.
