"""编译服务：raw → wiki 文章"""
import logging
from services.llm_client import chat_json
from store.raw_store import read_raw, list_raw
from store.wiki_store import write_article, update_index, append_log

logger = logging.getLogger(__name__)

COMPILE_PROMPT = """你是知识编译专家。阅读原始资料，提取关键信息，编译成结构化的 Wiki 页面。

编译规则：
1. 提取事实声明，不要编造任何原文没有的信息
2. 用 ## 标题组织内容
3. 在每段后标注置信度：[已验证]（原文明确提到）、[推断]（多条事实的逻辑推论）、[未验证]（你的判断）
4. 保留原文关键引用（谁、什么时候、在哪说的）
5. 列出相关概念，用于交叉引用

返回 JSON：
{
  "title": "页面标题（概念名，简洁）",
  "topic": "分类目录（ai/backend/frontend/devops 等）",
  "slug": "url-friendly-slug",
  "content": "完整的 Markdown 页面内容",
  "confidence": "high|medium|low",
  "cross_refs": ["相关概念1", "相关概念2"],
  "summary": "一句话摘要"
}"""


def compile_raw_source(raw_path: str) -> dict | None:
    """将 raw 目录中的一篇源文章编译为 wiki 页面"""
    raw_content = read_raw(raw_path)
    if not raw_content:
        logger.error("raw 文件不存在: %s", raw_path)
        return None

    user_msg = f"原始资料路径: {raw_path}\n\n内容:\n{raw_content[:12000]}"
    result = chat_json(COMPILE_PROMPT, user_msg)

    if not result.get("content"):
        logger.error("编译失败，LLM 未返回内容")
        return None

    # 写入 wiki
    path = write_article(result["topic"], result["slug"], result["content"])

    # 更新索引
    update_index([{
        "title": result["title"],
        "topic": result["topic"],
        "slug": result["slug"],
        "summary": result.get("summary", ""),
    }])

    # 记录日志
    append_log("compile", f"{result['title']} (from {raw_path})")

    result["path"] = path
    logger.info("编译完成: %s → %s", raw_path, path)
    return result
