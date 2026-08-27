from __future__ import annotations

from common import DATA, ensure_dirs, fmt, number, read_csv, rolling_median, write_csv

FIELDS = ["编号", "发布日期", "栏目", "标题", "阅读人数", "送达阅读率", "读完率", "分享率", "收藏率", "关注转化率", "相对阅读指数", "诊断", "实验建议"]


def diagnose(row: dict[str, str], medians: dict[str, float | None]) -> tuple[str, str]:
    reads = number(row.get("阅读人数"))
    open_rate = number(row.get("送达阅读率"))
    finish = number(row.get("读完率"))
    share = number(row.get("分享率"))
    collect = number(row.get("收藏率"))
    conversion = number(row.get("关注转化率"))
    if reads is None:
        return "数据不足", "补录发布后 T+1、T+3、T+7 数据，暂不调整内容策略"
    high_open = open_rate is not None and medians["送达阅读率"] is not None and open_rate >= medians["送达阅读率"]
    high_finish = finish is not None and medians["读完率"] is not None and finish >= medians["读完率"]
    if high_open and finish is not None and not high_finish:
        return "打开高、读完偏低", "下一篇只测试：将核心判断提前到前 300 字"
    if open_rate is not None and not high_open and high_finish:
        return "打开偏低、读完高", "下一篇保持正文结构，只测试标题与封面包装"
    if collect is not None and medians["收藏率"] is not None and collect >= medians["收藏率"] * 1.3:
        return "高收藏长尾题", "14 天内安排同主题的不同场景延伸"
    if share is not None and medians["分享率"] is not None and share >= medians["分享率"] * 1.3 and (conversion or 0) < (medians["关注转化率"] or 0):
        return "分享高、关注沉淀弱", "下一篇只测试：强化合集定位与关注理由"
    return "接近账号基线", "保持定位；等待更多样本后再形成规律"


def main() -> None:
    ensure_dirs()
    rows = read_csv(DATA / "article_metrics.csv")
    metric_names = ["送达阅读率", "读完率", "分享率", "收藏率", "关注转化率"]
    medians = {name: rolling_median([number(row.get(name)) for row in rows]) for name in metric_names}
    read_median = rolling_median([number(row.get("7天阅读人数")) or number(row.get("阅读人数")) for row in rows])
    output = []
    for row in rows:
        current = number(row.get("7天阅读人数")) or number(row.get("阅读人数"))
        relative = current / read_median if current is not None and read_median else None
        diagnosis, experiment = diagnose(row, medians)
        item = {key: row.get(key, "") for key in FIELDS}
        item["相对阅读指数"] = fmt(relative)
        item["诊断"] = diagnosis
        item["实验建议"] = experiment
        output.append(item)
    write_csv(DATA / "analysis_results.csv", output, FIELDS)
    print(f"已分析 {len(output)} 篇文章：data/analysis_results.csv")


if __name__ == "__main__":
    main()
