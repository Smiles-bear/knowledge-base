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
from services.context_compressor import compress as compress_context
from services.semantic_cache import lookup as semantic_lookup, store as semantic_store, invalidate_all as semantic_invalidate
from store.raw_store import save_raw, list_raw
from store.wiki_store import list_articles
from store.db import SessionLocal, Conversation, Message
import uuid
from datetime import datetime, timezone

import os
from store.wiki_store import list_articles

WIKI_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wiki")


def _build_page_tree(article_paths: list[str]) -> list[dict]:
    """将扁平的 wiki/ 路径列表构建为嵌套页面树"""
    tree: dict[str, dict] = {}
    for path in sorted(article_paths):
        path = path.replace("\\", "/")
        if path.endswith(".md"):
            path = path[:-3]
        parts = [p for p in path.split("/") if p]
        node = tree
        for i, part in enumerate(parts):
            if part not in node:
                node[part] = {"_children": {}}
            if i == len(parts) - 1:
                node[part]["_leaf"] = True
            node = node[part]["_children"]

    def convert(node: dict, prefix: str = "") -> list[dict]:
        result = []
        for name, data in node.items():
            full_path = f"{prefix}/{name}" if prefix else name
            children = convert(data.get("_children", {}), full_path)
            result.append({
                "path": full_path,
                "title": name.replace("-", " ").replace("_", " ").title(),
                "children": children,
            })
        return result

    return convert(tree)


def _read_wiki_doc(rel_path: str) -> dict | None:
    """读取单篇 wiki 文档，返回 {path, title, content, confidence, updated_at, stats}"""
    rel_path = rel_path.strip("/")
    md_path = os.path.join(WIKI_DIR, rel_path + ".md")
    if not os.path.isfile(md_path):
        return None
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    title = rel_path.split("/")[-1].replace("-", " ").replace("_", " ").title()
    for line in content.split("\n"):
        if line.startswith("# "):
            title = line[2:].strip()
            break
    statements = len([l for l in content.split("\n") if l.strip() and not l.startswith("#")])
    references = len([l for l in content.split("\n") if l.startswith(">")])
    stat = os.stat(md_path)
    from datetime import datetime, timezone
    return {
        "path": rel_path,
        "title": title,
        "content": content,
        "confidence": "verified" if "[已验证]" in content else ("inferred" if "[推断]" in content else "unverified"),
        "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "stats": {"statements": statements, "references": references},
    }


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
    semantic_invalidate()

    # 增量重建向量索引，让新知识立即可检索
    try:
        from store.vector_store import VectorStore
        VectorStore().build_index()
    except Exception as e:
        logger.warning("向量索引重建失败: %s", e)

    return IngestResponse(
        status="completed",
        wiki_path=result.get("path", ""),
        confidence=result.get("confidence", "unknown"),
        verified_claims=verified,
        flagged_claims=flagged,
    )


def _load_history(session_id: str | None) -> tuple[str, str | None]:
    """加载对话历史，返回 (history_text, title)"""
    if not session_id:
        return "", None
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == session_id).first()
        if not conv:
            return "", None
        messages = conv.messages[-10:]  # 最近 10 条
        lines = []
        for m in messages:
            role = "用户" if m.role == "user" else "助手"
            lines.append(f"{role}：{m.content}")
        return "\n".join(lines), conv.title
    finally:
        db.close()


def _save_message(session_id: str, role: str, content: str):
    """保存消息到对话"""
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == session_id).first()
        if not conv:
            conv = Conversation(id=session_id, title=content[:30])
            db.add(conv)
        msg = Message(conversation_id=session_id, role=role, content=content)
        db.add(msg)
        conv.updated_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as e:
        logger.warning("保存消息失败: %s", e)
    finally:
        db.close()


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """Query 操作：意图路由 → 检索 → 多轮对话 → 回答"""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    # 三级缓存查找：精确 → 语义 → 生成
    if not req.session_id:
        cached = cache_get(req.question)
        if not cached:
            cached = semantic_lookup(req.question)
        if cached:
            return QueryResponse(**cached)

    # 加载对话历史
    history, _ = _load_history(req.session_id)

    # 意图路由
    route_info = route(req.question)

    # 检索
    context = search(req.question, route_info)
    context = compress_context(context) if context else context

    # 构建 Prompt（含历史）
    system_prompt = QUERY_SYSTEM
    if history:
        system_prompt += f"\n\n## 对话历史（用于理解上下文和指代）\n{history}\n---\n请基于以上历史理解用户意图，结合知识库内容回答当前问题。"

    user_msg = f"知识库内容：\n{context}\n\n问题：{req.question}" if context else req.question
    answer = chat_text(system_prompt, user_msg)

    token_est = {"wiki_direct": 1500, "wiki_with_links": 3000, "rag_search": 5000, "simple_chat": 500}.get(
        route_info.get("route", "rag_search"), 3000
    )

    # 保存对话消息
    session_id = req.session_id or str(uuid.uuid4())
    _save_message(session_id, "user", req.question)
    _save_message(session_id, "assistant", answer)

    response = QueryResponse(
        answer=answer,
        route=route_info.get("route", "rag_search"),
        route_reason=route_info.get("reason", ""),
        token_estimate=token_est,
        sources=[s.split("\n")[0] for s in context.split("---")][:5] if context else [],
        session_id=session_id,
    )

    # 写入缓存
    if not req.session_id:
        cache_set(req.question, response.model_dump())
        semantic_store(req.question, response.model_dump())

    return response


