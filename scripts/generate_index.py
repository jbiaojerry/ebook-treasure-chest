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
        lines.append(f"<p class=\"note-text\">💡 注：共 {len(category_counts)} 个分类，以下显示前 {max_categories} 个热门分类的书籍。使用搜索功能可查找所有书籍。</p>\n\n")
        sorted_categories = sorted_categories[:max_categories]

    for category in sorted_categories:
        lines.append(f"<div class=\"category-section\">\n")
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
                    lines.append(f"<p class=\"note-text\">*（共 {len(grouped[category][language][level])} 本，显示前 {max_books_per_section} 本）*</p>\n")

                for b in books_list:
                    formats = ", ".join(b.get("formats", []))
                    author = b.get('author', '未知')
                    lines.append(
                        f"<div class=\"book-item\">\n"
                        f"<strong>{b['title']}</strong>\n"
                        f"<div class=\"book-meta\">👤 {author} ｜ 📥 {formats}</div>\n"
                        f"<a href=\"{b['link']}\" target=\"_blank\" rel=\"noopener\" class=\"book-link\">📥 下载</a>\n"
                        f"</div>\n"
                    )

                lines.append("")
        
        lines.append("</div>\n\n")

    if len(sorted_categories) < len(grouped.keys()):
        lines.append(f"\n<hr>\n\n<p class=\"note-text\">💡 还有 {len(grouped.keys()) - len(sorted_categories)} 个分类未显示，请使用搜索功能查找。</p>\n")

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
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #24292e;
            background: linear-gradient(to bottom, #f6f8fa 0%, #ffffff 200px);
            min-height: 100vh;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 15px;
            }}
        }}
        
        header {{
            background: #ffffff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            margin-bottom: 30px;
        }}
        
        h1 {{
            font-size: 2.5em;
            margin: 0 0 16px 0;
            background: linear-gradient(135deg, #0366d6 0%, #0056b3 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
            text-align: center;
        }}
        
        h2 {{
            font-size: 1.75em;
            margin: 32px 0 20px 0;
            padding-bottom: 12px;
            border-bottom: 3px solid #0366d6;
            color: #24292e;
            font-weight: 600;
            position: relative;
        }}
        
        h2::before {{
            content: "";
            position: absolute;
            left: 0;
            bottom: -3px;
            width: 60px;
            height: 3px;
            background: linear-gradient(90deg, #0366d6, #0056b3);
            border-radius: 2px;
        }}
        
        h3 {{
            font-size: 1.3em;
            margin: 24px 0 12px 0;
            color: #586069;
            font-weight: 500;
        }}
        
        h4 {{
            font-size: 1.1em;
            margin: 16px 0 8px 0;
            color: #6a737d;
            font-weight: 500;
        }}
        
        a {{
            color: #0366d6;
            text-decoration: none;
            transition: all 0.2s ease;
            font-weight: 500;
        }}
        
        a:hover {{
            color: #0056b3;
            text-decoration: underline;
        }}
        
        a:focus {{
            outline: 2px solid #0366d6;
            outline-offset: 2px;
            border-radius: 2px;
        }}
        
        blockquote {{
            padding: 16px 20px;
            color: #586069;
            border-left: 4px solid #0366d6;
            margin: 20px 0;
            background: linear-gradient(to right, #f6f8fa 0%, #ffffff 100%);
            border-radius: 6px;
            font-style: italic;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }}
        
        hr {{
            height: 1px;
            margin: 40px 0;
            background: linear-gradient(90deg, transparent, #e1e4e8, transparent);
            border: 0;
        }}
        
        .search-container {{
            margin: 30px 0;
            position: relative;
            background: #ffffff;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        }}
        
        input[type="text"] {{
            width: 100%;
            padding: 14px 18px;
            font-size: 16px;
            border: 2px solid #d1d9e0;
            border-radius: 8px;
            box-sizing: border-box;
            transition: all 0.3s ease;
            background-color: #ffffff;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }}
        
        input[type="text"]:hover {{
            border-color: #0366d6;
            box-shadow: 0 2px 6px rgba(3, 102, 214, 0.15);
        }}
        
        input[type="text"]:focus {{
            outline: none;
            border-color: #0366d6;
            box-shadow: 0 0 0 4px rgba(3, 102, 214, 0.15), 0 2px 8px rgba(0, 0, 0, 0.1);
            transform: translateY(-1px);
        }}
        
        input[type="text"]::placeholder {{
            color: #959da5;
        }}
        
        .search-hint {{
            margin-top: 12px;
            color: #586069;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            background: #f6f8fa;
            border-radius: 6px;
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
            background: #f6f8fa;
            border-radius: 8px;
        }}
        
        .loading-indicator::before {{
            content: "⏳ ";
            animation: pulse 1.5s ease-in-out infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        ul {{
            padding-left: 0;
            margin: 16px 0;
            list-style: none;
        }}
        
        li {{
            margin: 12px 0;
            padding: 12px 16px;
            background: #ffffff;
            border-left: 3px solid #0366d6;
            border-radius: 6px;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }}
        
        li:hover {{
            transform: translateX(4px);
            box-shadow: 0 2px 8px rgba(3, 102, 214, 0.15);
            border-left-width: 4px;
        }}
        
        li strong {{
            color: #24292e;
            font-size: 1.05em;
        }}
        
        p {{
            margin: 16px 0;
            line-height: 1.7;
        }}
        
        .overview-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        
        .stat-item {{
            padding: 24px;
            background: linear-gradient(135deg, #ffffff 0%, #f6f8fa 100%);
            border-radius: 10px;
            border: 1px solid #e1e4e8;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            transition: all 0.3s ease;
            text-align: center;
        }}
        
        .stat-item:hover {{
            transform: translateY(-4px);
            box-shadow: 0 4px 16px rgba(3, 102, 214, 0.15);
            border-color: #0366d6;
        }}
        
        .stat-item span {{
            display: block;
            font-size: 14px;
            color: #586069;
            margin-bottom: 8px;
            font-weight: 500;
        }}
        
        .stat-item strong {{
            display: block;
            font-size: 1.8em;
            background: linear-gradient(135deg, #0366d6 0%, #0056b3 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
            margin-top: 4px;
        }}
        
        @media (max-width: 600px) {{
            .overview-stats {{
                grid-template-columns: 1fr;
                gap: 16px;
            }}
            
            h1 {{
                font-size: 2em;
            }}
            
            h2 {{
                font-size: 1.5em;
            }}
        }}
        
        .category-section {{
            background: #ffffff;
            padding: 24px;
            margin: 24px 0;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            border: 1px solid #e1e4e8;
            transition: all 0.3s ease;
        }}
        
        .category-section:hover {{
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
            border-color: #0366d6;
        }}
        
        .book-item {{
            padding: 16px;
            margin: 12px 0;
            background: #f6f8fa;
            border-radius: 8px;
            border-left: 4px solid #0366d6;
            transition: all 0.2s ease;
        }}
        
        .book-item:hover {{
            background: #e8f4fd;
            transform: translateX(4px);
            box-shadow: 0 2px 8px rgba(3, 102, 214, 0.1);
        }}
        
        .book-item strong {{
            color: #24292e;
            font-size: 1.05em;
            display: block;
            margin-bottom: 6px;
        }}
        
        .book-item .book-meta {{
            color: #586069;
            font-size: 0.9em;
            margin: 8px 0;
        }}
        
        .book-item .book-link {{
            display: inline-block;
            margin-top: 8px;
            padding: 6px 14px;
            background: #0366d6;
            color: #ffffff !important;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.2s ease;
            text-decoration: none !important;
        }}
        
        .book-item .book-link:hover {{
            background: #0056b3;
            transform: translateY(-1px);
            box-shadow: 0 2px 6px rgba(3, 102, 214, 0.3);
        }}
        
        .note-text {{
            padding: 12px 16px;
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            border-radius: 6px;
            color: #856404;
            font-size: 14px;
            margin: 20px 0;
        }}
        
        .footer-note {{
            margin-top: 60px;
            padding: 24px;
            background: linear-gradient(135deg, #f6f8fa 0%, #ffffff 100%);
            border-radius: 12px;
            text-align: center;
            color: #586069;
            font-size: 14px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            border-top: 3px solid #0366d6;
        }}
        
        .footer-note a {{
            margin: 0 8px;
            padding: 4px 8px;
            border-radius: 4px;
        }}
        
        .footer-note a:hover {{
            background: #e8f4fd;
            text-decoration: none;
        }}
        
        /* 滚动条样式 */
        ::-webkit-scrollbar {{
            width: 10px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #f1f1f1;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: #0366d6;
            border-radius: 5px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: #0056b3;
        }}
    </style>
</head>
<body>
<header>
{content}
</header>

<footer class="footer-note">
    <p>📚 电子书下载宝库 </p>
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
