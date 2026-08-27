from common import DATA, ROOT, ensure_dirs, extract_article, write_csv

FIELDS = ["文章路径", "发布日期", "标题", "标题类型", "正文字符数", "段落数", "小标题数", "是否含行动建议"]


def main() -> None:
    ensure_dirs()
    paths = sorted((ROOT / "dataset").glob("**/*发布稿.md"))
    rows = [extract_article(path) for path in paths]
    write_csv(DATA / "article_features.csv", rows, FIELDS)
    print(f"已扫描 {len(rows)} 篇文章：data/article_features.csv")


if __name__ == "__main__":
    main()
