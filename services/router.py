"""意图路由器：判断问题类型，选择最优路径（Token 优化第 2 层）"""
import logging
from services.llm_client import chat_json

logger = logging.getLogger(__name__)

ROUTE_PROMPT = """分析用户问题，判断应该走哪条检索路径。

路径选择：
- wiki_direct: 简单事实型问题，读 1-2 篇 Wiki 文章就能回答（Token: ~1.5K）
- wiki_with_links: 需要跨文章关联，跟随交叉引用（Token: ~3K）
- rag_search: 复杂综合型问题，需要向量检索多篇文章（Token: ~5K）
- simple_chat: 不需要知识库，直接回答（Token: ~0.5K）

返回 JSON：
{
  "route": "wiki_direct|wiki_with_links|rag_search|simple_chat",
  "reason": "判断依据（一句话）",
  "keywords": ["搜索关键词1", "搜索关键词2"]
}"""


def route(question: str) -> dict:
    """判断问题应该走哪条路径，路由本身只消耗 ~100 token"""
    result = chat_json(ROUTE_PROMPT, question, temperature=0.0)
    logger.info("路由: %s → %s (%s)", question[:50], result.get("route"), result.get("reason"))
    return result
