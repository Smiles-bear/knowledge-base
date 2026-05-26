from pydantic import BaseModel
from typing import Optional


class IngestRequest(BaseModel):
    content: str
    title: str
    topic: str = "general"
    source_url: str = ""


class IngestResponse(BaseModel):
    status: str
    wiki_path: str
    confidence: str
    verified_claims: int = 0
    flagged_claims: int = 0


class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    route: str
    route_reason: str
    token_estimate: int
    sources: list[str] = []


class ArchiveRequest(BaseModel):
    question: str
    answer: str
    topic: str = "archived"


class LintResponse(BaseModel):
    total_articles: int
    issues: list[dict]
    auto_fixed: list[str]


class HealthResponse(BaseModel):
    status: str
    wiki_articles: int
    raw_sources: int
    modes: list[str] = ["wiki_direct", "rag_search", "ingest", "lint", "archive"]


class ConversationCreate(BaseModel):
    title: str = "New Conversation"


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0


class MessageSchema(BaseModel):
    id: int
    role: str
    content: str
    meta_json: Optional[str] = None
    created_at: str


class ConversationDetail(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[MessageSchema] = []
