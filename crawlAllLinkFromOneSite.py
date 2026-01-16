import requests
import time
import random
import json
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


def fetch_html(url: str, timeout: int = 15) -> str | None:
    """
    访问 URL 并返回 HTML
    """
    logging.debug(f"开始获取页面: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        
        # 检查内容类型
        content_type = resp.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type and 'application/xhtml' not in content_type:
            logging.warning(f"非 HTML 内容类型: {content_type}")
            # 不是HTML也尝试继续，但记录警告
        
        # 使用 apparent_encoding 来更准确地检测编码
        # 这会分析内容本身来判断编码，而不是仅依赖 HTTP 头
        if resp.encoding and resp.apparent_encoding:
            if resp.encoding.lower() != resp.apparent_encoding.lower():
                logging.debug(f"检测到编码不一致: HTTP头={resp.encoding}, 实际={resp.apparent_encoding}")
                resp.encoding = resp.apparent_encoding
        elif resp.apparent_encoding:
            resp.encoding = resp.apparent_encoding
        
        logging.debug(f"成功获取页面: {url}, 状态码: {resp.status_code}, 编码: {resp.encoding}")
        return resp.text
    except Exception as e:
        logging.error(f"获取页面失败: {url} -> {e}")
        return None


def should_filter_url(url: str) -> bool:
    """
    判断URL是否应该被过滤
    返回 True 表示过滤（跳过），返回 False 表示不过滤（保留）
    
    逻辑：
    - 无扩展名 -> False（不过滤）
    - 有扩展名且为 .html/.htm -> False（不过滤）
    - 其他情况 -> True（过滤）
    """
    parsed = urlparse(url)
    path = parsed.path
    
    # 获取路径的最后部分
    if '/' in path:
        last_part = path.split('/')[-1]
    else:
        last_part = path
    
    # 如果没有点号，说明无扩展名
    if '.' not in last_part:
        return False
    
    # 获取扩展名（转为小写）
    ext = last_part.split('.')[-1].lower()
    
    # 如果是 html 或 htm，不过滤
    if ext in ['html', 'htm']:
        return False
    
    # 其他情况都过滤
    logging.debug(f"过滤URL（扩展名: .{ext}）: {url}")
    return True


def extract_links(html: str, base_url: str) -> list[dict]:
    """
    从 HTML 中提取所有链接（包括站内和站外）
    return: [{url: xxx, title: xxx, is_external: bool}]
    """
    logging.debug(f"开始提取链接，基础URL: {base_url}")
    
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception as e:
        logging.error(f"BeautifulSoup 解析失败: {base_url} -> {e}")
        logging.debug(f"HTML 内容前 200 字符: {html[:200] if html else 'None'}")
        return []
    
    results = []

    base_domain = urlparse(base_url).netloc
    logging.debug(f"基础域名: {base_domain}")

    for a in soup.find_all("a", href=True):
        href = a.get("href").strip()

        # 跳过锚点、JS、空链接
        if href.startswith(("#", "javascript:", "mailto:")):
            continue

        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        # 跳过没有域名的链接
        if not parsed.netloc:
            continue

        clean_url = parsed.scheme + "://" + parsed.netloc + parsed.path
        
        # 过滤不需要的URL
        if should_filter_url(clean_url):
            continue

        title = a.get_text(strip=True)
        if not title:
            title = soup.title.string.strip() if soup.title else ""

        # 判断是否为站外链接
        is_external = parsed.netloc != base_domain

        results.append({
            "url": clean_url,
            "title": title,
            "is_external": is_external
        })

    internal_count = sum(1 for r in results if not r["is_external"])
    external_count = len(results) - internal_count
    logging.debug(f"从 {base_url} 提取到 {internal_count} 个站内链接, {external_count} 个站外链接")
    return results


def crawl_site(start_url: str, output_file: str = "sitemap.json"):
    logging.info(f"开始爬取网站: {start_url}")
    pages = []
    visited = set()
    external_links = []  # 存储站外链接
    
    # 创建链接日志文件
    link_log_file = "discovered_links.log"
    with open(link_log_file, "w", encoding="utf-8") as f:
        f.write(f"=== 链接发现日志 ===\n")
        f.write(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"起始 URL: {start_url}\n")
        f.write(f"{'='*60}\n\n")
    
    logging.info(f"链接日志将记录到: {link_log_file}")

    # 初始化
    pages.append({
        "url": start_url,
        "title": "TOP",
        "is_external": False
    })
    visited.add(start_url)
    logging.info(f"初始化完成，起始页面已加入队列")

    index = 0

    while index < len(pages):
        current = pages[index]
        url = current["url"]
        title = current.get("title", "")

        logging.info(f"[{index + 1}/{len(pages)}] 正在爬取: {url} | 标题: {title}")

        html = fetch_html(url)
        if not html:
            logging.warning(f"跳过无法获取的页面: {url}")
            index += 1
            continue

        links = extract_links(html, url)
        logging.debug(f"发现 {len(links)} 个链接")

        new_internal_links = 0
        new_external_links = 0
        
        for item in links:
            link_url = item["url"]

            if link_url not in visited:
                visited.add(link_url)
                
                # 写入链接日志文件
                with open(link_log_file, "a", encoding="utf-8") as f:
                    link_type = "站外" if item["is_external"] else "站内"
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] [{link_type}] {link_url}\n")
                    if item["title"]:
                        f.write(f"  标题: {item['title']}\n")
                    f.write(f"  来源: {url}\n\n")
                
                if item["is_external"]:
                    # 站外链接只记录，不加入爬取队列
                    external_links.append(item)
                    new_external_links += 1
                else:
                    # 站内链接加入爬取队列
                    pages.append(item)
                    new_internal_links += 1
        
        if new_internal_links > 0 or new_external_links > 0:
            logging.info(f"添加了 {new_internal_links} 个站内链接到队列, 记录了 {new_external_links} 个站外链接")

        index += 1

        # 随机延迟 0~2 秒
        time.sleep(random.uniform(0, 2))

    # 写入 JSON
    logging.info(f"开始保存结果到文件: {output_file}")
    result = {
        "internal_pages": pages,
        "external_links": external_links,
        "summary": {
            "total_internal": len(pages),
            "total_external": len(external_links),
            "crawled_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 在链接日志文件中记录统计信息
    with open(link_log_file, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"=== 爬取完成 ===\n")
        f.write(f"结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"站内页面总数: {len(pages)}\n")
        f.write(f"站外链接总数: {len(external_links)}\n")
        f.write(f"{'='*60}\n")
    
    logging.info(f"爬取完成！站内页面: {len(pages)}, 站外链接: {len(external_links)}")
    logging.info(f"结果已保存到: {output_file}")
    logging.info(f"链接日志已保存到: {link_log_file}")


if __name__ == "__main__":
    crawl_site("https://antique-coin-galleria.com/")
    # crawl_site("https://custpro.terabox.co.jp/home/zh/")
