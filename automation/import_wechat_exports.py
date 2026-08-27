from __future__ import annotations

import re
from difflib import SequenceMatcher
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd

from common import DATA, ROOT, ensure_dirs, read_csv, write_csv
from import_manual_data import FIELDS as DASHBOARD_FIELDS

CONTENT_FIELDS = ["发布日期", "标题", "阅读人数", "公众号消息", "聊天会话", "朋友圈", "公众号主页", "其他", "推荐阅读人数", "搜一搜阅读人数"]
DAILY_FIELDS = ["日期", "阅读人数", "分享人数", "跳转阅读原文人数", "微信收藏人数", "发表篇数"]
USER_FIELDS = ["日期", "新增关注", "取关", "净增关注", "累计关注"]


def clean(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return text[:-2] if text.endswith(".0") and text[:-2].isdigit() else text


def normalize_date(value) -> str:
    text = clean(value)
    digits = re.sub(r"\D", "", text)
    if len(digits) == 8:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:]}"
    return text


def normalized_title(value: str) -> str:
    return re.sub(r"[\s，。！？、：；“”‘’《》【】（）()\-—]", "", value)


def match_article(publish_date: str, title: str, candidates: list[dict[str, str]]) -> tuple[dict[str, str] | None, str]:
    exact = next((item for item in candidates if item["发布日期"] == publish_date and item["标题"] == title), None)
    if exact:
        return exact, "精确"
    same_day = [item for item in candidates if item["发布日期"] == publish_date]
    scored = sorted(
        ((SequenceMatcher(None, normalized_title(title), normalized_title(item["标题"])).ratio(), item) for item in same_day),
        key=lambda pair: pair[0], reverse=True,
    )
    if not scored:
        return None, "无匹配"
    best_score, best = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else 0
    if best_score >= 0.88 and best_score - second_score >= 0.05:
        return best, f"模糊({best_score:.2f})"
    return None, "有歧义"


def find_header(raw: pd.DataFrame, label: str) -> tuple[int, int] | None:
    for row in range(len(raw)):
        for col in range(len(raw.columns)):
            if clean(raw.iat[row, col]) == label:
                return row, col
    return None


def parse_content(path: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    raw = pd.read_excel(path, header=None)
    source_pos = find_header(raw, "传播渠道")
    if not source_pos:
        return [], []
    header_row, start = source_pos
    article_map: dict[tuple[str, str], dict[str, str]] = {}
    channel_map = {"推荐": "推荐阅读人数", "搜一搜": "搜一搜阅读人数"}
    for row_index in range(header_row + 1, len(raw)):
        channel = clean(raw.iat[row_index, start])
        publish_date = normalize_date(raw.iat[row_index, start + 1])
        title = clean(raw.iat[row_index, start + 2])
        reads = clean(raw.iat[row_index, start + 3])
        if not title or not publish_date:
            continue
        key = (publish_date, title)
        item = article_map.setdefault(key, {field: "0" for field in CONTENT_FIELDS})
        item.update({"发布日期": publish_date, "标题": title})
        if channel == "全部":
            item["阅读人数"] = reads
        else:
            target = channel_map.get(channel, channel)
            if target in item:
                item[target] = reads

    daily_pos = None
    for row in range(len(raw)):
        for col in range(len(raw.columns) - 4):
            if clean(raw.iat[row, col]) == "日期" and clean(raw.iat[row, col + 1]) == "分享人数":
                daily_pos = (row, col)
                break
        if daily_pos:
            break
    daily_rows: list[dict[str, str]] = []
    if daily_pos:
        row, col = daily_pos
        for index in range(row + 1, len(raw)):
            day = normalize_date(raw.iat[index, col])
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", day):
                continue
            daily_rows.append({
                "日期": day,
                "分享人数": clean(raw.iat[index, col + 1]),
                "跳转阅读原文人数": clean(raw.iat[index, col + 2]),
                "微信收藏人数": clean(raw.iat[index, col + 3]),
                "发表篇数": clean(raw.iat[index, col + 4]),
                "阅读人数": "",
            })
    channel_pos = find_header(raw, "渠道")
    if channel_pos:
        row, col = channel_pos
        totals: dict[str, str] = {}
        for index in range(row + 1, len(raw)):
            day = normalize_date(raw.iat[index, col - 1])
            channel = clean(raw.iat[index, col])
            if channel == "全部":
                totals[day] = clean(raw.iat[index, col + 1])
        for item in daily_rows:
            item["阅读人数"] = totals.get(item["日期"], "")
    return list(article_map.values()), daily_rows


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self.row: list[str] | None = None
        self.cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag in ("th", "td") and self.row is not None:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("th", "td") and self.cell is not None and self.row is not None:
            self.row.append("".join(self.cell).strip())
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.row:
                self.rows.append(self.row)
            self.row = None


def parse_users(path: Path) -> list[dict[str, str]]:
    parser = TableParser()
    parser.feed(path.read_text(encoding="utf-8-sig"))
    result = []
    for cells in parser.rows:
        if len(cells) >= 5 and re.match(r"^\d{4}-\d{2}-\d{2}$", cells[0]):
            values = ["" if value == "-" else value for value in cells]
            result.append(dict(zip(USER_FIELDS, values[:5])))
    return result


def main() -> None:
    ensure_dirs()
    imports = DATA / "imports"
    content_rows: list[dict[str, str]] = []
    daily_rows: list[dict[str, str]] = []
    user_rows: list[dict[str, str]] = []
    for path in sorted(imports.glob("*.xls")):
        signature = path.read_bytes()[:8]
        if signature.startswith(b"<html"):
            user_rows.extend(parse_users(path))
        elif signature == bytes.fromhex("D0CF11E0A1B11AE1"):
            articles, daily = parse_content(path)
            content_rows.extend(articles)
            daily_rows.extend(daily)
    write_csv(DATA / "wechat_content_metrics.csv", content_rows, CONTENT_FIELDS)
    write_csv(DATA / "wechat_daily_metrics.csv", daily_rows, DAILY_FIELDS)
    write_csv(DATA / "wechat_user_metrics.csv", user_rows, USER_FIELDS)

    dashboard = read_csv(ROOT / "运营数据看板.csv")
    updated = 0
    match_log = []
    for row in dashboard:
        source, match_type = match_article(row.get("发布日期", ""), row.get("标题", ""), content_rows)
        if not source:
            continue
        for field in ("阅读人数", "推荐阅读人数", "搜一搜阅读人数"):
            row[field] = source.get(field, "")
        updated += 1
        match_log.append({"看板标题": row.get("标题", ""), "导出标题": source.get("标题", ""), "匹配方式": match_type})
    if updated:
        write_csv(ROOT / "运营数据看板.csv", dashboard, DASHBOARD_FIELDS)
    write_csv(DATA / "wechat_title_matches.csv", match_log, ["看板标题", "导出标题", "匹配方式"])
    print(f"已解析文章 {len(content_rows)} 条、账号日数据 {len(daily_rows)} 条、用户日数据 {len(user_rows)} 条；匹配看板 {updated} 篇。")


if __name__ == "__main__":
    main()
