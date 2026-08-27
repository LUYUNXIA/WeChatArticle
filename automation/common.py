from __future__ import annotations

import csv
import json
import re
from datetime import date, datetime
from pathlib import Path
from statistics import median
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
REPORTS = ROOT / "reports"
KNOWLEDGE = ROOT / "knowledge"


def ensure_dirs() -> None:
    for path in (DATA, RAW, REPORTS, KNOWLEDGE):
        path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def number(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(str(value).strip().rstrip("%")) / (100 if "%" in str(value) else 1)
    except ValueError:
        return None


def ratio(part: Any, whole: Any) -> float | None:
    p, w = number(part), number(whole)
    return p / w if p is not None and w not in (None, 0) else None


def fmt(value: float | None, percent: bool = False) -> str:
    if value is None:
        return "—"
    return f"{value:.1%}" if percent else f"{value:.2f}".rstrip("0").rstrip(".")


def rolling_median(values: list[float | None], window: int = 5) -> float | None:
    clean = [v for v in values if v is not None]
    return median(clean[-window:]) if clean else None


def load_env() -> dict[str, str]:
    result: dict[str, str] = {}
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                result[key.strip()] = value.strip()
    return result


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def extract_article(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    headings = [line.lstrip("# ").strip() for line in lines if re.match(r"^#{1,3}\s+", line)]
    title = headings[0] if headings else path.stem
    title = re.sub(r"^(标题[一二三四五六七八九十]*[:：]\s*)", "", title)
    body = re.sub(r"[#>*_`\-]", "", text)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    folder_date = re.search(r"day\d+_(\d{8})", path.as_posix())
    publish_date = ""
    if folder_date:
        publish_date = datetime.strptime(folder_date.group(1), "%Y%m%d").date().isoformat()
    title_type = "判断型"
    if "？" in title or "?" in title:
        title_type = "提问型"
    elif re.search(r"\d|[一二三四五六七八九十]+种|[一二三四五六七八九十]+个", title):
        title_type = "数字型"
    elif re.search(r"他|她|孩子|妈妈|父母|妻子|丈夫", title):
        title_type = "故事/关系型"
    return {
        "文章路径": path.relative_to(ROOT).as_posix(),
        "发布日期": publish_date,
        "标题": title,
        "标题类型": title_type,
        "正文字符数": len(re.sub(r"\s", "", body)),
        "段落数": len(paragraphs),
        "小标题数": max(0, len(headings) - 1),
        "是否含行动建议": "是" if re.search(r"可以|试着|先做|观察|行动", text) else "否",
    }
