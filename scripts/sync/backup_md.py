#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份现有的md目录
"""

import shutil
from pathlib import Path
from datetime import datetime
import sys

ROOT = Path(__file__).parent.parent.parent
MD_DIR = ROOT / "md"
BACKUP_DIR = ROOT / "md_backup"


def backup_md_directory():
    """备份md目录"""
    print("=" * 80)
    print("📦 备份md目录")
    print("=" * 80)
    print()
    
    if not MD_DIR.exists():
        print(f"⚠️  md目录不存在: {MD_DIR}")
        print("   无需备份")
        return None
    
    # 创建备份目录（带时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"md_backup_{timestamp}"
    
    print(f"📁 源目录: {MD_DIR}")
    print(f"📁 备份目录: {backup_path}")
    
    try:
        # 创建备份目录的父目录
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 复制目录
        print("\n⏳ 正在备份...")
        shutil.copytree(MD_DIR, backup_path)
        
        # 统计文件数量
        md_files = list(backup_path.glob("*.md"))
        json_files = list(backup_path.glob("*.json"))
        
        print(f"\n✅ 备份完成！")
        print(f"  - MD文件数: {len(md_files)}")
        print(f"  - JSON文件数: {len(json_files)}")
        print(f"  - 备份路径: {backup_path}")
        
        return backup_path
        
    except Exception as e:
        print(f"\n❌ 备份失败: {e}")
        return None


if __name__ == "__main__":
    backup_path = backup_md_directory()
    if backup_path:
        print(f"\n💾 备份已保存到: {backup_path}")
