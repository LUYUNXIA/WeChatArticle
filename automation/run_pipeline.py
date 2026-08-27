import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    for script in ("scan_articles.py", "import_manual_data.py", "merge_wechat_data.py", "analyze_performance.py", "generate_weekly_report.py"):
        subprocess.run([sys.executable, str(HERE / script)], check=True)
    print("内容学习闭环运行完成。")


if __name__ == "__main__":
    main()
