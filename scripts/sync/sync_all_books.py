#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量同步脚本：备份现有md目录，查找最大书籍ID，然后生成所有书籍的md文件
"""

import sys
import argparse
import os
from pathlib import Path
import subprocess

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 注意：不在这里导入test_batch_sync，因为需要先设置环境变量
from backup_md import backup_md_directory
from find_max_book_id import find_max_book_id_from_homepage, find_max_book_id_by_binary_search


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='全量同步书籍数据')
    parser.add_argument('--max-id', type=int, help='手动指定最大书籍ID（跳过查找步骤）')
    parser.add_argument('--skip-backup', action='store_true', help='跳过备份步骤')
    parser.add_argument('--skip-find-id', action='store_true', help='跳过查找最大ID步骤（需要提供--max-id）')
    parser.add_argument('--start-id', type=int, default=1, help='起始书籍ID（默认：1）')
    parser.add_argument('--batch-size', type=int, help='分批处理大小（例如：20000，每次处理2万本书）。如果不指定，则一次性处理所有书籍')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 全量同步书籍数据")
    print("=" * 80)
    print()
    
    # 步骤1：备份现有md目录
    if not args.skip_backup:
        print("📦 步骤1: 备份现有md目录")
        print("-" * 80)
        backup_path = backup_md_directory()
        if backup_path:
            print(f"✅ 备份完成: {backup_path}\n")
        else:
            print("⚠️  备份失败或目录不存在，继续执行...\n")
    else:
        print("⏭️  跳过备份步骤\n")
    
    # 步骤2：查找最大书籍ID
    max_book_id = None
    if not args.skip_find_id:
        if args.max_id:
            max_book_id = args.max_id
            print(f"📊 使用指定的最大书籍ID: {max_book_id}\n")
        else:
            print("🔍 步骤2: 查找最大书籍ID")
            print("-" * 80)
            # 先尝试从首页快速查找
            max_book_id = find_max_book_id_from_homepage()
            
            # 如果首页没找到，使用二分查找（较慢但准确）
            if not max_book_id:
                print("\n使用二分查找法（较慢但更准确）...")
                max_book_id = find_max_book_id_by_binary_search(start=1, end=100000)
            
            if max_book_id:
                print(f"\n✅ 找到最大书籍ID: {max_book_id}\n")
            else:
                print("\n❌ 未能找到最大书籍ID")
                print("   请手动指定: python3 sync_all_books.py --max-id <ID>")
                return
    else:
        if args.max_id:
            max_book_id = args.max_id
        else:
            print("❌ 错误: 跳过查找ID步骤时必须提供 --max-id")
            return
    
    # 步骤3：生成所有书籍的md文件
    print("📚 步骤3: 生成所有书籍的md文件")
    print("-" * 80)
    print(f"📊 处理范围: ID {args.start_id} - {max_book_id}")
    print(f"📊 预计书籍数量: {max_book_id - args.start_id + 1}")
    
    # 方案3：分批处理支持
    if args.batch_size:
        total_books = max_book_id - args.start_id + 1
        num_batches = (total_books + args.batch_size - 1) // args.batch_size
        print(f"📦 分批处理: 每批 {args.batch_size} 本，共 {num_batches} 批")
    print()
    
    # 设置环境变量，确保使用正式目录md/
    # 必须在导入test_batch_sync之前设置
    os.environ['OUTPUT_DIR'] = 'md'
    
    # 现在导入test_batch_sync（会读取环境变量）
    import test_batch_sync
    import asyncio
    
    print("⏳ 开始处理，这可能需要较长时间...")
    print("💡 提示：可以随时中断（Ctrl+C），下次运行会自动跳过已处理的ID（断点续传）")
    if args.batch_size:
        print(f"💡 分批处理：每批约 {args.batch_size * 0.5 / 60:.1f} 分钟")
    print(f"💡 预计总时间：约 {((max_book_id - args.start_id + 1) * 0.5 / 60):.1f} 分钟（基于0.5秒/请求）")
    print(f"💡 超时保护：600分钟（10小时）\n")
    
    sync_success = False
    try:
        # 方案3：分批处理
        if args.batch_size:
            current_start = args.start_id
            batch_num = 1
            
            while current_start <= max_book_id:
                current_end = min(current_start + args.batch_size - 1, max_book_id)
                
                print("\n" + "=" * 80)
                print(f"📦 批次 {batch_num}: 处理 ID {current_start} - {current_end}")
                print("=" * 80)
                
                # 调用test_batch_sync的main函数，传入当前批次的范围
                asyncio.run(test_batch_sync.main(current_start, current_end))
                
                print(f"\n✅ 批次 {batch_num} 完成")
                
                # 准备下一批
                current_start = current_end + 1
                batch_num += 1
                
                # 如果不是最后一批，稍作停顿
                if current_start <= max_book_id:
                    print("⏸️  批次间暂停 5 秒...")
                    import time
                    time.sleep(5)
        else:
            # 一次性处理所有书籍
            asyncio.run(test_batch_sync.main(args.start_id, max_book_id))
        
        sync_success = True
        print("\n" + "=" * 80)
        print("✅ 全量同步完成！")
        print("=" * 80)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断，已保存进度")
        print("   下次运行时会自动从上次中断的地方继续（断点续传）")
        return
    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
        return
    
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
        
        print("\n" + "=" * 80)
        print("✅ 全量同步及后续更新完成！")
        print("=" * 80)


if __name__ == "__main__":
    main()
