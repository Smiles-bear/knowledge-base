"""企业级知识库 — FastAPI 入口"""
import sys
import os
import time
import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from store.wiki_store import _ensure_wiki
from store.raw_store import ensure_raw
from store.db import init_db
from routers.api import router as api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# 简易速率限制：每 IP 每分钟最多 30 次请求
_rate_window = 60  # 秒
_rate_limit = 30   # 次
_rate_records: dict[str, list[float]] = defaultdict(list)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_raw()
    _ensure_wiki()
    try:
        init_db()
    except Exception as e:
        logger.warning("DB init skipped (pgvector may not be installed): %s", e)
    yield


app = FastAPI(
    title="Enterprise Knowledge Base",
    description="RAG + Karpathy LLM Wiki + 反幻觉验证 — 企业级知识库系统",
    version="1.0.0",
    lifespan=lifespan,
)

# 请求体大小限制 5MB
MAX_BODY_SIZE = 5 * 1024 * 1024


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # 1. 速率限制
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    records = _rate_records[client_ip]
    # 清理过期记录
    records[:] = [t for t in records if now - t < _rate_window]
    if len(records) >= _rate_limit:
        logger.warning("速率限制触发: %s (%d 次/%ds)", client_ip, len(records), _rate_window)
        return JSONResponse({"detail": "请求过于频繁，请稍后再试"}, status_code=429)
    records.append(now)

    # 2. 请求体大小限制
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BODY_SIZE:
        return JSONResponse({"detail": "请求体过大，上限 5MB"}, status_code=413)

    return await call_next(request)


app.include_router(api_router)

# 前端静态文件服务
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "frontend", "dist")
_has_frontend = os.path.exists(FRONTEND_DIST)

if _has_frontend:
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/")
async def root():
    if _has_frontend:
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
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
    logger.info("启动企业级知识库服务 (内网可访问: http://<本机IP>:8000)...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
