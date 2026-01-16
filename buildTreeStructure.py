import json
import logging
import re
from urllib.parse import urlparse, unquote
from collections import defaultdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 定义需要识别为动态路径的模式
# 特殊的collection分类列表（不应该被动态化的collection名称）
STATIC_COLLECTIONS = {
    '1000000-5000000', '100万円以下のコイン', '500000-1000000', 
    '5000000-10000000', 'over-10000000'  # 价格区间分类
}

DYNAMIC_PATTERNS = [
    r'/blogs?/[^/]+/[^/]+$',                        # /blog/xxx 或 /blogs/news/xxx
    r'/blogs/[^/]+/tagged/[^/]+$',                  # /blogs/times/tagged/xxx, /blogs/news/tagged/xxx
    r'/pages/[^/]+$',                                # /pages/xxx
    r'/news/[^/]+$',                                 # /news/xxx
    r'/collections/[^/]+/products/[^/]+$',          # /collections/xxx/products/yyy
    r'/collections/[^/]+$',                          # /collections/xxx (collection分类)
    r'/products/[^/]+$',                             # /products/xxx
    r'/articles?/[^/]+$',                            # /article/xxx 或 /articles/xxx
    r'/posts?/[^/]+$',                               # /post/xxx 或 /posts/xxx
    r'/items?/[^/]+$',                               # /item/xxx 或 /items/xxx
]


class PathNode:
    """路径树节点"""
    def __init__(self, name, full_path="", url="", title="", is_dynamic=False):
        self.name = name  # 当前路径段名称
        self.full_path = full_path  # 完整路径
        self.url = url  # 完整URL
        self.title = title  # 页面标题
        self.children = {}  # 子节点字典
        self.is_page = bool(url)  # 是否为实际页面
        self.is_dynamic = is_dynamic  # 是否为动态路径
        self.instances = []  # 如果是动态节点，存储所有实例
    
    def add_child(self, name, is_dynamic=False):
        """添加子节点"""
        if name not in self.children:
            self.children[name] = PathNode(name, is_dynamic=is_dynamic)
        return self.children[name]
    
    def add_instance(self, url, title, actual_id):
        """添加动态路径实例"""
        self.instances.append({
            "url": url,
            "title": title,
            "id": actual_id
        })
    
    def to_dict(self):
        """转换为字典格式 - 简化版"""
        result = {
            "path": self.full_path,
            "name": self.name,
        }
        
        if self.is_dynamic:
            result["type"] = "dynamic"
            result["count"] = len(self.instances)
        elif self.is_page:
            result["type"] = "page"
            result["url"] = self.url
            result["title"] = self.title
        else:
            result["type"] = "directory"
        
        # 简化的children表示
        if self.children:
            result["children"] = [
                child.to_dict() 
                for child in sorted(self.children.values(), key=lambda x: x.name)
            ]
        
        return result


def is_dynamic_path(path):
    """
    判断路径是否匹配动态模式
    返回: (is_dynamic, pattern_path, actual_id)
    """
    parts = path.split('/')
    
    # 特殊处理：/collections/xxx/products/yyy 优先匹配
    if len(parts) >= 5 and parts[1] == 'collections' and parts[3] == 'products':
        # /collections/uk/products/some-product -> /collections/[category]/products/[id]
        category = parts[2]
        product_id = parts[4]
        pattern_path = f"/collections/[category]/products/[id]"
        actual_id = f"{category}/{product_id}"
        return True, pattern_path, actual_id
    
    # 特殊处理：/collections/xxx (但排除价格区间)
    if len(parts) == 3 and parts[1] == 'collections':
        category = parts[2]
        # 如果是静态的collection（如价格区间），不动态化
        if category not in STATIC_COLLECTIONS:
            pattern_path = "/collections/[category]"
            return True, pattern_path, category
    
    # 特殊处理：/blogs/xxx/tagged/yyy -> /blogs/xxx/tagged/[tag]
    if len(parts) == 5 and parts[1] == 'blogs' and parts[3] == 'tagged':
        blog_type = parts[2]  # news 或 times
        tag = parts[4]
        pattern_path = f"/blogs/{blog_type}/tagged/[tag]"
        return True, pattern_path, tag
    
    # 特殊处理：/pages/xxx -> /pages/[slug]
    if len(parts) == 3 and parts[1] == 'pages':
        slug = parts[2]
        pattern_path = "/pages/[slug]"
        return True, pattern_path, slug
    
    # 处理其他动态模式
    for pattern in DYNAMIC_PATTERNS:
        if re.search(pattern, path):
            # 排除已经处理过的collections模式
            if '/collections/' in pattern:
                continue
            
            # 其他单层动态路径
            actual_id = parts[-1]
            pattern_path = '/'.join(parts[:-1]) + '/[id]'
            return True, pattern_path, actual_id
    
    return False, path, None


