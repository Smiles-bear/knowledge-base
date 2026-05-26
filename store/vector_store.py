"""向量存储：ChromaDB + BGE Embedding，只索引 wiki/ 目录"""
import os
import re
import logging
import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder
from config import CHROMA_DIR, WIKI_DIR, CHUNK_SIZE, CHUNK_OVERLAP, RERANKER_MODEL

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self):
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        self.client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.collection = self.client.get_or_create_collection("wiki_knowledge")
        self._reranker = None

    def _get_reranker(self):
        if self._reranker is None:
            logger.info("Loading cross-encoder reranker: %s", RERANKER_MODEL)
            self._reranker = CrossEncoder(RERANKER_MODEL)
        return self._reranker

    def rerank(self, query: str, candidates: list[str], top_k: int = 3) -> list[str]:
        """Cross-encoder 重排序候选文档"""
        if len(candidates) <= 1:
            return candidates
        reranker = self._get_reranker()
        pairs = [[query, doc] for doc in candidates]
        scores = reranker.predict(pairs)
        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        logger.info("Reranked %d candidates -> top %d", len(candidates), top_k)
        return [doc for doc, _ in ranked[:top_k]]

    def _chunk_markdown(self, text, source):
        """按 ## 标题分块，保持 wiki 页面结构"""
        sections = re.split(r"\n(?=## )", text)
        chunks = []
        for section in sections:
            if len(section) > CHUNK_SIZE:
                for i in range(0, len(section), CHUNK_SIZE - CHUNK_OVERLAP):
                    chunk = section[i : i + CHUNK_SIZE]
                    if chunk.strip():
                        chunks.append({"text": chunk, "source": source, "index": len(chunks)})
            elif section.strip():
                chunks.append({"text": section.strip(), "source": source, "index": len(chunks)})
        return chunks

    def load_wiki_files(self):
        documents = []
        if not os.path.exists(WIKI_DIR):
            return documents
        for root, _, files in os.walk(WIKI_DIR):
            for fname in files:
                if fname.endswith(".md"):
                    path = os.path.join(root, fname)
                    rel = os.path.relpath(path, WIKI_DIR)
                    with open(path, "r", encoding="utf-8") as f:
                        documents.extend(self._chunk_markdown(f.read(), rel))
        return documents

    def build_index(self):
        docs = self.load_wiki_files()
        if not docs:
            logger.warning("wiki/ 目录为空")
            return
        existing = self.collection.get()
        if existing["ids"]:
            self.collection.delete(ids=existing["ids"])
        texts = [d["text"] for d in docs]
        embeddings = self.embedder.encode(texts).tolist()
        metadatas = [{"source": d["source"], "index": d["index"]} for d in docs]
        ids = [f"{d['source']}_{d['index']}" for d in docs]
        self.collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        logger.info("向量索引完成: %d 块, %d 文件", len(docs), len(set(d["source"] for d in docs)))

    def _vector_search(self, query, top_k):
        emb = self.embedder.encode([query]).tolist()
        results = self.collection.query(query_embeddings=emb, n_results=top_k)
        return results["documents"][0] if results["documents"] else []

    def _keyword_search(self, query, top_k):
        docs = self.load_wiki_files()
        if not docs:
            return []
        keywords = set(re.findall(r"[一-鿿]+|[a-zA-Z]+", query.lower()))
        if not keywords:
            return []
        scored = [(d["text"], sum(1 for kw in keywords if kw in d["text"].lower())) for d in docs]
        scored = [(t, s) for t, s in scored if s > 0]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [t for t, _ in scored[:top_k]]

    def search(self, query, top_k=3, rerank=True):
        """混合检索（RRF 融合 + 可选 cross-encoder 重排序）"""
        vec = self._vector_search(query, top_k * 2)
        kw = self._keyword_search(query, top_k * 2)
        if not kw:
            candidates = vec[:top_k]
        elif not vec:
            candidates = kw[:top_k]
        else:
            scores = {}
            for rank, text in enumerate(vec):
                scores[text] = scores.get(text, 0) + 1.0 / (60 + rank + 1)
            for rank, text in enumerate(kw):
                scores[text] = scores.get(text, 0) + 1.0 / (60 + rank + 1)
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            candidates = [t for t, _ in ranked[:top_k * 2]]

        # Cross-encoder rerank
        if rerank and len(candidates) > top_k:
            candidates = self.rerank(query, candidates, top_k)
        else:
            candidates = candidates[:top_k]

        return candidates
