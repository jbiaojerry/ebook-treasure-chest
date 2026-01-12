#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量同步脚本：比较已更新的最大书籍ID和读书站的最大ID，只处理新增书籍
"""

import sys
import os
from pathlib import Path
import asyncio

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 设置环境变量，确保使用正式目录md/
# 必须在导入test_batch_sync之前设置
os.environ['OUTPUT_DIR'] = 'md'

# 导入test_batch_sync（必须在设置环境变量后）
from find_max_book_id import find_max_book_id_from_homepage
from test_batch_sync import load_max_book_id, main as sync_main


async def incremental_sync():
    """执行增量同步"""
    print("=" * 80)
    print("🔄 增量同步书籍数据")
    print("=" * 80)
    print()
    
    # 步骤1：获取已更新的最大书籍ID
    print("📊 步骤1: 获取已更新的最大书籍ID")
    print("-" * 80)
    last_max_id = load_max_book_id()
    
    if last_max_id == 0:
        print("⚠️  未找到已更新的最大ID，将执行全量同步")
        print("   建议先运行全量同步脚本")
        return False
    
    print(f"✅ 已更新的最大书籍ID: {last_max_id}")
    print()
    
    # 步骤2：查找读书站当前的最大ID
    print("🔍 步骤2: 查找读书站当前的最大ID")
    print("-" * 80)
    current_max_id = find_max_book_id_from_homepage()
    
    if not current_max_id:
        print("❌ 未能找到读书站的最大ID")
        return False
    
    print(f"✅ 读书站当前最大ID: {current_max_id}")
    print()
    
    # 步骤3：比较并确定需要同步的范围
    if current_max_id <= last_max_id:
        print("✅ 没有新书籍需要同步")
        print(f"   当前最大ID: {current_max_id}")
        print(f"   已更新最大ID: {last_max_id}")
        return True
    
    new_books_count = current_max_id - last_max_id
    print(f"📚 步骤3: 发现 {new_books_count} 本新书籍需要同步")
    print(f"   同步范围: ID {last_max_id + 1} - {current_max_id}")
    print()
    
    # 步骤4：执行同步
    print("⏳ 开始同步新书籍...")
    sync_success = False
    try:
        await sync_main(last_max_id + 1, current_max_id)
        sync_success = True
        print("\n" + "=" * 80)
        print("✅ 增量同步完成！")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ 同步失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 只有同步成功才更新README和all_books.json
    if sync_success:
        print("\n" + "=" * 80)
        print("📝 步骤4: 更新README.md和all_books.json")
        print("=" * 80)
        print()
        
        # 更新README.md的热门分类章节
        print("📝 更新README.md热门分类章节...")
        try:
            from update_readme_hot_categories import update_readme
            if update_readme():
                print("✅ README.md已更新")
            else:
                print("⚠️  README.md更新失败，但继续执行")
        except Exception as e:
            print(f"⚠️  更新README.md失败: {e}")
        
        # 生成all_books.json
        print("\n📝 生成all_books.json...")
        try:
            import subprocess
            result = subprocess.run(
                ["python3", str(Path(__file__).parent.parent.parent / "scripts" / "parse_md_to_json.py")],
                cwd=str(Path(__file__).parent.parent.parent),
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ all_books.json已生成")
                if result.stdout:
                    print(result.stdout)
            else:
                print(f"⚠️  生成all_books.json失败: {result.stderr}")
        except Exception as e:
            print(f"⚠️  生成all_books.json失败: {e}")
    
    return sync_success


if __name__ == "__main__":
    success = asyncio.run(incremental_sync())
    exit(0 if success else 1)
