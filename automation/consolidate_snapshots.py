from __future__ import annotations

from common import DATA, ROOT, ensure_dirs, number, ratio, read_csv, write_csv
from import_manual_data import FIELDS

CHECKPOINT_ORDER = {"T+1": 1, "T+3": 3, "T+7": 7}


def main() -> None:
    ensure_dirs()
    dashboard = read_csv(ROOT / "运营数据看板.csv")
    snapshots = read_csv(DATA / "metric_snapshots.csv")
    latest: dict[str, dict[str, str]] = {}
    for snapshot in snapshots:
        article_id = snapshot.get("文章编号", "")
        current = latest.get(article_id)
        key = (CHECKPOINT_ORDER.get(snapshot.get("检查点", ""), 0), snapshot.get("记录时间", ""))
        current_key = (CHECKPOINT_ORDER.get(current.get("检查点", ""), 0), current.get("记录时间", "")) if current else (-1, "")
        if key >= current_key:
            latest[article_id] = snapshot
    copied_fields = ["送达人数", "阅读人数", "读完率", "分享人数", "收藏人数", "点赞在看人数", "留言人数", "新增关注", "取关", "推荐阅读人数", "搜一搜阅读人数"]
    updated = 0
    for row in dashboard:
        snapshot = latest.get(row.get("编号", ""))
        if not snapshot:
            continue
        for field in copied_fields:
            if snapshot.get(field, "") != "":
                row[field] = snapshot[field]
        if snapshot.get("检查点") == "T+7" and snapshot.get("阅读人数"):
            row["7天阅读人数"] = snapshot["阅读人数"]
        calculated = {
            "送达阅读率": ratio(row.get("阅读人数"), row.get("送达人数")),
            "分享率": ratio(row.get("分享人数"), row.get("阅读人数")),
            "收藏率": ratio(row.get("收藏人数"), row.get("阅读人数")),
            "关注转化率": ratio(row.get("新增关注"), row.get("阅读人数")),
        }
        for field, value in calculated.items():
            if value is not None:
                row[field] = f"{value:.6f}"
        added, lost = number(row.get("新增关注")), number(row.get("取关"))
        if added is not None and lost is not None:
            row["净增关注"] = str(int(added - lost))
        updated += 1
    if updated:
        write_csv(ROOT / "运营数据看板.csv", dashboard, FIELDS)
    print(f"已用最新快照更新 {updated} 篇文章的运营数据看板。")


if __name__ == "__main__":
    main()
