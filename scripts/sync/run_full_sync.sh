#!/bin/bash
# 全量同步一键执行脚本

cd "$(dirname "$0")"

echo "=========================================="
echo "🚀 全量同步书籍数据"
echo "=========================================="
echo ""

# 检查配置文件
if [ ! -f "config.py" ]; then
    echo "⚠️  配置文件不存在，正在创建..."
    cp config.py.example config.py
    echo "✅ 已创建 config.py，请编辑并设置 BOOK_SITE_DOMAIN"
    echo ""
    read -p "按回车键继续（确保已配置config.py）..."
fi

# 执行全量同步
echo "开始执行全量同步..."
python3 sync_all_books.py

echo ""
echo "=========================================="
echo "✅ 执行完成"
echo "=========================================="
