"""Lint 服务：Wiki 健康检查 + 反幻觉扫描（第四层）"""
import re
import logging
from datetime import date, datetime
from collections import defaultdict
from store.wiki_store import read_article, read_index, list_articles, append_log
from store.raw_store import list_raw
from config import STALE_DAYS

logger = logging.getLogger(__name__)


def _extract_refs(content: str) -> list[str]:
    """从 wiki 内容中提取 raw 文件引用"""
    refs = []
    matches = re.findall(r'(?:来源|源文件|ref|参考|source)[：:]\s*(raw/[^\s\n\)]+)', content)
    refs.extend(matches)
    link_matches = re.findall(r'\]\((raw/[^\)]+)\)', content)
    refs.extend(link_matches)
    return refs


def _parse_date_from_content(content: str):
    """从文章内容中提取日期"""
    patterns = [
        r'(\d{4}-\d{2}-\d{2})',
        r'Collected:\s*(\d{4}-\d{2}-\d{2})',
    ]
    for pat in patterns:
        m = re.search(pat, content)
        if m:
            try:
                return datetime.strptime(m.group(1), "%Y-%m-%d").date()
            except ValueError:
                pass
    return None


def _check_contradictions(articles: list[str]) -> list[dict]:
    """LLM 检测同主题文章间的矛盾"""
    from services.llm_client import chat_json

    CONTRADICTION_PROMPT = """检查两篇知识库文章是否存在事实矛盾。

规则：
- 矛盾 = 同一个事实在两篇文章中被描述得不一致
- 互补 = 同一主题的不同方面，不矛盾
- 无关 = 讨论完全不同的主题

返回 JSON：
{
  "has_contradiction": true/false,
  "detail": "矛盾描述（如果有）",
  "article_a_claim": "文章A的声明",
  "article_b_claim": "文章B的声明"
}"""

    issues = []
    by_topic = defaultdict(list)
    for art in articles:
        topic = art.split("/")[0] if "/" in art else "root"
        by_topic[topic].append(art)

    for topic, arts in by_topic.items():
        if len(arts) < 2:
            continue
        for i in range(len(arts)):
            for j in range(i + 1, len(arts)):
                content_a = read_article(arts[i]) or ""
                content_b = read_article(arts[j]) or ""
                if not content_a or not content_b:
                    continue
                user_msg = f"文章1 ({arts[i]}):\n{content_a[:3000]}\n\n文章2 ({arts[j]}):\n{content_b[:3000]}"
                try:
                    result = chat_json(CONTRADICTION_PROMPT, user_msg, temperature=0.0)
                    if result.get("has_contradiction"):
                        issues.append({
                            "type": "contradiction",
                            "article": arts[i],
                            "other": arts[j],
                            "detail": result.get("detail", ""),
                            "claim_a": result.get("article_a_claim", ""),
                            "claim_b": result.get("article_b_claim", ""),
                        })
                        logger.info("矛盾检测: %s <-> %s", arts[i], arts[j])
                except Exception as e:
                    logger.warning("矛盾检测失败 (%s <-> %s): %s", arts[i], arts[j], e)
    return issues


def run_lint() -> dict:
    """运行 Wiki 健康检查（6 项检查）"""
    articles = list_articles()
    idx = read_index()
    raw_files = set(list_raw())
    report = {
        "total_articles": len(articles),
        "issues": [],
        "auto_fixed": [],
    }

    # 1. 死引用检查
    for art in articles:
        content = read_article(art) or ""
        refs = _extract_refs(content)
        for ref in refs:
            normalized = ref[4:] if ref.startswith("raw/") else ref
            if normalized not in raw_files:
                report["issues"].append({
                    "type": "dead_ref",
                    "article": art,
                    "ref": ref,
                    "detail": f"引用的 raw 文件 '{ref}' 不存在",
                })

    # 2. 索引一致性检查
    for art in articles:
        if art.replace(".md", "") not in idx and art.split("/")[-1].replace(".md", "") not in idx:
            report["issues"].append({"type": "missing_from_index", "article": art})

    # 3. 孤立声明检查
    for art in articles:
        content = read_article(art) or ""
        if "[已验证]" not in content and "[未验证]" not in content and "[推断]" not in content:
            report["issues"].append({
                "type": "no_verification_marks",
                "article": art,
                "detail": "页面中没有置信度标记",
            })

    # 4. 重复内容检测
    seen = {}
    for art in articles:
        content = read_article(art) or ""
        first_line = content.split("\n")[0].strip() if content else ""
        if first_line and first_line in seen:
            report["issues"].append({
                "type": "possible_duplicate",
                "article": art,
                "other": seen[first_line],
                "detail": f"与 {seen[first_line]} 标题相同",
            })
        if first_line:
            seen[first_line] = art

    # 5. 矛盾检测（LLM 驱动）
    contradiction_issues = _check_contradictions(articles)
    report["issues"].extend(contradiction_issues)

    # 6. 时效性检查
    today = date.today()
    for art in articles:
        content = read_article(art) or ""
        art_date = _parse_date_from_content(content)
        if art_date:
            days_old = (today - art_date).days
            if days_old > STALE_DAYS:
                report["issues"].append({
                    "type": "stale_content",
                    "article": art,
                    "days_old": days_old,
                    "detail": f"内容已 {days_old} 天未更新（阈值: {STALE_DAYS} 天）",
                })

    if report["issues"]:
        append_log("lint", f"{len(report['issues'])} 个问题, {len(report['auto_fixed'])} 自动修复")
    else:
        append_log("lint", "无问题")

    logger.info("Lint 完成: %d 篇文章, %d 个问题", len(articles), len(report["issues"]))
    return report
