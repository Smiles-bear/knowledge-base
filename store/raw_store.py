"""Raw 源文件操作：只读，不可变"""
import os
import logging
from datetime import date
from config import RAW_DIR

logger = logging.getLogger(__name__)


def ensure_raw():
    os.makedirs(RAW_DIR, exist_ok=True)


def save_raw(topic: str, title: str, content: str, source_url: str = "") -> str:
    ensure_raw()
    d = os.path.join(RAW_DIR, topic)
    os.makedirs(d, exist_ok=True)
    slug = title.lower().replace(" ", "-")[:60]
    today = date.today().isoformat()
    fname = f"{today}-{slug}.md"
    path = os.path.join(d, fname)
    header = f"# {title}\n\n> Source: {source_url}\n> Collected: {today}\n\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + content)
    return path


def read_raw(path: str) -> str | None:
    full = os.path.join(RAW_DIR, path) if not path.startswith(RAW_DIR) else path
    if not os.path.exists(full):
        return None
    with open(full, "r", encoding="utf-8") as f:
        return f.read()


def list_raw() -> list[str]:
    if not os.path.exists(RAW_DIR):
        return []
    files = []
    for root, _, filenames in os.walk(RAW_DIR):
        for f in filenames:
            if f.endswith(".md"):
                files.append(os.path.relpath(os.path.join(root, f), RAW_DIR))
    return sorted(files)
