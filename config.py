import os

_ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_ENV_FILE):
    with open(_ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./knowledge.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw")
WIKI_DIR = os.path.join(BASE_DIR, "wiki")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
HIGH_CONFIDENCE_THRESHOLD = 2
VERIFY_ENABLED = True
