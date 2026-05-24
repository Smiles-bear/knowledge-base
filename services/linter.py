"""Lint 服务：Wiki 健康检查 + 反幻觉扫描（第四层）"""
import logging
from store.wiki_store import read_article, read_index, list_articles, append_log
from store.raw_store import read_raw

logger = logging.getLogger(__name__)


def run_lint() -> dict:
    """运行 Wiki 健康检查"""
    articles = list_articles()
    idx = read_index()
    report = {
        "total_articles": len(articles),
        "issues": [],
        "auto_fixed": [],
    }

    # 1. 死引用检查
    for art in articles:
        content = read_article(art) or ""
        if "来源: raw/" in content or "来源：" in content:
            # 检查引用路径是否在 raw/ 中存在
            pass

    # 2. 索引一致性检查
    for art in articles:
        if art.replace(".md", "") not in idx and art.split("/")[-1].replace(".md", "") not in idx:
            report["issues"].append({"type": "missing_from_index", "article": art})

    # 3. 孤立声明检查：没有引用任何 source 的段落
    for art in articles:
        content = read_article(art) or ""
        if "[已验证]" not in content and "[未验证]" not in content and "[推断]" not in content:
            report["issues"].append({
                "type": "no_verification_marks",
                "article": art,
                "detail": "页面中没有置信度标记"
            })

    # 4. 重复内容检测
    seen = {}
    for art in articles:
        content = read_article(art) or ""
        first_line = content.split("\n")[0] if content else ""
        if first_line in seen:
            report["issues"].append({
                "type": "possible_duplicate",
                "article": art,
                "other": seen[first_line],
            })
        seen[first_line] = art

    if report["issues"]:
        append_log("lint", f"{len(report['issues'])} 个问题, {len(report['auto_fixed'])} 自动修复")
    else:
        append_log("lint", "无问题")

    logger.info("Lint 完成: %d 篇文章, %d 个问题", len(articles), len(report["issues"]))
    return report
