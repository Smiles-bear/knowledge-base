"""企业级知识库 — FastAPI 入口"""
import sys
import logging
from fastapi import FastAPI
from store.wiki_store import _ensure_wiki
from store.raw_store import ensure_raw
from routers.api import router as api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enterprise Knowledge Base",
    description="RAG + Karpathy LLM Wiki + 反幻觉验证 — 企业级知识库系统",
    version="1.0.0",
)

# 启动时初始化目录
ensure_raw()
_ensure_wiki()

app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "name": "Enterprise Knowledge Base",
        "version": "1.0.0",
        "architecture": "RAG + LLM Wiki + Anti-Hallucination",
        "endpoints": {
            "ingest": "POST /api/v1/ingest",
            "query": "POST /api/v1/query",
            "lint": "POST /api/v1/lint",
            "archive": "POST /api/v1/archive",
            "health": "GET /api/v1/health",
            "docs": "/docs",
        },
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("启动企业级知识库服务...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
