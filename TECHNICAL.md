# knowledge-base 技术说明

## 一句话概括

企业级知识库系统——Vue 3 前端 + FastAPI 后端 + 本地 Ollama LLM + RAG 混合检索 + 反幻觉五层防御，支持 SSE 流式输出和对话持久化。

## 解决了什么问题

```
传统 RAG：每次查询从碎片中重新发现知识 → Token 浪费 + 无积累
LLM Wiki：编译时整理知识 → 查询时直接读文章 → 越用越丰富
          但有幻觉风险：LLM 编译时可能编造信息

本系统：LLM Wiki 模型 + 自动验证 + 置信度标记 + RAG 回退
       + Vue 3 前端 + 本地 LLM（零 API 成本）
```

## 架构

```
┌─ frontend/ (Vue 3 + Element Plus + Vite) ───────────────────┐
│  AppShell ─┬─ QueryView   (问答，SSE 流式，对话历史侧边栏)  │
│            ├─ IngestView  (录入资料表单)                     │
│            ├─ LintView    (健康检查面板)                     │
│            └─ ArchiveView (归档表单)                         │
└──────────────────────┬───────────────────────────────────────┘
                       │ Axios + SSE fetch
                       ▼
┌─ FastAPI REST API ──────────────────────────────────────────┐
│  POST /api/v1/query          — 问答（阻塞返回）             │
│  POST /api/v1/query/stream   — 问答（SSE 流式逐字返回）     │
│  POST /api/v1/ingest         — raw → wiki 编译 + 验证       │
│  POST /api/v1/lint           — 6 项健康检查                 │
│  POST /api/v1/archive        — 归档回 wiki                   │
│  GET  /api/v1/health         — 服务状态                      │
│  GET  /api/v1/conversations  — 对话列表 CRUD                │
│  GET  /api/v1/cache/stats    — 缓存命中统计                  │
└──────────────────────┬───────────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
   services/        store/          models/
   ├─ compiler     ├─ vector_store  ├─ schemas
   ├─ verifier     ├─ wiki_store    └─ (Pydantic)
   ├─ router       ├─ raw_store
   ├─ searcher     ├─ db (SQLite)
   ├─ rewriter     └─ chroma_db/
   ├─ linter
   ├─ archiver
   ├─ cache (Redis + 内存)
   └─ llm_client (Ollama OpenAI 兼容)
```

## 核心设计

### 1. 双知识管道 + Query Rewrite

| 路径 | Token | 适用 | 原理 |
|------|-------|------|------|
| wiki_direct | ~1.5K | 简单事实型 | 读 index → 读 1-2 篇文章 → 回答 |
| rag_search | ~5K | 复杂综合型 | Query Rewrite → 混合检索 → RRF → Rerank → 回答 |

路由前对问题做 Query Rewrite：消歧义、扩展同义词、拆分子问题，提升检索命中率。

### 2. 三阶段检索

```
用户问题
  → Query Rewrite（LLM 消歧义 + 扩展）
     → RRF 混合检索（向量语义 + 关键词命中双路召回）
        → Cross-Encoder Rerank（BGE-reranker-v2-m3 精排）
```

### 3. 反幻觉五层防御

| 层 | 机制 | 实现 |
|---|------|------|
| L1 | 编译后验证 | `verifier.py` 逐条对照 raw 原文，找支持证据 |
| L2 | 置信度标记 | `[已验证]` `[推断]` `[未验证]` 三段式 |
| L3 | Git PR 审核 | Wiki 是 Git 仓库，LLM 编译 = commit，人类 review = merge |
| L4 | Lint 扫描 | 死引用、索引一致性、孤立声明、重复内容、矛盾检测、时效性 — 6 项 |
| L5 | 查询引用锁定 | 回答时必须带具体文件路径，无来源就说"没有记录" |

### 4. LLM Wiki 模型（Karpathy 理念）

```
raw/           ← 不可变原始资料，LLM 只读
wiki/          ← LLM 维护的结构化文章，持续更新
wiki/index.md  ← 全局索引，每个页面一条摘要
wiki/log.md    ← 操作日志，append-only
```

每次 Ingest：读 raw → 编译 wiki 文章 → 更新 index → 更新交叉引用 → 写 log。
每次 Query：读 index → 找相关文章 → 综合回答 → 归档（如果有价值）。

### 5. 验证循环

```
编译 Agent 产出 wiki 页面
    ↓
验证 Agent 逐条检查：
  "Transformer 于 2017 年提出" → raw 原文有 → [已验证]
  "由 Google Brain 团队发表" → raw 原文没有 → [未验证] ⚠️
    ↓
标记后的 wiki 页面：读者一眼能看到哪些是可以信任的
```

