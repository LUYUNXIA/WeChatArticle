from datetime import date

from common import DATA, REPORTS, ensure_dirs, read_csv


def main() -> None:
    ensure_dirs()
    rows = read_csv(DATA / "analysis_results.csv")
    daily_rows = read_csv(DATA / "wechat_daily_metrics.csv")
    user_rows = read_csv(DATA / "wechat_user_metrics.csv")
    dated = sorted(rows, key=lambda row: row.get("发布日期", ""))
    recent = dated[-5:]
    lines = [
        f"# 向阳小人间内容学习周报 · {date.today().isoformat()}", "",
        "## 本轮结论", "",
    ]
    if not recent:
        lines.append("暂无可分析数据。请先运行数据导入并补录文章表现。")
    else:
        for row in recent:
            lines.extend([
                f"### {row.get('标题') or '未命名文章'}", "",
                f"- 诊断：{row.get('诊断', '—')}",
                f"- 阅读人数：{row.get('阅读人数') or '—'}；相对阅读指数：{row.get('相对阅读指数') or '—'}",
                f"- 建议实验：{row.get('实验建议', '—')}", "",
            ])
    suggestions = [row.get("实验建议", "") for row in reversed(recent) if row.get("实验建议") and row.get("诊断") != "数据不足"]
    lines.extend(["## 账号级数据", ""])
    if daily_rows:
        latest_daily = sorted(daily_rows, key=lambda row: row.get("日期", ""))[-1]
        lines.append(
            f"- {latest_daily.get('日期')}：账号阅读人数 {latest_daily.get('阅读人数') or '—'}，"
            f"分享人数 {latest_daily.get('分享人数') or '—'}，收藏人数 {latest_daily.get('微信收藏人数') or '—'}，"
            f"发表篇数 {latest_daily.get('发表篇数') or '—'}。"
        )
    if user_rows:
        latest_user = sorted(user_rows, key=lambda row: row.get("日期", ""))[-1]
        lines.append(
            f"- {latest_user.get('日期')}：新增关注 {latest_user.get('新增关注') or '—'}，"
            f"取关 {latest_user.get('取关') or '—'}，净增关注 {latest_user.get('净增关注') or '—'}，"
            f"累计关注 {latest_user.get('累计关注') or '—'}。"
        )
    lines.extend(["", "账号级数据不直接归因给单篇文章；文章指标只采用标题与日期匹配后的导出记录。", "",
                  "## 下一篇唯一主要改动", "", suggestions[0] if suggestions else "补齐数据，暂不改变内容策略。", "",
                  "## 学习边界", "", "本报告只生成候选假设。规律至少需要 3 篇同类文章验证，并排除热点、节假日和异常推荐影响后，才能写入 `knowledge/proven_patterns.md`。", ""])
    target = REPORTS / f"weekly-{date.today().isoformat()}.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    print(f"周报已生成：{target.relative_to(target.parents[1])}")


if __name__ == "__main__":
    main()
