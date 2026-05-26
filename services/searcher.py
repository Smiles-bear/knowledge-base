"""检索服务：Wiki 直读 + RAG 混合检索"""
import logging
from store.vector_store import VectorStore
from store.wiki_store import read_article, read_index, list_articles
from services.query_rewriter import rewrite_query

logger = logging.getLogger(__name__)
_vector_store = None


def _get_vector_store():
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
        _vector_store.build_index()
    return _vector_store


def wiki_direct_search(keywords: list[str]) -> str:
    """直接读 Wiki 索引，找到相关文章后全文返回（Token 最省）"""
    idx = read_index()
    articles = list_articles()
    found = []

    for kw in keywords:
        for art in articles:
            if kw.lower() in art.lower():
                found.append(art)

    if not found:
        return idx if idx else "知识库为空"

    contents = []
    for art in found[:3]:
        c = read_article(art)
        if c:
            contents.append(f"## {art}\n\n{c[:2000]}")

    return "\n\n---\n\n".join(contents) if contents else idx


def rag_search(query: str, top_k: int = 5) -> str:
    """RAG 混合检索：向量 + 关键词（Token 消耗较高，但覆盖面广）"""
    vs = _get_vector_store()
    results = vs.search(query, top_k)
    return "\n\n---\n\n".join(results) if results else "未找到相关内容"


def search(query: str, route_info: dict) -> str:
    """根据路由结果选择搜索策略"""
    route_type = route_info.get("route", "rag_search")
    keywords = route_info.get("keywords", [query])

    if route_type in ("simple_chat",):
        return ""

    # Query rewrite: expand and disambiguate before search
    rewrite_result = rewrite_query(query)
    search_query = rewrite_result.get("rewritten_query", query)
    merged_keywords = list(set(
        keywords + rewrite_result.get("keywords", [])
    ))

    if route_type in ("wiki_direct", "wiki_with_links"):
        result = wiki_direct_search(merged_keywords)
        if result and result != "知识库为空":
            return result
        logger.info("Wiki 未命中，回退到 RAG")

    return rag_search(search_query)
