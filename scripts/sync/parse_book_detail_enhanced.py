#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版书籍详情页解析模块
功能：解析书籍详情页，提取完整信息（包括标签、图片等）
"""

import requests
import re
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Dict, List, Optional

# 尝试导入配置文件，如果不存在则使用环境变量或默认值
try:
    from config import BOOK_SITE_DOMAIN
except ImportError:
    # 如果配置文件不存在，尝试从环境变量读取
    BOOK_SITE_DOMAIN = os.getenv("BOOK_SITE_DOMAIN", "")
    if not BOOK_SITE_DOMAIN:
        # 如果都没有，使用占位符（但会导致功能不可用）
        BOOK_SITE_DOMAIN = ""


def parse_download_page(url: str) -> Optional[Dict[str, str]]:
    """
    解析下载页面，提取诚通网盘的真实下载链接
    
    Args:
        url: 下载页面 URL，例如: "https://www.dushupai.com/download-book-64938.html"
    
    Returns:
        Optional[Dict]: 如果找到诚通网盘下载链接，返回包含 download_url 的字典；
                       如果不存在该下载方式，返回 None
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
        # 发送请求
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 解析 HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 步骤1: 精确定位"诚通网盘下载"区域
        # 方法1: 查找 class="source-title" 且包含"诚通网盘"的 div
        cheng_tong_title = soup.find('div', class_='source-title', string=lambda x: x and '诚通网盘' in str(x) if x else False)
        
        if not cheng_tong_title:
            # 方法2: 查找包含"诚通网盘下载"文本的元素
            cheng_tong_text = soup.find(string=lambda x: x and '诚通网盘下载' in str(x) if x else False)
            if cheng_tong_text:
                # 向上查找包含该文本的 source-title div
                parent = cheng_tong_text.parent
                while parent:
                    if parent.name == 'div' and 'source-title' in str(parent.get('class', [])):
                        cheng_tong_title = parent
                        break
                    if parent.name in ['body', 'html']:
                        break
                    parent = parent.parent
        
        if not cheng_tong_title:
            # 如果找不到"诚通网盘下载"区域，返回 None
            return None
        
        # 步骤2: 找到包含"诚通网盘下载"的容器（通常是 <div class="box">）
        container = cheng_tong_title.parent
        while container:
            # 如果当前容器是 box，使用它
            if container.name == 'div' and 'box' in str(container.get('class', [])):
                break
            
            # 检查当前容器是否包含 button
            button_div = container.find('div', class_='button')
            if button_div:
                # 找到了包含按钮的容器
                break
            
            # 继续向上查找
            container = container.parent
            
            # 如果已经到 body 或 html，停止
            if not container or container.name in ['body', 'html']:
                container = None
                break
        
        if not container:
            return None
        
        # 步骤3: 在容器内查找"立即下载"按钮并提取链接
        # 方法1: 查找 class="button" 的 div 中的链接（最精确）
        button_div = container.find('div', class_='button')
        if button_div:
            download_link = button_div.find('a', href=True)
            if download_link:
                download_url = download_link.get('href', '').strip()
                # 验证是否是 ctfile.com 链接
                if download_url and 'ctfile.com' in download_url.lower():
                    return {
                        "download_url": download_url
                    }
        
        # 方法2: 在容器内查找包含"立即下载"文本的链接
        download_links = container.find_all('a', string=lambda x: x and '立即下载' in str(x) if x else False)
        for link in download_links:
            href = link.get('href', '').strip()
            if href and 'ctfile.com' in href.lower():
                return {
                    "download_url": href
                }
        
        # 方法3: 在容器内查找所有包含 ctfile.com 的链接（最后备用）
        ctfile_links = container.find_all('a', href=lambda x: x and 'ctfile.com' in str(x).lower() if x else False)
        if ctfile_links:
            download_url = ctfile_links[0].get('href', '').strip()
            if download_url:
                return {
                    "download_url": download_url
                }
        
        # 如果都没找到，返回 None
        return None
        
    except requests.exceptions.RequestException as e:
        return None
    except Exception as e:
        return None


def extract_book_id(url: str) -> Optional[str]:
    """
    从URL中提取书籍ID
    
    Args:
        url: 书籍详情页URL，例如: "https://www.dushupai.com/book-content-63067.html"
    
    Returns:
        书籍ID字符串，例如: "63067"
    """
    match = re.search(r'book-content-(\d+)\.html', url)
    if match:
        return match.group(1)
    return None


