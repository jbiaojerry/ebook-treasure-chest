import yaml
import json
import re
from collections import defaultdict
from pathlib import Path

# 路径定义
ROOT = Path(__file__).parent.parent
BOOKS_FILE = ROOT / "metadata" / "books.yaml"
OUTPUT_HTML = ROOT / "docs" / "index.html"
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
    placeholder="搜索 书名 / 作者 / 分类（支持多关键词，用空格分隔）"
    oninput="onSearch(event)"
    style="width: 100%; padding: 10px; font-size: 16px; border: 2px solid #0366d6; border-radius: 4px;"
  />
  <p style="margin-top: 10px; color: #586069; font-size: 14px;">
    💡 提示：支持搜索书名、作者、分类，可输入多个关键词（用空格分隔）
  </p>
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


def markdown_to_html(md_content):
    """简单的 Markdown 转 HTML 转换"""
    lines = md_content.split('\n')
    result_lines = []
    in_list = False
    in_paragraph = False
    paragraph_lines = []
    in_html_block = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # 检测 HTML 块开始/结束
        if '<div' in stripped or '<script' in stripped:
            in_html_block = True
        if '</div>' in stripped or '</script>' in stripped:
            in_html_block = False
        
        # HTML 块内的内容直接保留
        if in_html_block or ('<' in stripped and '>' in stripped and not stripped.startswith('#')):
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_paragraph:
                result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
                paragraph_lines = []
                in_paragraph = False
            result_lines.append(line)
            i += 1
            continue
        
        # 空行
        if not stripped:
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_paragraph:
                result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
                paragraph_lines = []
                in_paragraph = False
            result_lines.append('')
            i += 1
            continue
        
        # 标题
        if stripped.startswith('#### '):
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_paragraph:
                result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
                paragraph_lines = []
                in_paragraph = False
            result_lines.append(f'<h4>{stripped[5:]}</h4>')
        elif stripped.startswith('### '):
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_paragraph:
                result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
                paragraph_lines = []
                in_paragraph = False
            result_lines.append(f'<h3>{stripped[4:]}</h3>')
        elif stripped.startswith('## '):
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_paragraph:
                result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
                paragraph_lines = []
                in_paragraph = False
            result_lines.append(f'<h2>{stripped[3:]}</h2>')
        elif stripped.startswith('# '):
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_paragraph:
                result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
                paragraph_lines = []
                in_paragraph = False
            result_lines.append(f'<h1>{stripped[2:]}</h1>')
        # 水平线
        elif stripped == '---':
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_paragraph:
                result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
                paragraph_lines = []
                in_paragraph = False
            result_lines.append('<hr>')
        # 引用
        elif stripped.startswith('> '):
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if in_paragraph:
                result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
                paragraph_lines = []
                in_paragraph = False
            result_lines.append(f'<blockquote>{stripped[2:]}</blockquote>')
        # 列表项
        elif stripped.startswith('- '):
            if in_paragraph:
                result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
                paragraph_lines = []
                in_paragraph = False
            if not in_list:
                result_lines.append('<ul>')
                in_list = True
            content = stripped[2:]
            # 处理内联格式
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', content)
            result_lines.append(f'<li>{content}</li>')
        # 普通段落
        else:
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            # 处理内联格式
            processed_line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
            processed_line = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', processed_line)
            paragraph_lines.append(processed_line)
            in_paragraph = True
        
        i += 1
    
    # 处理结尾
    if in_list:
        result_lines.append('</ul>')
    if in_paragraph:
        result_lines.append('<p>' + ' '.join(paragraph_lines) + '</p>')
    
    return '\n'.join(result_lines)


def generate_html(md_content):
    """生成完整的 HTML 页面"""
    html_body = markdown_to_html(md_content)
    
    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📚 Ebook Treasure Chest</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #24292e;
        }}
        h1, h2, h3, h4 {{
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
        }}
        h1 {{ font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
        h2 {{ font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
        h3 {{ font-size: 1.25em; }}
        h4 {{ font-size: 1em; }}
        a {{
            color: #0366d6;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        blockquote {{
            padding: 0 1em;
            color: #6a737d;
            border-left: 0.25em solid #dfe2e5;
            margin: 0;
        }}
        hr {{
            height: 0.25em;
            padding: 0;
            margin: 24px 0;
            background-color: #e1e4e8;
            border: 0;
        }}
        input {{
            width: 100%;
            padding: 10px;
            font-size: 16px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }}
        #search-results {{
            margin-top: 20px;
        }}
        #search-results p {{
            margin: 10px 0;
        }}
        ul {{
            padding-left: 2em;
        }}
        li {{
            margin: 0.25em 0;
        }}
        p {{
            margin: 16px 0;
        }}
    </style>
</head>
<body>
{content}
</body>
</html>"""
    
    return html_template.format(content=html_body)


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

    md_content = "\n".join(md_parts)
    
    OUTPUT_HTML.parent.mkdir(exist_ok=True)

    # 写 index.html（GitHub Pages 优先查找）
    html_content = generate_html(md_content)
    OUTPUT_HTML.write_text(html_content, encoding="utf-8")

    # 写 books.json（给前端搜索用，作为 metadata 数据的备份）
    OUTPUT_JSON.write_text(
        json.dumps(books, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("✅ index.html & books.json generated")
    
    # 提示：all-books.json 需要单独运行 parse_md_to_json.py 生成
    all_books_file = ROOT / "docs" / "all-books.json"
    if all_books_file.exists():
        print(f"ℹ️  检测到 all-books.json ({all_books_file.stat().st_size / 1024 / 1024:.2f} MB)")
    else:
        print("ℹ️  提示：运行 'python scripts/parse_md_to_json.py' 生成 all-books.json")


if __name__ == "__main__":
    main()
