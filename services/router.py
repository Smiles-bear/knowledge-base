"""意图路由器：判断问题类型，选择最优路径（Token 优化第 2 层）"""
import logging
from services.llm_client import chat_json

logger = logging.getLogger(__name__)

ROUTE_PROMPT = """你是一个查询路由分类器。判断用户问题在知识库系统中应该走哪条检索路径。

## 可用路径

1. **wiki_direct** — 问题涉及事实、定义、概念，可以阅读 1-2 篇 Wiki 文章直接回答。用于：
   - "X 是什么？"（X 是具体术语/概念）
   - "介绍一下 Y"
   - "解释 Z 的原理"
   - 询问知识库内容的："知识库中有哪些内容？"、"有哪些文章？"、"列出所有关于 X 的文章"
   - 关于特定实体、人物、事件的问题

2. **rag_search** — 问题需要跨多篇文章搜索，答案分散在知识库各处。用于：
   - "比较 A 和 B 的区别"
   - "X 和 Y 有什么关系？"
   - "X 怎么做？"（复杂流程）
   - "总结所有关于 T 的内容"
   - 涉及"所有"、"全部"、"综合"的问题
   - 问题较长（超过20字）且涉及技术概念时优先选此路径

3. **simple_chat** — 问题完全不需要知识库，直接回答即可。**仅用于**：
   - 问候语："你好"、"嗨"、"早上好"
   - 关于系统本身的元问题："你是谁？"、"你是什么模型？"
   - 闲聊：笑话、天气、个人观点
   - 不涉及任何可能存储在知识库中的话题
   - 重要：只要问题涉及任何可能存在于知识库中的话题，就选 wiki_direct 或 rag_search

## 判断示例

Q: "什么是 Transformer？" → route: "wiki_direct", reason: "询问具体概念的定义"
Q: "知识库中有哪些内容？" → route: "wiki_direct", reason: "询问知识库内容清单，需要读取索引"
Q: "比较 BERT 和 GPT 的区别" → route: "rag_search", reason: "对比分析需要检索多篇文章"
Q: "你好" → route: "simple_chat", reason: "问候语，不需要知识库"
Q: "你是谁？" → route: "simple_chat", reason: "关于系统本身的元问题"
Q: "列出所有关于 Python 的文章" → route: "wiki_direct", reason: "查看文章列表，读取索引即可"

## 输出格式
返回 JSON：
{
  "route": "wiki_direct|rag_search|simple_chat",
  "reason": "简短判断依据",
  "keywords": ["关键词1", "关键词2"]
}

CRITICAL: 在 simple_chat 和其他路径之间犹豫时，选择知识库路径。只有确信问题与知识库完全无关时才选 simple_chat。"""


def route(question: str) -> dict:
    """判断问题应该走哪条路径，路由本身只消耗 ~100 token"""
    result = chat_json(ROUTE_PROMPT, question, temperature=0.0)

    route_val = result.get("route", "rag_search")

    # Guard: 长问题 + 非问候语 → 不太可能是 simple_chat
    greetings = ["你好", "hello", "hi", "谢谢", "再见", "早上好", "晚上好"]
    is_greeting = any(g in question.lower() for g in greetings)

    if route_val == "simple_chat" and len(question.strip()) > 15 and not is_greeting:
        logger.warning(
            "Router misclassified substantive query as simple_chat, forcing rag_search: %.60s",
            question,
        )
        route_val = "rag_search"
        result["route"] = route_val
        result["reason"] = "Fallback: question appears substantive, defaulting to rag_search"

    logger.info("路由: %.50s → %s (%s)", question, route_val, result.get("reason"))
    return result
