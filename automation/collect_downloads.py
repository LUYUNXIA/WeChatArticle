from __future__ import annotations

import argparse
import hashlib
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from common import DATA, ensure_dirs, load_env

SUPPORTED = {".csv", ".xlsx", ".xls", ".zip"}


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="收集浏览器下载的微信公众号数据文件")
    parser.add_argument("--source", help="浏览器下载目录；默认读取 .env 或 Windows Downloads")
    parser.add_argument("--hours", type=int, default=24, help="只收集最近多少小时的文件，默认 24")
    parser.add_argument("--dry-run", action="store_true", help="只显示候选文件，不复制")
    args = parser.parse_args()
    ensure_dirs()
    env = load_env()
    configured = args.source or env.get("WECHAT_DOWNLOAD_DIR", "")
    source = Path(configured).expanduser() if configured else Path.home() / "Downloads"
    if not source.is_dir():
        raise SystemExit(f"下载目录不存在：{source}。可通过 --source 或 WECHAT_DOWNLOAD_DIR 指定。")
    target = DATA / "imports"
    target.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now() - timedelta(hours=args.hours)
    existing_hashes = {digest(path) for path in target.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED}
    candidates = [
        path for path in source.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED
        and datetime.fromtimestamp(path.stat().st_mtime) >= cutoff
        and not path.name.endswith((".crdownload", ".tmp"))
    ]
    copied = 0
    for path in sorted(candidates, key=lambda item: item.stat().st_mtime):
        file_hash = digest(path)
        if file_hash in existing_hashes:
            print(f"跳过重复文件：{path.name}")
            continue
        print(f"发现：{path}")
        if args.dry_run:
            continue
        destination = target / path.name
        if destination.exists():
            stamp = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y%m%d-%H%M%S")
            destination = target / f"{path.stem}-{stamp}{path.suffix.lower()}"
        shutil.copy2(path, destination)
        existing_hashes.add(file_hash)
        copied += 1
        print(f"已复制到：{destination}")
    print(f"候选 {len(candidates)} 个，新收集 {copied} 个。")


if __name__ == "__main__":
    main()
