import yaml
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
BOOKS_FILE = ROOT / "metadata" / "books.yaml"
OUTPUT_FILE = ROOT / "docs" / "index.md"
JSON_FILE = ROOT / "docs" / "books.json"


def load_books():
    with open(BOOKS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["books"]


def group_books(books):
    grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    categories = set()
    languages = set()
    levels = set()

    for book in books:
        c = book["category"]
        l = book["language"]
        lv = book["level"]

        categories.add(c)
        languages.add(l)
        levels.add(lv)

        grouped[c][l][lv].append(book)

    return grouped, categories, languages, levels


def generate_overview(books, categories, languages, levels):
    lines = []
    lines.append("## 📊 Overview\n")
    lines.append(f"- 📘 Total books: **{len(books)}**")
    lines.append(f"- 📂 Categories: **{' / '.join(sorted(categories))}**")
    lines.append(f"- 🌍 Languages: **{' / '.join(sorted(languages))}**")
    lines.append(f"- ⭐ Levels: **{' / '.join(sorted(levels))}**\n")
    return "\n".join(lines)


def generate_nav(categories):
    lines = []
    lines.append("## 🧭 Quick Navigation\n")
    for c in sorted(categories):
        anchor = c.lower().replace(" ", "-")
        lines.append(f"- [📂 {c}](#- {anchor})".replace(" ", ""))
    lines.append("")
    return "\n".join(lines)


def generate_content(grouped):
    lines = []

    for category, languages in grouped.items():
        lines.append(f"## 📂 {category}\n")

        for language, levels in languages.items():
            lines.append(f"### 🌍 Language: {language}\n")

            for level, books in levels.items():
                lines.append(f"#### ⭐ Level: {level}\n")

                for book in books:
                    formats = ", ".join(book["formats"])
                    lines.append(
                        f"- **{book['title']}** — {book['author']}  \n"
                        f"  格式：{formats} ｜ "
                        f"[下载链接]({book['link']})\n"
                    )

                lines.append("")

    return "\n".join(lines)


def main():
    books = load_books()
    grouped, categories, languages, levels = group_books(books)

    md = []
    md.append("# 📚 Ebook Treasure Chest\n")
    md.append("> 自动生成，请勿手动修改\n\n---\n")
    md.append(generate_overview(books, categories, languages, levels))
    md.append("\n---\n")
    md.append(generate_nav(categories))
    md.append("\n---\n")
    md.append(generate_content(grouped))

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(md), encoding="utf-8")

    # 生成给前端用的搜索数据
    JSON_FILE.write_text(
        json.dumps(books, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("✅ index.md updated")


if __name__ == "__main__":
    main()
