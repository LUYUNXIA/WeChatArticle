from datetime import date

from common import DATA, REPORTS, ensure_dirs, read_csv


def main() -> None:
    ensure_dirs()
    rows = read_csv(DATA / "analysis_results.csv")
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
    lines.extend(["## 下一篇唯一主要改动", "", suggestions[0] if suggestions else "补齐数据，暂不改变内容策略。", "",
                  "## 学习边界", "", "本报告只生成候选假设。规律至少需要 3 篇同类文章验证，并排除热点、节假日和异常推荐影响后，才能写入 `knowledge/proven_patterns.md`。", ""])
    target = REPORTS / f"weekly-{date.today().isoformat()}.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    print(f"周报已生成：{target.relative_to(target.parents[1])}")


if __name__ == "__main__":
    main()
