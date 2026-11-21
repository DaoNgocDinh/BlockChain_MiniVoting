# Script dùng chung

`run-node.ps1 -NodeId node1` chạy một API scaffold ở foreground; Ctrl+C dừng đúng tiến trình.
Để thử bốn node, mở bốn terminal và lần lượt chọn node1–node4.

TV3 bổ sung bộ chạy/dừng bốn tiến trình có kiểm tra PID và ownership, không kill theo tên
`python` chung. TV1/TV3 bổ sung sinh key/genesis. TV4/TV3 bổ sung workload và fault runner.

Các script sắp tới phải ghi rõ config, seed, commit SHA và nơi xuất log; không xóa DB/keys
âm thầm. Không tái sử dụng biến hệ thống như `$HOME` làm biến nội bộ.