### 6. SSE 流式输出

`POST /api/v1/query/stream` 端点在回答生成时逐 token 推送到前端。前端用 fetch + ReadableStream 解析 SSE 事件，增量追加到聊天气泡。支持随时中止。

### 7. 对话持久化

SQLAlchemy + SQLite 存储对话和消息。前端左侧对话列表支持新建/切换/删除。刷新页面消息不丢失。

## 技术栈

| 层级 | 组件 | 原因 |
|------|------|------|
| 前端 | Vue 3 + Element Plus + Vite | Composition API、中文组件库、快速 HMR |
| LLM | Ollama (qwen3:8b) | 本地运行，零 API 成本，OpenAI 兼容接口 |
| 向量库 | ChromaDB | 轻量本地运行，索引 wiki/ 目录 |
| Embedding | BAAI/bge-small-zh-v1.5 | 中文 SOTA，本地 CPU 运行 |
| Reranker | BAAI/bge-reranker-v2-m3 | 交叉编码器精排，提升检索精度 |
| 后端 | FastAPI | 异步、自动生成 OpenAPI 文档、支持 SSE |
| 缓存 | Redis + 内存 | 热点问题零 Token 返回，ingest 自动失效 |
| 存储 | SQLAlchemy + SQLite | 对话持久化，轻量零配置 |

## 全部端点

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | /api/v1/query | 问答（阻塞返回完整响应） |
| POST | /api/v1/query/stream | 问答（SSE 流式逐 token 返回） |
| POST | /api/v1/ingest | 录入原始资料 → 编译 → 验证 |
| POST | /api/v1/lint | 6 项 Wiki 健康检查 |
| POST | /api/v1/archive | 有价值回答归档回 Wiki |
| GET | /api/v1/health | 服务健康状态 |
| GET/POST | /api/v1/conversations | 对话列表 / 新建 |
| GET/DELETE | /api/v1/conversations/{id} | 对话详情 / 删除 |
| GET | /api/v1/cache/stats | 缓存命中率统计 |

## 面试能讲的故事线

面试官：你做的最有深度的项目是什么？

你：企业级知识库。它把两种知识管理范式融合了——RAG 的检索能力和 Karpathy LLM Wiki 的知识积累能力。

核心技术挑战有四个：

1. **Token 优化 + Query Rewrite**：我设计了一个意图路由器，简单问题直接读 Wiki（1.5K token），复杂问题走混合检索（5K token）。检索前做 Query Rewrite 消歧义，检索后用 Cross-Encoder Reranker 精排，保证召回质量。

2. **反幻觉机制**：LLM 编译 Wiki 时可能编造信息，我做了五层防御——编译后自动验证、置信度标记、6 项 Lint 扫描（包括死引用、矛盾检测、时效性检查）、查询引用锁定。

3. **SSE 流式输出**：用 Server-Sent Events 实现 Token 级别流式推送，前端 fetch + ReadableStream 解析，支持随时中止，用户感知延迟大幅降低。

4. **本地部署**：整个系统完全本地运行——qwen3:8b 处理所有 LLM 调用，ChromaDB 向量检索，SQLite 持久化。零 API 成本，数据不出本地。

## 文件清单

| 文件 | 作用 |
|------|------|
| `main.py` | FastAPI 入口，serve 前端静态文件 |
| `config.py` | 环境变量配置 |
| `models/schemas.py` | Pydantic 数据模型 |
| `routers/api.py` | 全部 API 端点 |
| `services/compiler.py` | raw → wiki 编译 |
| `services/verifier.py` | 反幻觉验证 |
| `services/router.py` | 意图路由（优化 Prompt + guard） |
| `services/query_rewriter.py` | 查询改写 |
| `services/searcher.py` | 双路径检索（集成 Rewrite） |
| `services/linter.py` | Wiki 健康检查（6 项） |
| `services/archiver.py` | 查询归档 |
| `services/cache.py` | Redis/内存缓存（连接池 + 统计） |
| `services/llm_client.py` | LLM 客户端（chat_text + chat_text_stream） |
| `store/vector_store.py` | ChromaDB + RRF + Rerank |
| `store/wiki_store.py` | Wiki 文件读写 |
| `store/raw_store.py` | Raw 源文件读写 |
| `store/db.py` | SQLAlchemy 对话持久化 |
| `frontend/` | Vue 3 SPA（见 `frontend/src/`） |

## 启动方式

```bash
# 开发模式
cd frontend && npm run dev    # Vite :5173，代理 API
python main.py                # FastAPI :8000

# 生产模式
cd frontend && npm run build  # 构建静态文件
python main.py                # 访问 http://127.0.0.1:8000
```