def parse_book_detail_enhanced(url: str) -> Dict:
    """
    解析书籍详情页，提取完整信息
    
    Args:
        url: 书籍详情页 URL，例如: "https://www.dushupai.com/book-content-63067.html"
    
    Returns:
        Dict: 包含以下字段的字典：
            - book_id: 书籍ID
            - title: 书名
            - author: 作者信息
            - cover_image: 封面图片URL
            - download_page: 下载页面URL
            - download_url: 实际下载链接（需要进一步解析下载页）
            - tags: 标签列表
            - category: 分类
            - isbn: ISBN号
            - rating: 评分
            - publish_date: 发布日期
            - description: 内容简介
            - author_bio: 作者简介
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    result = {
        "book_id": extract_book_id(url) or "",
        "title": "",
        "author": "未知",
        "cover_image": "",
        "download_page": "",
        "download_url": "",
        "tags": [],
        "category": "",
        "isbn": "",
        "rating": "",
        "publish_date": "",
        "description": "",
        "author_bio": "",
        "formats": []
    }
    
    try:
        # 发送请求
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 解析 HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. 提取书名
        title_elem = soup.select_one('h4.post-title')
        if title_elem:
            result["title"] = title_elem.get_text(strip=True)
        
        if not result["title"]:
            post_info = soup.select_one('.post-info')
            if post_info:
                for li in post_info.find_all('li'):
                    strong = li.find('strong')
                    if strong and '书名' in strong.get_text():
                        title_text = li.get_text().replace('书名：', '').strip()
                        if title_text:
                            result["title"] = title_text
                            break
        
        # 2. 提取作者信息
        post_info = soup.select_one('.post-info')
        if post_info:
            for li in post_info.find_all('li'):
                strong = li.find('strong')
                if strong and '作者' in strong.get_text():
                    author_links = li.find_all('a', href=lambda x: x and 'book-author' in str(x) if x else False)
                    if author_links:
                        authors = [link.get_text(strip=True) for link in author_links if link.get_text(strip=True)]
                        if authors:
                            result["author"] = " / ".join(authors)
                    else:
                        author_text = li.get_text().replace('作者：', '').strip()
                        if author_text:
                            result["author"] = author_text
                    break
        
        # 3. 提取封面图片
        img_elem = soup.select_one('.post-content img')
        if img_elem:
            img_src = img_elem.get('src', '')
            if img_src:
                result["cover_image"] = urljoin(url, img_src)
        
        # 4. 提取下载页面URL并解析实际下载链接
        download_elem = soup.select_one('.post-download a')
        if download_elem:
            download_href = download_elem.get('href', '')
            if download_href:
                result["download_page"] = urljoin(url, download_href)
                
                # 解析下载页面，获取诚通网盘的实际下载链接
                try:
                    download_info = parse_download_page(result["download_page"])
                    if download_info and download_info.get("download_url"):
                        result["download_url"] = download_info["download_url"]
                except Exception as e:
                    # 如果解析失败，不影响其他信息的提取
                    pass
        
        # 5. 提取标签列表（关键功能）
        # 方法1：直接查找包含 book-tag 的链接（最可靠）
        tag_links = soup.find_all('a', href=lambda x: x and 'book-tag' in str(x) if x else False)
        if tag_links:
            tags = []
            for link in tag_links:
                tag_text = link.get_text(strip=True)
                # 格式可能是 "中国(5333)" 或 "中国"
                if '(' in tag_text:
                    tag_name = tag_text.split('(')[0].strip()
                else:
                    tag_name = tag_text
                
                # 过滤掉空标签和数字标签（如年份）
                if tag_name and tag_name not in tags:
                    # 跳过纯数字标签（如年份）
                    if not tag_name.isdigit():
                        tags.append(tag_name)
            
            result["tags"] = tags
        
        # 方法2：如果方法1没找到，尝试查找"标签："后面的内容
        if not result["tags"]:
            for elem in soup.find_all(['div', 'p', 'span', 'strong']):
                text = elem.get_text()
                if '标签' in text and ('：' in text or ':' in text):
                    # 查找父元素或兄弟元素中的标签链接
                    parent = elem.find_parent()
                    if parent:
                        tag_links = parent.find_all('a', href=lambda x: x and 'book-tag' in str(x) if x else False)
                        if tag_links:
                            tags = []
                            for link in tag_links:
                                tag_text = link.get_text(strip=True)
                                if '(' in tag_text:
                                    tag_name = tag_text.split('(')[0].strip()
                                else:
                                    tag_name = tag_text
                                if tag_name and tag_name not in tags and not tag_name.isdigit():
                                    tags.append(tag_name)
                            if tags:
                                result["tags"] = tags
                                break
        
        # 6. 提取分类
        category_link = soup.find('a', href=lambda x: x and 'book-category' in str(x) if x else False)
        if category_link:
            result["category"] = category_link.get_text(strip=True)
        
        # 7. 提取其他信息（ISBN、评分、发布日期等）
        if post_info:
            for li in post_info.find_all('li'):
                strong = li.find('strong')
                if not strong:
                    continue
                
                strong_text = strong.get_text()
                li_text = li.get_text()
                
                if 'ISBN' in strong_text:
                    result["isbn"] = li_text.replace('ISBN：', '').replace('ISBN:', '').strip()
                elif '评分' in strong_text:
                    rating_text = li_text.replace('评分：', '').replace('评分:', '').strip()
                    result["rating"] = rating_text
                elif '时间' in strong_text or '日期' in strong_text:
                    date_text = li_text.replace('时间：', '').replace('日期：', '').strip()
                    result["publish_date"] = date_text
                elif '格式' in strong_text:
                    formats_text = li_text.replace('格式：', '').replace('格式:', '').strip()
                    result["formats"] = [f.strip() for f in formats_text.split(',') if f.strip()]
        
        # 8. 提取内容简介
        desc_elem = soup.find(string=re.compile(r'内容简介'))
        if desc_elem:
            # 查找简介内容（通常在"内容简介"后面的元素中）
            parent = desc_elem.find_parent()
            if parent:
                # 查找下一个兄弟元素或父元素中的文本
                desc_text = ""
                for sibling in parent.next_siblings:
                    if hasattr(sibling, 'get_text'):
                        desc_text = sibling.get_text(strip=True)
                        if desc_text:
                            break
                
                if not desc_text:
                    # 尝试从父元素中提取
                    desc_text = parent.get_text(strip=True)
                    # 去掉"内容简介："前缀
                    desc_text = re.sub(r'内容简介[：:]?\s*', '', desc_text)
                
                result["description"] = desc_text[:500]  # 限制长度
        
        # 9. 提取作者简介
        author_bio_elem = soup.find(string=re.compile(r'作者简介'))
        if author_bio_elem:
            parent = author_bio_elem.find_parent()
            if parent:
                bio_text = ""
                for sibling in parent.next_siblings:
                    if hasattr(sibling, 'get_text'):
                        bio_text = sibling.get_text(strip=True)
                        if bio_text:
                            break
                
                if not bio_text:
                    bio_text = parent.get_text(strip=True)
                    bio_text = re.sub(r'作者简介[：:]?\s*', '', bio_text)
                
                result["author_bio"] = bio_text[:300]  # 限制长度
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return result
    except Exception as e:
        print(f"❌ 解析过程出错: {e}")
        import traceback
        traceback.print_exc()
        return result


def main():
    """主函数：测试增强版解析功能"""
    print("=" * 80)
    print("📚 测试增强版 parse_book_detail_enhanced 功能")
    print("=" * 80)
    
    # 测试 URL
    test_url = "https://www.dushupai.com/book-content-63067.html"
    
    print(f"\n📄 测试 URL: {test_url}\n")
    
    # 解析书籍详情
    result = parse_book_detail_enhanced(test_url)
    
    # 显示结果
    print("📋 解析结果：")
    print("-" * 80)
    print(f"书籍ID: {result['book_id']}")
    print(f"书名: {result['title']}")
    print(f"作者: {result['author']}")
    print(f"封面图片: {result['cover_image']}")
    print(f"下载页面: {result['download_page']}")
    print(f"标签: {', '.join(result['tags']) if result['tags'] else '无'}")
    print(f"分类: {result['category']}")
    print(f"ISBN: {result['isbn']}")
    print(f"评分: {result['rating']}")
    print(f"发布日期: {result['publish_date']}")
    print(f"格式: {', '.join(result['formats']) if result['formats'] else '无'}")
    print(f"简介: {result['description'][:100]}..." if result['description'] else "无简介")
    
    # 显示 JSON 格式
    print("\n📋 JSON 格式：")
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)
    
    return result


if __name__ == "__main__":
    result = main()
