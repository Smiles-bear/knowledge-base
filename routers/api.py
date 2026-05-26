"""统一 API 路由"""
import json
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models.schemas import (
    IngestRequest, IngestResponse,
    QueryRequest, QueryResponse,
    ArchiveRequest,
    LintResponse,
    HealthResponse,
    ConversationCreate, ConversationResponse,
    ConversationDetail, MessageSchema,
)
from services.compiler import compile_raw_source
from services.verifier import verify_article
from services.router import route
from services.searcher import search
from services.linter import run_lint
from services.archiver import archive_answer
from services.cache import get as cache_get, set as cache_set, invalidate_all as cache_invalidate, get_stats as cache_stats
from services.llm_client import chat_text, chat_text_stream
from store.raw_store import save_raw, list_raw
from store.wiki_store import list_articles
from store.db import SessionLocal, Conversation, Message
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["knowledge-base"])

QUERY_SYSTEM = """你是企业知识库助手。根据提供的知识库内容回答问题。
规则：
1. 基于提供的知识库内容回答，不要使用训练数据
2. 每个声明引用具体来源（文件名 + 段落）
3. 如果内容不足以回答，说"知识库中没有相关信息"
4. 简洁准确，不编造"""


@router.post("/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest):
    """Ingest 操作：存储原始资料 → 编译为 Wiki → 验证"""
    # 存储到 raw/
    raw_path = save_raw(req.topic, req.title, req.content, req.source_url)

    # 编译为 Wiki
    result = compile_raw_source(raw_path)
    if not result:
        raise HTTPException(status_code=500, detail="编译失败")

    # 验证
    verify_result = {}
    verified = 0
    flagged = 0
    if result.get("path"):
        verify_result = verify_article(result["path"], [raw_path])
        claims = verify_result.get("claims", [])
        verified = sum(1 for c in claims if c.get("found_in_source"))
        flagged = sum(1 for c in claims if not c.get("found_in_source"))

    cache_invalidate()
    return IngestResponse(
        status="completed",
        wiki_path=result.get("path", ""),
        confidence=result.get("confidence", "unknown"),
        verified_claims=verified,
        flagged_claims=flagged,
    )


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """Query 操作：意图路由 → 检索 → 回答 → 归档判断"""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    # 查缓存
    cached = cache_get(req.question)
    if cached:
        return QueryResponse(**cached)

    # 意图路由
    route_info = route(req.question)

    # 检索
    context = search(req.question, route_info)

    # 回答
    user_msg = f"知识库内容：\n{context}\n\n问题：{req.question}" if context else req.question
    answer = chat_text(QUERY_SYSTEM, user_msg)

    token_est = {"wiki_direct": 1500, "wiki_with_links": 3000, "rag_search": 5000, "simple_chat": 500}.get(
        route_info.get("route", "rag_search"), 3000
    )

    response = QueryResponse(
        answer=answer,
        route=route_info.get("route", "rag_search"),
        route_reason=route_info.get("reason", ""),
        token_estimate=token_est,
        sources=[s.split("\n")[0] for s in context.split("---")][:5] if context else [],
    )

    # 写入缓存
    cache_set(req.question, response.model_dump())

    return response


@router.post("/query/stream")
async def query_stream(req: QueryRequest):
    """Query 操作（SSE 流式）：Token 逐字返回"""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    cached = cache_get(req.question)
    if cached:
        import json as _json

        async def cached_stream():
            yield f"data: {_json.dumps({'type': 'complete', 'data': cached}, ensure_ascii=False)}\n\n"

        return StreamingResponse(cached_stream(), media_type="text/event-stream")

    route_info = route(req.question)
    context = search(req.question, route_info)
    user_msg = f"知识库内容：\n{context}\n\n问题：{req.question}" if context else req.question

    async def event_stream():
        full_answer = []
        try:
            # 先发 metadata
            meta = {
                "type": "meta",
                "route": route_info.get("route", "rag_search"),
                "route_reason": route_info.get("reason", ""),
            }
            yield f"data: {json.dumps(meta, ensure_ascii=False)}\n\n"

            # 流式 token
            for token in chat_text_stream(QUERY_SYSTEM, user_msg):
                full_answer.append(token)
                yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"

            # 完成
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

            # 写缓存
            answer = "".join(full_answer)
            token_est = {"wiki_direct": 1500, "wiki_with_links": 3000, "rag_search": 5000, "simple_chat": 500}.get(
                route_info.get("route", "rag_search"), 3000
            )
            cache_set(
                req.question,
                {
                    "answer": answer,
                    "route": route_info.get("route", "rag_search"),
                    "route_reason": route_info.get("reason", ""),
                    "token_estimate": token_est,
                    "sources": [s.split("\n")[0] for s in context.split("---")][:5] if context else [],
                },
            )
        except Exception as e:
            logger.error("Stream error: %s", e)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/archive")
async def archive(req: ArchiveRequest):
    """归档有价值的回答回 Wiki"""
    path = archive_answer(req.question, req.answer, req.topic)
    return {"status": "archived", "path": path}


@router.post("/lint", response_model=LintResponse)
async def lint():
    """Lint 操作：Wiki 健康检查"""
    report = run_lint()
    return LintResponse(
        total_articles=report["total_articles"],
        issues=report["issues"],
        auto_fixed=report["auto_fixed"],
    )


@router.get("/health", response_model=HealthResponse)
async def health():
    """健康检查"""
    return HealthResponse(
        status="ok",
        wiki_articles=len(list_articles()),
        raw_sources=len(list_raw()),
    )


# --- Conversation CRUD ---

@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations():
    db = SessionLocal()
    try:
        convs = db.query(Conversation).order_by(Conversation.updated_at.desc()).all()
        return [
            ConversationResponse(
                id=c.id,
                title=c.title,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
                message_count=len(c.messages),
            )
            for c in convs
        ]
    finally:
        db.close()


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(req: ConversationCreate):
    db = SessionLocal()
    try:
        conv = Conversation(id=str(uuid.uuid4()), title=req.title)
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return ConversationResponse(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat(),
            message_count=0,
        )
    finally:
        db.close()


@router.get("/conversations/{conv_id}", response_model=ConversationDetail)
async def get_conversation(conv_id: str):
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return ConversationDetail(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat(),
            messages=[
                MessageSchema(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    meta_json=m.meta_json,
                    created_at=m.created_at.isoformat(),
                )
                for m in conv.messages
            ],
        )
    finally:
        db.close()


@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        db.delete(conv)
        db.commit()
        return {"status": "deleted", "id": conv_id}
    finally:
        db.close()


@router.get("/cache/stats")
async def cache_statistics():
    """缓存命中率统计"""
    return cache_stats()
