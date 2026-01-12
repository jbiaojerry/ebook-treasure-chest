import yaml
import json
import re
from collections import defaultdict
from pathlib import Path

# 路径定义
ROOT = Path(__file__).parent.parent
BOOKS_FILE = ROOT / "metadata" / "books.yaml"
ALL_BOOKS_FILE = ROOT / "docs" / "all-books.json"
STATS_FILE = ROOT / "docs" / "parse-stats.json"
OUTPUT_HTML = ROOT / "docs" / "index.html"
OUTPUT_JSON = ROOT / "docs" / "books.json"


def load_books():
    """优先从 all-books.json 加载真实数据，如果不存在则从 metadata/books.yaml 加载"""
    # 优先加载 all-books.json（包含所有 md 文件的数据）
    if ALL_BOOKS_FILE.exists():
        try:
            with open(ALL_BOOKS_FILE, "r", encoding="utf-8") as f:
                books = json.load(f)
                print(f"✅ 从 all-books.json 加载了 {len(books)} 本书籍")
                return books
        except Exception as e:
            print(f"⚠️  加载 all-books.json 失败: {e}，降级到 metadata/books.yaml")
    
    # 降级到 metadata/books.yaml
    if BOOKS_FILE.exists():
        with open(BOOKS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            books = data.get("books", [])
            print(f"ℹ️  从 metadata/books.yaml 加载了 {len(books)} 本书籍（示例数据）")
            return books
    
    print("⚠️  未找到书籍数据文件")
    return []


def load_stats():
    """加载统计信息"""
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  加载统计信息失败: {e}")
    return None


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


def render_overview(total_books, total_categories, languages, levels):
    # 格式化数字
    books_display = f"{total_books:,}" if total_books > 1000 else str(total_books)
    cats_display = f"{total_categories:,}" if total_categories > 1000 else str(total_categories)
    
    # 语言显示
    lang_display = " / ".join(sorted(languages)) if languages else "中文 / 英文"
    
    return f"""## 📊 统计概览

<div class="overview-stats">
<div class="stat-item">
<span>📘 总书籍数</span>
<strong id="total-books">{books_display}</strong>
</div>
<div class="stat-item">
<span>📂 分类数量</span>
<strong id="total-categories">{cats_display}</strong>
</div>
<div class="stat-item">
<span>🌍 支持语言</span>
<strong>{lang_display}</strong>
</div>
<div class="stat-item">
<span>📥 支持格式</span>
<strong>EPUB / MOBI / AZW3</strong>
</div>
</div>
"""


def render_search_ui():
    # 直接写 HTML（GitHub Pages 支持）
    return """## 🔍 搜索书籍

<div class="search-container">
  <input
    type="text"
    id="search-input"
    placeholder="搜索 书名 / 作者 / 分类（支持多关键词，用空格分隔）"
    oninput="onSearch(event)"
    aria-label="搜索书籍"
    autocomplete="off"
  />
  <div class="search-hint">
    <span>💡</span>
    <span>支持搜索书名、作者、分类，可输入多个关键词（用空格分隔）</span>
  </div>
</div>

<div id="search-results" role="region" aria-live="polite" aria-label="搜索结果">
  <div class="loading-indicator">正在加载书籍数据...</div>
</div>

<script src="search.js"></script>
"""


def render_content(grouped, stats=None):
    lines = []
    
    # 计算每个分类的书籍数量
    category_counts = {}
    for category, languages in grouped.items():
        count = sum(len(books) for lang_dict in languages.values() for books in lang_dict.values())
        category_counts[category] = count
    
    # 按书籍数量排序，优先显示热门分类
    sorted_categories = sorted(category_counts.keys(), key=lambda x: category_counts[x], reverse=True)
    
    # 优先显示用户指定的热门分类
    priority_categories = ["文学", "沟通", "励志", "经典", "历史", "科普", "管理", "社会", "推理", "经济", "哲学", "传记"]
    
    # 重新排序：优先分类在前，然后按数量排序
    priority_set = set(priority_categories)
    priority_list = [cat for cat in priority_categories if cat in sorted_categories]
    other_list = [cat for cat in sorted_categories if cat not in priority_set]
    sorted_categories = priority_list + other_list
    
    # 限制显示的分类数量（避免页面过长）
    max_categories = 20
    if len(sorted_categories) > max_categories:
        lines.append(f"*注：共 {len(category_counts)} 个分类，以下显示前 {max_categories} 个热门分类的书籍。使用搜索功能可查找所有书籍。*\n\n")
        sorted_categories = sorted_categories[:max_categories]

    for category in sorted_categories:
        lines.append(f"## 📂 {category}\n")

        for language in sorted(grouped[category].keys()):
            lines.append(f"### 🌍 Language: {language}\n")

            for level in sorted(grouped[category][language].keys()):
                lines.append(f"#### ⭐ Level: {level}\n")

                books_list = grouped[category][language][level]
                # 每个分类-语言-级别组合最多显示10本书
                max_books_per_section = 10
                if len(books_list) > max_books_per_section:
                    books_list = books_list[:max_books_per_section]
                    lines.append(f"*（共 {len(grouped[category][language][level])} 本，显示前 {max_books_per_section} 本）*\n")

                for b in books_list:
                    formats = ", ".join(b.get("formats", []))
                    lines.append(
                        f"- **{b['title']}** — {b.get('author', '未知')}  \n"
                        f"  格式：{formats} ｜ "
                        f"[下载链接]({b['link']})\n"
                    )

                lines.append("")
        
        lines.append("")

    if len(sorted_categories) < len(grouped.keys()):
        lines.append(f"\n---\n\n*还有 {len(grouped.keys()) - len(sorted_categories)} 个分类未显示，请使用搜索功能查找。*\n")

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
    
    # 尝试加载统计信息并生成更新脚本
    stats_info = ""
    try:
        stats_file = ROOT / "docs" / "parse-stats.json"
        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                stats_info = f"""
<script>
// 更新统计信息（从 parse-stats.json）
(function() {{
    const stats = {json.dumps(stats, ensure_ascii=False)};
    const totalBooksEl = document.getElementById('total-books');
    const totalCatsEl = document.getElementById('total-categories');
    if (totalBooksEl && stats.total_books) {{
        totalBooksEl.textContent = stats.total_books.toLocaleString() + ' 本';
    }}
    if (totalCatsEl && stats.categories_count) {{
        totalCatsEl.textContent = stats.categories_count.toLocaleString() + ' 个';
    }}
}})();
</script>"""
    except Exception as e:
        print(f"⚠️  生成统计信息脚本失败: {e}")
    
    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="电子书下载宝库 - 汇聚24,000+本电子书，涵盖文学、历史、科普、管理、技术等各个领域。支持epub、mobi、azw3格式，完全免费。">
    <meta name="keywords" content="电子书下载,免费电子书,epub下载,mobi下载,azw3下载,电子书资源,文学电子书,历史电子书">
    <meta name="author" content="ebook-treasure-chest">
    <meta name="robots" content="index, follow">
    
    <!-- Open Graph -->
    <meta property="og:title" content="📚 电子书下载宝库 - Ebook Treasure Chest">
    <meta property="og:description" content="汇聚24,000+本电子书，涵盖文学、历史、科普、管理、技术等各个领域">
    <meta property="og:type" content="website">
    
    <!-- Preload critical resources -->
    <link rel="preload" href="all-books.json" as="fetch" crossorigin>
    <link rel="preload" href="search.js" as="script">
    
    <title>📚 电子书下载宝库 - Ebook Treasure Chest</title>
    <style>
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, "Microsoft YaHei", sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #24292e;
            background-color: #ffffff;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
        }}
        
        h1, h2, h3, h4 {{
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
        }}
        
        h1 {{
            font-size: 2em;
            border-bottom: 2px solid #eaecef;
            padding-bottom: 0.3em;
            margin-top: 0;
        }}
        
        h2 {{
            font-size: 1.5em;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
        }}
        
        h3 {{ font-size: 1.25em; }}
        h4 {{ font-size: 1em; }}
        
        a {{
            color: #0366d6;
            text-decoration: none;
            transition: color 0.2s ease;
        }}
        
        a:hover {{
            text-decoration: underline;
            color: #0056b3;
        }}
        
        a:focus {{
            outline: 2px solid #0366d6;
            outline-offset: 2px;
        }}
        
        blockquote {{
            padding: 12px 16px;
            color: #6a737d;
            border-left: 0.25em solid #dfe2e5;
            margin: 16px 0;
            background-color: #f6f8fa;
            border-radius: 4px;
        }}
        
        hr {{
            height: 0.25em;
            padding: 0;
            margin: 32px 0;
            background-color: #e1e4e8;
            border: 0;
            border-radius: 2px;
        }}
        
        .search-container {{
            margin: 24px 0;
            position: relative;
        }}
        
        input[type="text"] {{
            width: 100%;
            padding: 12px 16px;
            font-size: 16px;
            border: 2px solid #0366d6;
            border-radius: 6px;
            box-sizing: border-box;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
            background-color: #fff;
        }}
        
        input[type="text"]:focus {{
            outline: none;
            border-color: #0056b3;
            box-shadow: 0 0 0 3px rgba(3, 102, 214, 0.1);
        }}
        
        input[type="text"]::placeholder {{
            color: #959da5;
        }}
        
        .search-hint {{
            margin-top: 10px;
            color: #586069;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        #search-results {{
            margin-top: 24px;
            min-height: 50px;
        }}
        
        .loading-indicator {{
            text-align: center;
            padding: 40px 20px;
            color: #586069;
            font-size: 16px;
        }}
        
        .loading-indicator::before {{
            content: "⏳ ";
        }}
        
        ul {{
            padding-left: 2em;
            margin: 16px 0;
        }}
        
        li {{
            margin: 0.5em 0;
        }}
        
        p {{
            margin: 16px 0;
        }}
        
        .overview-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }}
        
        .stat-item {{
            padding: 16px;
            background: #f6f8fa;
            border-radius: 6px;
            border: 1px solid #e1e4e8;
        }}
        
        .stat-item strong {{
            display: block;
            font-size: 1.2em;
            color: #0366d6;
            margin-top: 4px;
        }}
        
        @media (max-width: 600px) {{
            .overview-stats {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .footer-note {{
            margin-top: 40px;
            padding: 16px;
            background: #f6f8fa;
            border-radius: 6px;
            text-align: center;
            color: #586069;
            font-size: 14px;
        }}
    </style>
</head>
<body>
<header>
{content}
</header>

<footer class="footer-note">
    <p>📚 电子书下载宝库 | 自动生成，请勿手动修改</p>
    <p style="margin-top: 8px; font-size: 12px;">
        <a href="https://github.com/jbiaojerry/ebook-treasure-chest" target="_blank" rel="noopener">GitHub 仓库</a> |
        <a href="README.md" target="_blank">使用说明</a>
    </p>
</footer>
{stats_script}
</body>
</html>"""
    
    return html_template.format(content=html_body, stats_script=stats_info)


def main():
    books = load_books()
    stats = load_stats()
    
    # 如果有统计信息，使用统计信息中的数据
    if stats:
        total_books = stats.get("total_books", len(books))
        total_categories = stats.get("categories_count", len(set(b.get("category", "") for b in books)))
    else:
        total_books = len(books)
        total_categories = len(set(b.get("category", "") for b in books))
    
    grouped, categories, languages, levels = group_books(books)
    
    # 使用统计信息中的分类数量（如果可用）
    if stats and "categories_count" in stats:
        categories_count = stats["categories_count"]
    else:
        categories_count = len(categories)

    md_parts = []
    md_parts.append("# 📚 Ebook Treasure Chest\n")
    md_parts.append("> 自动生成，请勿手动修改\n\n---\n")
    md_parts.append(render_overview(total_books, categories_count, languages, levels))
    md_parts.append("\n---\n")
    md_parts.append(render_search_ui())
    md_parts.append("\n---\n")
    md_parts.append(render_content(grouped, stats))

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
