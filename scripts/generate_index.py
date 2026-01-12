import yaml
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
BOOKS_FILE = ROOT / "metadata" / "books.yaml"
OUTPUT_FILE = ROOT / "docs" / "index.md"


def load_books():
    with open(BOOKS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["books"]


def group_books(books):
    grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for book in books:
        grouped[book["category"]][book["language"]][book["level"]].append(book)

    return grouped


def generate_markdown(grouped):
    lines = []

    lines.append("# 📚 Ebook Treasure Chest\n")
    lines.append("> 自动生成，请勿手动修改\n\n")

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

                lines.append("\n")

    return "\n".join(lines)


def main():
    books = load_books()
    grouped = group_books(books)
    markdown = generate_markdown(grouped)

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(markdown, encoding="utf-8")

    print("✅ docs/index.md generated successfully")


if __name__ == "__main__":
    main()
