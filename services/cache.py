"""缓存服务：Redis + 内存双模（Token 优化第 4 层）"""
import json
import hashlib
import logging
from config import REDIS_URL

logger = logging.getLogger(__name__)

_redis = None
_memory_cache: dict[str, tuple[float, str]] = {}

try:
    import redis
    _redis = redis.from_url(REDIS_URL, socket_connect_timeout=2)
    _redis.ping()
    logger.info("Redis 已连接")
except Exception:
    logger.warning("Redis 不可用，使用内存缓存")


def _hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:16]


def get(key: str) -> dict | None:
    """查缓存"""
    h = _hash(key)
    try:
        if _redis:
            data = _redis.get(f"kb:{h}")
            return json.loads(data) if data else None
        else:
            import time
            if h in _memory_cache:
                ts, data = _memory_cache[h]
                if time.time() - ts < 3600:
                    return json.loads(data)
                del _memory_cache[h]
    except Exception as e:
        logger.warning("缓存读取失败: %s", e)
    return None


def set(key: str, value: dict, ttl: int = 3600):
    """写缓存"""
    h = _hash(key)
    data = json.dumps(value, ensure_ascii=False)
    try:
        if _redis:
            _redis.setex(f"kb:{h}", ttl, data)
        else:
            import time
            _memory_cache[h] = (time.time(), data)
    except Exception as e:
        logger.warning("缓存写入失败: %s", e)
