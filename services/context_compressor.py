"""上下文预算控制：压缩过长检索结果，控制 LLM KV Cache 消耗"""
import re
import logging
from config import MAX_CONTEXT_CHARS

logger = logging.getLogger(__name__)


def compress(context: str, max_chars: int = None) -> str:
    """按预算压缩上下文，超长时逐级压缩"""
    if max_chars is None:
        max_chars = MAX_CONTEXT_CHARS

    if len(context) <= max_chars:
        logger.debug("上下文 %d 字符，未超预算 %d", len(context), max_chars)
        return context

    original_len = len(context)
    chunks = context.split("\n\n---\n\n")

    # Level 1: truncate each chunk proportionally
    budget_per_chunk = max(300, max_chars // len(chunks))
    compressed = _truncate_chunks(chunks, budget_per_chunk, max_chars)
    if len("".join(compressed)) <= max_chars:
        logger.info("上下文 %d→%d 字符 (L1 截断)", original_len, len("".join(compressed)))
        return _join(compressed)

    # Level 2: reduce chunk count, keep top-ranked
    half = max(len(chunks) // 2, 1)
    logger.info("上下文 %d 字符超预算，丢弃末尾 %d 个 chunk", original_len, len(chunks) - half)
    compressed = _truncate_chunks(chunks[:half], budget_per_chunk, max_chars)
    return _join(compressed)


def _truncate_chunks(chunks: list[str], per_chunk: int, total: int) -> list[str]:
    """截断每个 chunk 到预算长度"""
    result = []
    remaining = total
    n = len(chunks)
    for i, chunk in enumerate(chunks):
        if remaining <= 150:
            break
        budget = min(per_chunk, remaining // (n - i))
        if len(chunk) > budget:
            # 截断时尽量保留完整句子
            truncated = chunk[:budget]
            last_period = max(truncated.rfind("。"), truncated.rfind("\n"))
            if last_period > budget * 0.6:
                truncated = truncated[:last_period + 1]
            result.append(truncated)
            remaining -= len(truncated) + 5
        else:
            result.append(chunk)
            remaining -= len(chunk) + 5
    return result


def _join(chunks: list[str]) -> str:
    return "\n\n---\n\n".join(chunks)
