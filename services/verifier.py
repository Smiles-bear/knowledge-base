"""验证服务：逐条检查 wiki 声明的准确性（反幻觉第一层）"""
import json
import logging
from services.llm_client import chat_json
from store.raw_store import read_raw
from store.wiki_store import read_article, write_article

logger = logging.getLogger(__name__)

VERIFY_PROMPT = """你是事实核查专家。检查 wiki 页面中的每个事实声明是否能在 raw 原文中找到支持。

对每个声明：
- found_in_source=true：在 raw 中找到逐字支持，提供引用
- found_in_source=false：找不到支持证据，可能是 LLM 编造的

返回 JSON：
{
  "claims": [
    {
      "statement": "wiki 中的声明",
      "found_in_source": true/false,
      "evidence": "原文引用" 或 "NOT_FOUND",
      "action": "keep|flag|remove"
    }
  ],
  "overall_confidence": "high|medium|low",
  "summary": "验证总结"
}"""


def verify_article(wiki_path: str, raw_paths: list[str]) -> dict:
    """验证 wiki 页面，逐条对照 raw 原文"""
    wiki_content = read_article(wiki_path)
    if not wiki_content:
        return {"error": "wiki 页面不存在", "claims": [], "overall_confidence": "low"}

    # 收集所有相关的 raw 内容
    raw_contents = []
    for rp in raw_paths:
        c = read_raw(rp)
        if c:
            raw_contents.append(f"--- {rp} ---\n{c[:8000]}")

    if not raw_contents:
        return {"error": "没有 raw 源文件可用于验证", "claims": [], "overall_confidence": "unknown"}

    user_msg = f"""Wiki 页面内容：
{wiki_content[:8000]}

原始资料：
{chr(10).join(raw_contents)}

逐条检查 wiki 中每个事实声明。"""

    result = chat_json(VERIFY_PROMPT, user_msg)

    # 标记未验证的声明
    claims = result.get("claims", [])
    flagged = sum(1 for c in claims if not c.get("found_in_source"))
    verified = sum(1 for c in claims if c.get("found_in_source"))

    logger.info(
        "验证完成 %s: %d/%d 通过, %d 标记",
        wiki_path, verified, len(claims), flagged
    )

    # 在 wiki 页面中追加验证标记
    if flagged > 0:
        wiki_content = read_article(wiki_path)
        verification_section = f"""
---
## 验证记录
- 验证时间: {__import__('datetime').date.today().isoformat()}
- 总声明: {len(claims)}
- 已验证: {verified}
- 未验证: {flagged}
- 置信度: {result.get('overall_confidence', 'unknown')}

### 未验证声明
"""
        for c in claims:
            if not c.get("found_in_source"):
                verification_section += f"- ⚠️ {c['statement'][:100]}\n"

        write_article(
            wiki_path.split("/")[-2] if "/" in wiki_path else "misc",
            wiki_path.split("/")[-1].replace(".md", ""),
            wiki_content + verification_section
        )

    return result
