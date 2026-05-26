"""Query rewrite service: disambiguate and expand user questions for better retrieval."""
import logging
from services.llm_client import chat_json

logger = logging.getLogger(__name__)

REWRITE_PROMPT = """你是一个 RAG 知识库的查询改写助手。将用户问题改写为更易检索的形式。

## 规则
1. 如果问题包含代词或模糊指代（"它"、"那个"、"这个"、"他们"），根据上下文推断并展开
2. 添加相关同义词和替代表述
3. 将复合问题拆分为子问题
4. 移除填充词，保留语义核心
5. 不要回答问题——只改写为更好的检索查询

## 输出格式
返回 JSON：
{
  "rewritten_query": "扩展消歧后的检索查询",
  "keywords": ["关键词1", "关键词2", "关键词3"],
  "sub_questions": ["子问题1", "子问题2"],
  "original_intent": "用户真正想问什么的简要描述"
}"""


def rewrite_query(question: str) -> dict:
    """改写用户查询以提升检索质量。改写失败时返回原始问题。"""
    if len(question.strip()) < 8:
        logger.info("Query too short for rewrite, using original: %s", question)
        return {
            "rewritten_query": question,
            "keywords": [question],
            "sub_questions": [],
            "original_intent": question,
        }

    try:
        result = chat_json(REWRITE_PROMPT, question, temperature=0.1)
        rewritten = result.get("rewritten_query", question)
        if not rewritten or rewritten == question:
            logger.info("Rewrite returned original query")
            return {
                "rewritten_query": question,
                "keywords": result.get("keywords", [question]),
                "sub_questions": result.get("sub_questions", []),
                "original_intent": result.get("original_intent", question),
            }
        logger.info("Query rewritten: '%.60s' -> '%.60s'", question, rewritten)
        return result
    except Exception as e:
        logger.warning("Query rewrite failed, using original: %s", e)
        return {
            "rewritten_query": question,
            "keywords": [question],
            "sub_questions": [],
            "original_intent": question,
        }
