#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新README.md中的"热门分类"章节
根据md目录下的所有md文件生成热门分类列表
"""

import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent.parent
README_FILE = ROOT / "README.md"
MD_DIR = ROOT / "md"


def count_books_in_md_file(md_file: Path) -> int:
    """统计md文件中的书籍数量"""
    try:
        content = md_file.read_text(encoding='utf-8')
        # 计算表格行数（排除表头）
        lines = content.split('\n')
        count = 0
        in_table = False
        for line in lines:
            if '| 书名' in line or '书名 |' in line:
                in_table = True
                continue
            if in_table and line.strip().startswith('|') and '---' not in line:
                # 检查是否是数据行（包含下载链接）
                if '[下载](' in line:
                    count += 1
        return count
    except Exception as e:
        print(f"⚠️  读取文件失败 {md_file}: {e}")
        return 0


def get_all_categories() -> dict:
    """获取所有分类及其书籍数量"""
    categories = {}
    
    if not MD_DIR.exists():
        print(f"⚠️  md目录不存在: {MD_DIR}")
        return categories
    
    md_files = list(MD_DIR.glob("*.md"))
    
    # 排除热门分类.md文件本身
    md_files = [f for f in md_files if f.name != "热门分类.md"]
    
    for md_file in md_files:
        category = md_file.stem  # 去掉.md扩展名
        count = count_books_in_md_file(md_file)
        if count > 0:
            categories[category] = count
    
    return categories


def generate_hot_categories_section(categories: dict) -> str:
    """生成热门分类章节内容"""
    # 按书籍数量排序
    sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    
    lines = []
    lines.append("## 🔥 热门分类")
    lines.append("")
    
    # 每行8个标签
    items_per_line = 8
    for i in range(0, len(sorted_categories), items_per_line):
        batch = sorted_categories[i:i + items_per_line]
        line_items = []
        
        for category, count in batch:
            link = f"- [{category}({count})](md/{category}.md)"
            line_items.append(link)
        
        # 用 | 分隔，每行8个
        line = "  | ".join(line_items)
        lines.append(line)
    
    return '\n'.join(lines)


def update_readme():
    """更新README.md中的热门分类章节"""
    if not README_FILE.exists():
        print(f"❌ README.md不存在: {README_FILE}")
        return False
    
    # 读取README内容
    content = README_FILE.read_text(encoding='utf-8')
    
    # 获取所有分类
    print("📊 正在统计分类...")
    categories = get_all_categories()
    print(f"✅ 找到 {len(categories)} 个分类")
    
    if not categories:
        print("⚠️  未找到任何分类，跳过更新")
        return False
    
    # 生成新的热门分类章节
    new_section = generate_hot_categories_section(categories)
    
    # 查找并替换"热门分类"章节
    # 匹配从 "## 🔥 热门分类" 开始到下一个 "##" 或文件结尾
    # 使用更宽松的匹配：允许不同的空行数量
    pattern = r'(## 🔥 热门分类\s*\n\s*\n)(.*?)(?=\n\s*## |\Z)'
    
    match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
    if match:
        # 替换匹配的内容
        new_content = re.sub(pattern, r'\1' + new_section, content, flags=re.DOTALL | re.MULTILINE)
        
        # 写入文件
        README_FILE.write_text(new_content, encoding='utf-8')
        print(f"✅ README.md已更新")
        print(f"   - 分类数量: {len(categories)}")
        print(f"   - 总书籍数: {sum(categories.values())}")
        return True
    else:
        print("⚠️  未找到'热门分类'章节，无法更新")
        return False


if __name__ == "__main__":
    print("=" * 80)
    print("📝 更新README.md热门分类章节")
    print("=" * 80)
    print()
    
    success = update_readme()
    
    if success:
        print("\n✅ 更新完成！")
    else:
        print("\n❌ 更新失败！")
        exit(1)
