#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找读书站中现有的最大书籍ID
通过检查"最新书籍"页面来找到最大ID
"""

import requests
import re
from bs4 import BeautifulSoup
from typing import Optional
import os
import sys

# 尝试导入配置
try:
    from config import BOOK_SITE_DOMAIN
except ImportError:
    BOOK_SITE_DOMAIN = os.getenv("BOOK_SITE_DOMAIN", "")
    if not BOOK_SITE_DOMAIN:
        print("❌ 错误: 未配置 BOOK_SITE_DOMAIN")
        print("请设置环境变量或创建 config.py")
        sys.exit(1)


def extract_book_id_from_url(url: str) -> Optional[int]:
    """从URL中提取书籍ID"""
    match = re.search(r'book-content-(\d+)\.html', url)
    if match:
        return int(match.group(1))
    return None


def find_max_book_id_from_homepage() -> Optional[int]:
    """
    从首页的"最新书籍"列表中查找最大书籍ID
    
    Returns:
        最大书籍ID，如果未找到返回None
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        # 访问首页
        url = f"{BOOK_SITE_DOMAIN}/"
        print(f"📄 正在访问首页: {url}")
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找所有包含 book-content 的链接
        book_links = soup.find_all('a', href=re.compile(r'book-content-\d+\.html'))
        
        max_id = 0
        found_ids = []
        
        for link in book_links:
            href = link.get('href', '')
            book_id = extract_book_id_from_url(href)
            if book_id:
                found_ids.append(book_id)
                if book_id > max_id:
                    max_id = book_id
        
        if max_id > 0:
            print(f"✅ 从首页找到 {len(found_ids)} 个书籍链接")
            print(f"📊 最大书籍ID: {max_id}")
            return max_id
        else:
            print("⚠️  首页未找到书籍链接")
            return None
            
    except Exception as e:
        print(f"❌ 访问首页失败: {e}")
        return None


def find_max_book_id_by_binary_search(start: int = 1, end: int = 100000) -> Optional[int]:
    """
    使用二分查找法找到最大有效的书籍ID
    
    Args:
        start: 起始ID
        end: 结束ID（预估的最大值）
    
    Returns:
        最大有效的书籍ID
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    def check_book_exists(book_id: int) -> bool:
        """检查书籍ID是否存在"""
        url = f"{BOOK_SITE_DOMAIN}/book-content-{book_id}.html"
        try:
            response = requests.head(url, headers=headers, timeout=5, allow_redirects=False)
            return response.status_code == 200
        except:
            return False
    
    print(f"🔍 使用二分查找法查找最大书籍ID (范围: {start} - {end})")
    
    left, right = start, end
    max_valid_id = 0
    
    # 先快速找到一个大致的上限
    print("📊 步骤1: 快速定位大致范围...")
    step = 1000
    current = start
    while current <= end:
        if check_book_exists(current):
            max_valid_id = current
            current += step
        else:
            break
        if current % 10000 == 0:
            print(f"   已检查到 ID: {current}")
    
    if max_valid_id == 0:
        print("⚠️  未找到任何有效书籍ID")
        return None
    
    print(f"✅ 找到大致范围，最大ID约在: {max_valid_id}")
    
    # 在找到的范围内进行精确查找
    print("📊 步骤2: 精确查找最大ID...")
    left = max_valid_id
    right = min(max_valid_id + step * 2, end)
    
    while left <= right:
        mid = (left + right) // 2
        if check_book_exists(mid):
            max_valid_id = mid
            left = mid + 1
        else:
            right = mid - 1
        
        if (left + right) // 2 % 100 == 0:
            print(f"   当前范围: {left} - {right}, 最大有效ID: {max_valid_id}")
    
    return max_valid_id


def find_max_book_id_from_latest_books(max_pages: int = 10) -> Optional[int]:
    """
    从"最新书籍"页面查找最大书籍ID（通过分页）
    
    Args:
        max_pages: 最多检查的页数
    
    Returns:
        最大书籍ID
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    max_id = 0
    page = 1
    
    print(f"📄 正在检查最新书籍页面（最多 {max_pages} 页）...")
    
    while page <= max_pages:
        # 构建URL（首页是 /，后续可能是分页）
        if page == 1:
            url = f"{BOOK_SITE_DOMAIN}/"
        else:
            # 尝试不同的分页格式
            url = f"{BOOK_SITE_DOMAIN}/book-{page}.html"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                break
            
            soup = BeautifulSoup(response.text, 'html.parser')
            book_links = soup.find_all('a', href=re.compile(r'book-content-\d+\.html'))
            
            if not book_links:
                break
            
            page_max_id = 0
            for link in book_links:
                href = link.get('href', '')
                book_id = extract_book_id_from_url(href)
                if book_id and book_id > page_max_id:
                    page_max_id = book_id
            
            if page_max_id > max_id:
                max_id = page_max_id
                print(f"   第 {page} 页: 最大ID = {page_max_id}")
            
            page += 1
            
        except Exception as e:
            print(f"⚠️  检查第 {page} 页时出错: {e}")
            break
    
    if max_id > 0:
        print(f"✅ 从最新书籍页面找到最大ID: {max_id}")
        return max_id
    else:
        print("⚠️  未从最新书籍页面找到有效ID")
        return None


def main():
    """主函数：查找最大书籍ID"""
    print("=" * 80)
    print("🔍 查找读书站最大书籍ID")
    print("=" * 80)
    print()
    
    # 方法1：从首页查找（最快）
    print("方法1: 从首页查找...")
    max_id = find_max_book_id_from_homepage()
    
    if max_id:
        print(f"\n✅ 找到最大书籍ID: {max_id}")
        return max_id
    
    # 方法2：从最新书籍页面查找
    print("\n方法2: 从最新书籍页面查找...")
    max_id = find_max_book_id_from_latest_books(max_pages=5)
    
    if max_id:
        print(f"\n✅ 找到最大书籍ID: {max_id}")
        return max_id
    
    # 方法3：使用二分查找（最可靠但较慢）
    print("\n方法3: 使用二分查找法（较慢但更准确）...")
    max_id = find_max_book_id_by_binary_search(start=1, end=100000)
    
    if max_id:
        print(f"\n✅ 找到最大书籍ID: {max_id}")
        return max_id
    
    print("\n❌ 未能找到最大书籍ID")
    return None


if __name__ == "__main__":
    max_id = main()
    if max_id:
        print(f"\n📝 建议：使用 ID 范围 1-{max_id} 进行全量同步")
        # 保存到文件
        with open("max_book_id_found.txt", "w") as f:
            f.write(str(max_id))
        print(f"💾 最大ID已保存到: max_book_id_found.txt")
