from pathlib import Path

DOCS = Path("docs")
DOCS.mkdir(exist_ok=True)

with open(DOCS / "index.md", "w", encoding="utf-8") as f:
    f.write("""---
layout: default
title: Ebook Treasure Chest
---

# 📚 Ebook Treasure Chest

这个页面是由脚本自动生成的。
""")

print("docs/index.md generated")
