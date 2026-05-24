"""Wiki 文件操作：读写 wiki/ 目录、维护 index 和 log"""
import os
import re
import logging
from datetime import date
from config import WIKI_DIR

logger = logging.getLogger(__name__)

def _ensure_wiki():
    os.makedirs(WIKI_DIR, exist_ok=True)
    idx = os.path.join(WIKI_DIR, "index.md")
    if not os.path.exists(idx):
        with open(idx, "w", encoding="utf-8") as f:
            f.write("# Knowledge Base Index\n\n")
    log = os.path.join(WIKI_DIR, "log.md")
    if not os.path.exists(log):
        with open(log, "w", encoding="utf-8") as f:
            f.write("# Wiki Log\n\n")

def _ensure_topic_dir(topic: str) -> str:
    d = os.path.join(WIKI_DIR, topic)
    os.makedirs(d, exist_ok=True)
    return d

def write_article(topic: str, slug: str, content: str) -> str:
    _ensure_wiki()
    d = _ensure_topic_dir(topic)
    path = os.path.join(d, f"{slug}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path

def read_article(path: str) -> str | None:
    full = os.path.join(WIKI_DIR, path) if not path.startswith(WIKI_DIR) else path
    if not os.path.exists(full):
        return None
    with open(full, "r", encoding="utf-8") as f:
        return f.read()

def read_index() -> str:
    idx = os.path.join(WIKI_DIR, "index.md")
    if not os.path.exists(idx):
        return ""
    with open(idx, "r", encoding="utf-8") as f:
        return f.read()

def update_index(entries: list[dict]):
    """entries: [{"title": str, "topic": str, "summary": str}, ...]"""
    idx_path = os.path.join(WIKI_DIR, "index.md")
    existing = read_index()
    for entry in entries:
        line = f"- [{entry['title']}](wiki/{entry['topic']}/{entry['slug']}.md) — {entry.get('summary', '')}"
        if f"({entry['title']})" in existing or f"[{entry['title']}]" in existing:
            existing = re.sub(
                rf"- \[{re.escape(entry['title'])}\].*",
                line, existing
            )
        else:
            existing = existing.rstrip() + "\n" + line + "\n"
    with open(idx_path, "w", encoding="utf-8") as f:
        f.write(existing)

def append_log(operation: str, detail: str, cascade: list[str] | None = None):
    log_path = os.path.join(WIKI_DIR, "log.md")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n## [{date.today().isoformat()}] {operation} | {detail}\n")
        if cascade:
            for c in cascade:
                f.write(f"- Updated: {c}\n")

def list_articles(topic: str | None = None) -> list[str]:
    base = os.path.join(WIKI_DIR, topic) if topic else WIKI_DIR
    if not os.path.exists(base):
        return []
    articles = []
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith(".md") and f not in ("index.md", "log.md"):
                articles.append(os.path.relpath(os.path.join(root, f), WIKI_DIR))
    return sorted(articles)
