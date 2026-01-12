import yaml
import json
from collections import defaultdict
from pathlib import Path

# 路径定义
ROOT = Path(__file__).parent.parent
BOOKS_FILE = ROOT / "metadata" / "books.yaml"
OUTPUT_MD = ROOT / "docs" / "index.md"
OUTPUT_JSON = ROOT / "docs" / "books.json"


def load_books():
    with open(BOOKS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data.get("books", [])


def group_books(books):
    grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    categories, languages, levels = set(), set(), set()

    for b in books:
        c = b["category"]
        l = b["language"]
        lv = b["level"]

        categories.add(c)
        languages.add(l)
        levels.add(lv)

        grouped[c][l][lv].append(b)

    return grouped, categories, languages, levels


def render_overview(books, categories, languages, levels):
    return f"""## 📊 Overview

- 📘 Total books: **{len(books)}**
- 📂 Categories: **{' / '.join(sorted(categories))}**
- 🌍 Languages: **{' / '.join(sorted(languages))}**
- ⭐ Levels: **{' / '.join(sorted(levels))}**
"""


def render_search_ui():
    # 直接写 HTML（GitHub Pages 支持）
    return """## 🔍 Search

<div style="margin: 20px 0;">
  <input
    type="text"
    placeholder="搜索 书名 / 作者 / 分类 / 语言 / 难度"
    oninput="onSearch(event)"
    style="width: 100%; padding: 10px; font-size: 16px;"
  />
</div>

<div id="search-results"></div>

<script src="search.js"></script>
"""


def render_content(grouped):
    lines = []

    for category in sorted(grouped.keys()):
        lines.append(f"## 📂 {category}\n")

        for language in sorted(grouped[category].keys()):
            lines.append(f"### 🌍 Language: {language}\n")

            for level in sorted(grouped[category][language].keys()):
                lines.append(f"#### ⭐ Level: {level}\n")

                for b in grouped[category][language][level]:
                    formats = ", ".join(b.get("formats", []))
                    lines.append(
                        f"- **{b['title']}** — {b.get('author', '')}  \n"
                        f"  格式：{formats} ｜ "
                        f"[下载链接]({b['link']})\n"
                    )

                lines.append("")

    return "\n".join(lines)


def main():
    books = load_books()
    grouped, categories, languages, levels = group_books(books)

    md_parts = []
    md_parts.append("# 📚 Ebook Treasure Chest\n")
    md_parts.append("> 自动生成，请勿手动修改\n\n---\n")
    md_parts.append(render_overview(books, categories, languages, levels))
    md_parts.append("\n---\n")
    md_parts.append(render_search_ui())
    md_parts.append("\n---\n")
    md_parts.append(render_content(grouped))

    OUTPUT_MD.parent.mkdir(exist_ok=True)

    # 写 index.md
    OUTPUT_MD.write_text("\n".join(md_parts), encoding="utf-8")

    # 写 books.json（给前端搜索用）
    OUTPUT_JSON.write_text(
        json.dumps(books, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("✅ index.md & books.json generated")


if __name__ == "__main__":
    main()
