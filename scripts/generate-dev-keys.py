"""Script chuẩn bị thư mục dữ liệu và khóa phát triển cho 4 validator.

Đảm bảo:
- 4 thư mục data/node1..data/node4 hoàn toàn độc lập.
- Thư mục keys/ được tạo và bảo vệ bởi .gitignore.
- Không commit khóa bảo mật thật vào git repository.
"""

import sys
from pathlib import Path

# Add project root to sys.path so src imports work when script is called directly
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.network.config import load_cluster_config


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    config = load_cluster_config(project_root / "config" / "nodes.json")

    print("=" * 60)
    print("CHUẨN BỊ MÔI TRƯỜNG LƯU TRỮ VÀ KHÓA CHO 4 VALIDATOR")
    print("=" * 60)

    # 1. Đảm bảo thư mục dữ liệu độc lập cho từng node
    for nid, node in config.nodes.items():
        abs_data = (project_root / node.data_dir).resolve()
        abs_data.mkdir(parents=True, exist_ok=True)
        print(f"[+] Thư mục dữ liệu {nid}: {abs_data}")

    # 2. Đảm bảo thư mục keys
    keys_dir = project_root / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)
    print(f"[+] Thư mục keys: {keys_dir}")

    # 3. Tạo placeholder khóa phát triển nếu chưa có
    for nid, node in config.nodes.items():
        abs_key = (project_root / node.key_path).resolve()
        if not abs_key.exists():
            # Tạo placeholder dev key để kiểm tra path
            abs_key.write_text(
                f"# Dev key placeholder for {nid}. Replaced during genesis generation.\n",
                encoding="utf-8",
            )
            print(f"[+] Đã tạo placeholder khóa: {abs_key}")
        else:
            print(f"[*] Khóa {nid} đã tồn tại: {abs_key}")

    print("\nHoàn tất: Đã thiết lập xong 4 thư mục dữ liệu và đường dẫn khóa tách biệt.")


if __name__ == "__main__":
    main()
