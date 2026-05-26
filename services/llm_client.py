"""统一 LLM 调用客户端"""
import json
import logging
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

logger = logging.getLogger(__name__)
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


def chat_json(system: str, user: str, temperature: float = 0.1) -> dict:
    """调用 LLM 并返回 JSON 解析结果"""
    try:
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        logger.error("LLM 调用失败: %s", e)
        raise


def chat_text(system: str, user: str, temperature: float = 0.3) -> str:
    """调用 LLM 并返回纯文本"""
    try:
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        return resp.choices[0].message.content
    except Exception as e:
        logger.error("LLM 调用失败: %s", e)
        raise


def chat_text_stream(system: str, user: str, temperature: float = 0.3):
    """调用 LLM 并流式逐 token 返回"""
    try:
        stream = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
    except Exception as e:
        logger.error("LLM 流式调用失败: %s", e)
        raise
