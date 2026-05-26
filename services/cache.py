"""缓存服务：Redis + 内存双模（Token 优化第 4 层）"""
import json
import hashlib
import logging
import time
from config import REDIS_URL

logger = logging.getLogger(__name__)

_redis = None
_redis_available = False
_memory_cache: dict[str, tuple[float, str]] = {}
_cache_hits = 0
_cache_misses = 0

try:
    import redis
    _pool = redis.ConnectionPool.from_url(REDIS_URL, socket_connect_timeout=2, max_connections=10)
    _redis = redis.Redis(connection_pool=_pool)
    _redis.ping()
    _redis_available = True
    logger.info("Redis 已连接: %s", REDIS_URL)
except Exception as e:
    logger.warning("Redis 不可用 (%s)，使用内存缓存", e)


def _hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:16]


def get(key: str) -> dict | None:
    """查缓存"""
    global _cache_hits, _cache_misses
    h = _hash(key)
    try:
        if _redis_available and _redis:
            data = _redis.get(f"kb:{h}")
            if data:
                _cache_hits += 1
                logger.info("缓存命中 (Redis): %.60s", h)
                return json.loads(data)
        else:
            if h in _memory_cache:
                ts, data = _memory_cache[h]
                if time.time() - ts < 3600:
                    _cache_hits += 1
                    logger.info("缓存命中 (内存): %.60s", h)
                    return json.loads(data)
                del _memory_cache[h]
        _cache_misses += 1
    except Exception as e:
        logger.warning("缓存读取失败: %s", e)
        _cache_misses += 1
    return None


def set(key: str, value: dict, ttl: int = 3600):
    """写缓存"""
    h = _hash(key)
    data = json.dumps(value, ensure_ascii=False)
    try:
        if _redis_available and _redis:
            _redis.setex(f"kb:{h}", ttl, data)
            logger.debug("缓存写入 (Redis): %.60s, TTL=%d", h, ttl)
        else:
            _memory_cache[h] = (time.time(), data)
            logger.debug("缓存写入 (内存): %.60s", h)
    except Exception as e:
        logger.warning("缓存写入失败: %s", e)


def delete(key: str):
    """删除单条缓存"""
    h = _hash(key)
    try:
        if _redis_available and _redis:
            _redis.delete(f"kb:{h}")
        if h in _memory_cache:
            del _memory_cache[h]
        logger.info("缓存失效: %.60s", h)
    except Exception as e:
        logger.warning("缓存删除失败: %s", e)


def invalidate_all():
    """清除全部缓存（ingest 后调用）"""
    try:
        if _redis_available and _redis:
            keys = _redis.keys("kb:*")
            if keys:
                _redis.delete(*keys)
        _memory_cache.clear()
        logger.info("全部缓存已失效")
    except Exception as e:
        logger.warning("缓存全部失效失败: %s", e)


def get_stats() -> dict:
    """返回缓存统计"""
    return {
        "hits": _cache_hits,
        "misses": _cache_misses,
        "backend": "redis" if _redis_available else "memory",
        "memory_entries": len(_memory_cache),
    }