def build_tree_from_sitemap(sitemap_file: str, output_file: str = "sitemap_tree.json"):
    """
    从sitemap.json构建树状结构
    """
    logging.info(f"开始读取sitemap文件: {sitemap_file}")
    
    # 读取sitemap
    with open(sitemap_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    internal_pages = data.get("internal_pages", [])
    logging.info(f"找到 {len(internal_pages)} 个内部页面")
    
    # 创建根节点
    root = PathNode("root")
    
    # 统计信息
    processed = 0
    skipped = 0
    
    for page in internal_pages:
        url = page.get("url", "")
        title = page.get("title", "")
        
        if not url:
            skipped += 1
            continue
        
        # 过滤掉畸形URL（包含空格或嵌入的http/https）
        parsed = urlparse(url)
        path = parsed.path
        
        # 检查路径是否包含畸形内容
        if ' http' in path or '%20http' in path:
            logging.warning(f"跳过畸形URL: {url}")
            skipped += 1
            continue
        
        # 解码URL编码的路径
        path = unquote(path)
        
        # 处理根路径
        if not path or path == "/":
            # 根路径
            if not root.url:  # 只设置一次
                root.url = url
                root.title = title
                root.full_path = "/"
                root.is_page = True
            processed += 1
            continue
        
        # 检查是否为动态路径
        is_dyn, pattern_path, actual_id = is_dynamic_path(path)
        
        # 如果是动态路径，使用模式路径
        working_path = pattern_path if is_dyn else path
        
        # 分割路径
        parts = [p for p in working_path.split("/") if p]
        
        # 构建树
        current_node = root
        current_path = ""
        
        for i, part in enumerate(parts):
            current_path += "/" + part
            
            # 判断这个部分是否是[id]
            is_id_part = (part == "[id]")
            
            # 添加或获取子节点
            if part not in current_node.children:
                current_node.children[part] = PathNode(
                    name=part,
                    full_path=current_path,
                    is_dynamic=is_id_part
                )
            
            current_node = current_node.children[part]
            
            # 如果是最后一个部分
            if i == len(parts) - 1:
                if is_dyn:
                    # 动态节点，添加实例
                    current_node.add_instance(url, title, actual_id)
                else:
                    # 普通页面，设置URL和标题
                    current_node.url = url
                    current_node.title = title
                    current_node.is_page = True
        
        processed += 1
        
        if processed % 10 == 0:
            logging.info(f"已处理 {processed} 个页面...")
    
    logging.info(f"处理完成: {processed} 个页面, 跳过 {skipped} 个")
    
    # 转换为字典树
    tree_dict = root.to_dict()
    
    # 构建结果
    result = {
        "metadata": {
            "source_file": sitemap_file,
            "total_pages": processed,
            "skipped": skipped,
            "generated_at": data.get("summary", {}).get("crawled_at", "")
        },
        "tree": tree_dict
    }
    
    # 保存结果
    logging.info(f"开始保存树状结构到: {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logging.info(f"树状结构已保存到: {output_file}")
    
    # 打印统计信息
    stats = count_tree_stats(root)
    print_stats(stats)


def count_tree_stats(node):
    """统计树的信息"""
    stats = {
        "total": 0,
        "pages": 0,
        "dynamic": 0,
        "directories": 0,
        "dynamic_instances": 0
    }
    
    def count_node(n):
        stats["total"] += 1
        if n.is_dynamic:
            stats["dynamic"] += 1
            stats["dynamic_instances"] += len(n.instances)
        elif n.is_page:
            stats["pages"] += 1
        elif n.children:
            stats["directories"] += 1
        
        for child in n.children.values():
            count_node(child)
    
    count_node(node)
    return stats


def print_stats(stats):
    """打印统计信息"""
    logging.info("=== 路径结构统计 ===")
    logging.info(f"总节点数: {stats['total']}")
    logging.info(f"  - 页面: {stats['pages']}")
    logging.info(f"  - 动态路径: {stats['dynamic']}")
    logging.info(f"  - 目录: {stats['directories']}")
    if stats['dynamic'] > 0:
        logging.info(f"动态路径总实例数: {stats['dynamic_instances']}")


if __name__ == "__main__":
    build_tree_from_sitemap("sitemap.json", "sitemap_tree.json")