@router.post("/query/stream")
async def query_stream(req: QueryRequest):
    """Query 操作（SSE 流式 + 多轮对话）：Token 逐字返回"""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    if not req.session_id:
        cached = cache_get(req.question)
        if not cached:
            cached = semantic_lookup(req.question)
        if cached:
            import json as _json

            async def cached_stream():
                yield f"data: {_json.dumps({'type': 'complete', 'data': cached}, ensure_ascii=False)}\n\n"

            return StreamingResponse(cached_stream(), media_type="text/event-stream")

    history, _ = _load_history(req.session_id)
    route_info = route(req.question)
    context = search(req.question, route_info)
    context = compress_context(context) if context else context

    system_prompt = QUERY_SYSTEM
    if history:
        system_prompt += f"\n\n## 对话历史（用于理解上下文和指代）\n{history}\n---\n请基于以上历史理解用户意图，结合知识库内容回答当前问题。"

    user_msg = f"知识库内容：\n{context}\n\n问题：{req.question}" if context else req.question
    session_id = req.session_id or str(uuid.uuid4())
    _save_message(session_id, "user", req.question)

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
            for token in chat_text_stream(system_prompt, user_msg):
                full_answer.append(token)
                yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"

            # 完成
            answer = "".join(full_answer)
            _save_message(session_id, "assistant", answer)
            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id}, ensure_ascii=False)}\n\n"

            # 写缓存
            token_est = {"wiki_direct": 1500, "wiki_with_links": 3000, "rag_search": 5000, "simple_chat": 500}.get(
                route_info.get("route", "rag_search"), 3000
            )
            if not req.session_id:
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


@router.get("/wiki/tree")
async def wiki_tree():
    """返回 Wiki 页面树结构"""
    articles = list_articles()
    if isinstance(articles, dict):
        articles = list(articles.keys())
    if articles and isinstance(articles[0], dict):
        articles = [a.get("path", "") for a in articles]
    tree = _build_page_tree(articles)
    return {"pages": tree}


@router.get("/wiki/{path:path}")
async def wiki_doc(path: str):
    """返回单篇 Wiki 文档"""
    doc = _read_wiki_doc(path)
    if not doc:
        raise HTTPException(status_code=404, detail=f"文档不存在: {path}")
    return doc


@router.get("/search")
async def wiki_search(q: str = ""):
    """全文搜索 wiki 文档"""
    if not q.strip():
        return {"query": q, "results": []}
    articles = list_articles()
    if isinstance(articles, dict):
        articles = list(articles.keys())
    if articles and isinstance(articles[0], dict):
        articles = [a.get("path", "") for a in articles]

    results = []
    q_lower = q.lower()
    for path in sorted(articles):
        path = path.replace("\\", "/")
        if path.endswith(".md"):
            path = path[:-3]
        title = path.split("/")[-1].replace("-", " ").replace("_", " ").lower()
        score = 0.0
        if q_lower in title:
            score = 0.9
        elif any(w in title for w in q_lower.split()):
            score = 0.5
        if score > 0:
            doc = _read_wiki_doc(path)
            snippet = ""
            if doc:
                for line in doc["content"].split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        snippet = line[:120]
                        break
            results.append({
                "path": path,
                "title": path.split("/")[-1].replace("-", " ").replace("_", " ").title(),
                "snippet": snippet,
                "score": round(score, 2),
            })
    results.sort(key=lambda r: r["score"], reverse=True)
    return {"query": q, "results": results[:20]}
