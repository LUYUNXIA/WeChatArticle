from common import DATA, ROOT, ensure_dirs, number, ratio, read_csv, write_csv

FIELDS = [
    "编号", "发布日期", "发布时间", "栏目", "标题", "字数", "送达人数", "阅读人数", "送达阅读率",
    "读完率", "分享人数", "分享率", "收藏人数", "收藏率", "点赞在看人数", "留言人数", "新增关注",
    "取关", "净增关注", "关注转化率", "推荐阅读人数", "搜一搜阅读人数", "7天阅读人数", "相对阅读指数",
    "关键留言", "复盘结论", "下一步动作",
]


def main() -> None:
    ensure_dirs()
    rows = read_csv(ROOT / "运营数据看板.csv")
    for row in rows:
        calculated = {
            "送达阅读率": ratio(row.get("阅读人数"), row.get("送达人数")),
            "分享率": ratio(row.get("分享人数"), row.get("阅读人数")),
            "收藏率": ratio(row.get("收藏人数"), row.get("阅读人数")),
            "关注转化率": ratio(row.get("新增关注"), row.get("阅读人数")),
        }
        for key, value in calculated.items():
            if number(row.get(key)) is None and value is not None:
                row[key] = f"{value:.6f}"
        if number(row.get("净增关注")) is None:
            added, lost = number(row.get("新增关注")), number(row.get("取关"))
            if added is not None and lost is not None:
                row["净增关注"] = str(int(added - lost))
    write_csv(DATA / "article_metrics.csv", rows, FIELDS)
    print(f"已导入 {len(rows)} 条记录：data/article_metrics.csv")


if __name__ == "__main__":
    main()
