from __future__ import annotations

import argparse
from datetime import datetime

from common import DATA, ROOT, ensure_dirs, read_csv, write_csv

FIELDS = [
    "记录时间", "文章编号", "检查点", "发布日期", "标题", "送达人数", "阅读人数", "读完率", "分享人数",
    "收藏人数", "点赞在看人数", "留言人数", "新增关注", "取关", "推荐阅读人数", "搜一搜阅读人数",
]
NUMBER_FIELDS = FIELDS[5:]


def ask(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def validate_number(name: str, value: str) -> None:
    if not value:
        return
    normalized = value.rstrip("%")
    try:
        parsed = float(normalized)
    except ValueError as exc:
        raise SystemExit(f"{name} 必须是数字，当前值：{value}") from exc
    if parsed < 0:
        raise SystemExit(f"{name} 不能小于 0")


def main() -> None:
    parser = argparse.ArgumentParser(description="记录公众号文章 T+1/T+3/T+7 数据快照")
    parser.add_argument("--id", dest="article_id", help="运营数据看板中的文章编号")
    parser.add_argument("--checkpoint", choices=("T+1", "T+3", "T+7"))
    for field in NUMBER_FIELDS:
        parser.add_argument("--" + field, dest=field)
    args = parser.parse_args()
    ensure_dirs()
    dashboard = read_csv(ROOT / "运营数据看板.csv")
    article_id = args.article_id or ask("文章编号")
    article = next((row for row in dashboard if row.get("编号") == article_id), None)
    if article is None:
        available = "、".join(f"{row.get('编号')}《{row.get('标题')}》" for row in dashboard)
        raise SystemExit(f"未找到文章编号 {article_id}。可选：{available}")
    checkpoint = args.checkpoint or ask("检查点（T+1/T+3/T+7）", "T+1")
    if checkpoint not in ("T+1", "T+3", "T+7"):
        raise SystemExit("检查点只能是 T+1、T+3 或 T+7")
    row = {
        "记录时间": datetime.now().isoformat(timespec="seconds"),
        "文章编号": article_id,
        "检查点": checkpoint,
        "发布日期": article.get("发布日期", ""),
        "标题": article.get("标题", ""),
    }
    values = vars(args)
    for field in NUMBER_FIELDS:
        value = values.get(field)
        if value is None:
            hint = "（可留空）"
            value = ask(field + hint)
        validate_number(field, value)
        row[field] = value
    path = DATA / "metric_snapshots.csv"
    rows = read_csv(path)
    rows.append(row)
    write_csv(path, rows, FIELDS)
    print(f"已记录：文章 {article_id} {checkpoint}，共 {len(rows)} 条历史快照。")


if __name__ == "__main__":
    main()
