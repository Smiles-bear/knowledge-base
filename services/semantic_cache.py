"""语义缓存：用 embedding 相似度匹配相似问题，复用缓存结果"""
import json
import hashlib
import logging
import numpy as np
from store.db import SessionLocal, CacheEntry

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.90  # cosine similarity 阈值

_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        from store.vector_store import get_embedder as load_embedder
        _embedder = load_embedder()
    return _embedder


def _cosine_sim(a, b) -> float:
    """NumPy 计算余弦相似度 [0, 1]"""
    a_arr = np.array(a)
    b_arr = np.array(b)
    return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))


def _hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:16]


def lookup(question: str) -> dict | None:
    """语义搜索缓存：相似问题命中同一缓存"""
    emb = _get_embedder().encode([question]).tolist()[0]

    session = SessionLocal()
    try:
        # 用 pgvector 余弦距离排序，取最近 3 个缓存条目
        results = (
            session.query(CacheEntry)
            .order_by(CacheEntry.embedding.cosine_distance(emb))
            .limit(3)
            .all()
        )
        if not results:
            return None

        best = results[0]
        similarity = _cosine_sim(emb, best.embedding)
        if similarity < SIMILARITY_THRESHOLD:
            logger.debug("最佳相似度 %.3f < 阈值 %.2f，未命中", similarity, SIMILARITY_THRESHOLD)
            return None

        cached = json.loads(best.answer_json)
        logger.info("语义缓存命中: %.50s ≈ %.50s (相似度 %.3f)", question, best.question, similarity)
        return cached
    except Exception as e:
        logger.warning("语义缓存查询失败: %s", e)
        return None
    finally:
        session.close()


def store(question: str, answer: dict):
    """存储语义缓存：问题 + 答案 + embedding"""
    h = _hash(question)
    emb = _get_embedder().encode([question]).tolist()[0]

    session = SessionLocal()
    try:
        # 检查是否已存在
        existing = session.query(CacheEntry).filter(CacheEntry.key_hash == h).first()
        if existing:
            existing.answer_json = json.dumps(answer, ensure_ascii=False)
            existing.embedding = emb
        else:
            entry = CacheEntry(
                key_hash=h,
                question=question,
                answer_json=json.dumps(answer, ensure_ascii=False),
                embedding=emb,
            )
            session.add(entry)
        session.commit()
        logger.debug("语义缓存写入: %.50s", question)
    except Exception as e:
        logger.warning("语义缓存写入失败: %s", e)
        session.rollback()
    finally:
        session.close()


def invalidate_all():
    """清空语义缓存"""
    session = SessionLocal()
    try:
        session.query(CacheEntry).delete()
        session.commit()
        logger.info("语义缓存已清空")
    except Exception as e:
        logger.warning("语义缓存清空失败: %s", e)
        session.rollback()
    finally:
        session.close()


def delete_by_question(question: str):
    """删除单条语义缓存"""
    h = _hash(question)
    session = SessionLocal()
    try:
        session.query(CacheEntry).filter(CacheEntry.key_hash == h).delete()
        session.commit()
    finally:
        session.close()
