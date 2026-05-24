# Enterprise Knowledge Base / 企业级知识库

**RAG + Karpathy LLM Wiki + Anti-Hallucination Verification**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)

An enterprise-grade knowledge base system that combines RAG (Retrieval-Augmented Generation) with Karpathy's LLM Wiki model and a five-layer anti-hallucination defense. Designed for teams that need trusted, compoundable knowledge.

结合 RAG 和 Karpathy LLM Wiki 模式的企业级知识库系统，内置五层反幻觉防御机制。

---

## Architecture / 架构

```
                    ┌─────────────┐
                    │  User Query  │
                    └──────┬──────┘
                           │
              ┌────────────▼────────────┐
              │    Intent Router         │
              │    wiki_direct (~1.5K)   │
              │    rag_search (~5K)      │
              └──────┬──────────┬───────┘
                     │          │
        ┌────────────▼──┐  ┌───▼────────────┐
        │  Wiki Direct   │  │  RAG Search     │
        │  Read index    │  │  Hybrid(向量+KW) │
        │  Read articles │  │  RRF Re-rank    │
        └──────┬─────────┘  └───┬─────────────┘
               │                │
        ┌──────▼────────────────▼──────┐
        │      LLM Answer + Cite       │
        └──────────────┬───────────────┘
                       │
        ┌──────────────▼───────────────┐
        │  Archive (if valuable)       │
        │  Write back to wiki/         │
        └──────────────────────────────┘
```

## Key Features / 核心功能

### 1. Dual Knowledge Pipeline / 双知识管道

| Mode | Token Cost | Use Case |
|------|-----------|----------|
| **Wiki Direct** | ~1.5K | Simple factual questions |
| **RAG Hybrid Search** | ~5K | Complex cross-topic queries |

### 2. Karpathy LLM Wiki Model

- **Ingest**: Raw sources → LLM compiles into structured wiki articles
- **Cross-references**: Auto-maintained links between related concepts
- **Index + Log**: `wiki/index.md` catalog + `wiki/log.md` operation timeline
- **Compounds over time**: Each new source updates multiple pages

### 3. Five-Layer Anti-Hallucination Defense / 五层反幻觉防御

| Layer | Mechanism | Description |
|-------|-----------|-------------|
| L1 | Compile-Verify | Every claim checked against raw source after compilation |
| L2 | Confidence Tags | `[Verified]` `[Inferred]` `[Unverified]` on every statement |
| L3 | Git PR Review | LLM compiles → human reviews diff → merge |
| L4 | Lint Scanner | Dead references, contradictions, claim drift detection |
| L5 | Citation Lock | Query answers must cite specific file + line number |

### 4. Token Optimization / Token 优化

```
Intent Router: 1 prompt → choose cheapest path
Query Archive: good answers saved as wiki pages → cache hit = 0 token
Redis Cache: identical queries return cached result
```

### 5. Enterprise Ready / 企业级

- FastAPI with auto-generated OpenAPI docs (`/docs`)
- SQLAlchemy ORM (SQLite dev / PostgreSQL prod)
- Redis caching with memory fallback
- Structured logging (stderr)
- Docker Compose deployment

## Quick Start / 快速开始

### Install / 安装

```bash
git clone https://github.com/Smiles-bear/knowledge-base.git
cd knowledge-base
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Configure / 配置

Edit `.env`:

```env
DEEPSEEK_API_KEY=your-key-here
DATABASE_URL=sqlite:///./knowledge.db
REDIS_URL=redis://localhost:6379/0
```

### Run / 启动

```bash
uvicorn main:app --reload
# Open http://localhost:8000/docs for API docs
```

### Docker / Docker 部署

```bash
docker-compose up -d
```

## API Endpoints / API 端点

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/ingest` | Ingest raw source → compile → verify |
| `POST` | `/api/v1/query` | Query with intent routing + citation |
| `POST` | `/api/v1/lint` | Wiki health check + anti-hallucination scan |
| `POST` | `/api/v1/archive` | Archive good answers back to wiki |
| `GET` | `/api/v1/health` | Health check + stats |

### Example / 示例

**Ingest:**

```json
POST /api/v1/ingest
{
  "content": "# AI Agent 开发入门\n\n## 什么是 Agent\nAgent 是...",
  "title": "AI Agent 开发入门",
  "topic": "ai",
  "source_url": "https://example.com/agent-intro"
}
```

**Query:**

```json
POST /api/v1/query
{
  "question": "Agent 有哪几个核心组成部分？"
}

Response:
{
  "answer": "根据知识库，Agent 核心组成包括：1. LLM...",
  "route": "wiki_direct",
  "token_estimate": 1500,
  "sources": ["wiki/ai/agent-intro.md"]
}
```

## Project Structure / 项目结构

```
knowledge-base/
├── main.py              # FastAPI entry point
├── config.py             # Environment configuration
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── models/
│   └── schemas.py        # Pydantic data models
├── routers/
│   └── api.py            # 5 API endpoints
├── services/
│   ├── compiler.py       # raw → wiki compilation
│   ├── verifier.py       # Anti-hallucination verification
│   ├── router.py         # Intent routing (token optimization)
│   ├── searcher.py       # Wiki direct + RAG hybrid search
│   ├── linter.py         # Wiki health checks
│   ├── archiver.py       # Query answer archiving
│   ├── cache.py          # Redis/memory dual cache
│   └── llm_client.py     # Unified LLM client
├── store/
│   ├── vector_store.py   # ChromaDB + BGE Embedding
│   ├── wiki_store.py     # Wiki file operations
│   └── raw_store.py      # Immutable raw source storage
├── wiki/                 # LLM-maintained knowledge pages
│   ├── index.md          # Global catalog
│   └── log.md            # Operation timeline
└── raw/                  # Immutable source material
```

## Technical Stack / 技术栈

| Layer | Component | Reason |
|-------|-----------|--------|
| LLM | DeepSeek API | Cost-effective, Chinese-optimized |
| Vector DB | ChromaDB | Lightweight, local, Python-native |
| Embedding | BAAI/bge-small-zh-v1.5 | Top Chinese performance, local |
| Backend | FastAPI | Async, auto OpenAPI docs |
| Cache | Redis + Memory | Graceful degradation |
| DB | SQLAlchemy + SQLite/PostgreSQL | Flexible storage |

## Design Decisions / 设计决策

### Why LLM Wiki over pure RAG? / 为什么用 LLM Wiki 而不是纯 RAG？

> RAG re-discovers knowledge on every query. LLM Wiki compiles once, queries forever.
> RAG 每次查询重新发现知识。LLM Wiki 编译一次，终身受益。

### Why multi-layer verification? / 为什么多层验证？

> LLMs hallucinate during compilation. Verification catches fabrications before they enter the knowledge base.
> LLM 编译时会产生幻觉。验证在编造信息进入知识库之前拦截。

### Why intent routing? / 为什么意图路由？

> Simple questions don't need 5K tokens of RAG context. A 100-token routing decision saves 60% per query.
> 简单问题不需要 5K token 的 RAG 上下文。100 token 的路由决策每次查询节省 60%。

## Inspired By / 灵感来源

- [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — The original idea
- [karpathy-llm-wiki](https://github.com/Astro-Han/karpathy-llm-wiki) — Agent Skills implementation

## License / 许可证

MIT
