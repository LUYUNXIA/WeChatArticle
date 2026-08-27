from __future__ import annotations

import json

from common import DATA, RAW, ensure_dirs, read_csv, write_csv
from import_manual_data import FIELDS


def latest_detail(details: list[dict]) -> dict:
    return max(details, key=lambda item: item.get("stat_date", ""), default={})


def main() -> None:
    ensure_dirs()
    rows = read_csv(DATA / "article_metrics.csv")
    by_title = {row.get("标题", "").strip(): row for row in rows}
    updated = 0
    for path in sorted(RAW.glob("wechat-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        article_total = payload.get("getarticletotal", {})
        if article_total.get("error"):
            continue
        for article in article_total.get("list", []):
            title = str(article.get("title", "")).strip()
            row = by_title.get(title)
            if not row:
                continue
            detail = latest_detail(article.get("details", []))
            mapping = {
                "送达人数": detail.get("target_user"),
                "阅读人数": detail.get("int_page_read_user"),
                "分享人数": detail.get("share_user"),
                "收藏人数": detail.get("add_to_fav_user"),
            }
            for target, value in mapping.items():
                if value is not None:
                    row[target] = str(value)
            updated += 1
    write_csv(DATA / "article_metrics.csv", rows, FIELDS)
    print(f"已将微信 API 数据合并到 {updated} 篇文章。")


if __name__ == "__main__":
    main()
