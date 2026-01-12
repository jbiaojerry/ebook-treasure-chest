import yaml
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
BOOKS_FILE = ROOT / "metadata" / "books.yaml"
OUTPUT_FILE = ROOT / "docs" / "index.md"

print("📂 ROOT:", ROOT)
print("📖 BOOKS_FILE:", BOOKS_FILE)
print("📝 OUTPUT_FILE:", OUTPUT_FILE)
print("📖 books.yaml exists:", BOOKS_FILE.exists())
print("📝 index.md exists:", OUTPUT_FILE.exists())


def load_books():
    with open(BOOKS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        print("📦 YAML raw data:", data)
        return data["books"]


def main():
    books = load_books()
    print("📚 Books count:", len(books))

    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    content = "# TEST GENERATED FILE\n\n"
    for b in books:
        content += f"- {b['title']}\n"

    OUTPUT_FILE.write_text(content, encoding="utf-8")
    print("✅ index.md written")


if __name__ == "__main__":
    main()
