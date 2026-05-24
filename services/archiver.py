"""归档服务：有价值的回答保存回 Wiki（查询归档）"""
import logging
from datetime import date
from store.wiki_store import write_article, update_index, append_log

logger = logging.getLogger(__name__)


def archive_answer(question: str, answer: str, topic: str = "archived") -> str:
    """将好的回答归档为 Wiki 页面，标记 [Archived]"""
    slug = question.lower().replace(" ", "-").replace("？", "").replace("?", "")[:50]
    today = date.today().isoformat()

    content = f"""# {question}

> 类型: [Archived] · 归档时间: {today}

## 回答

{answer}

---
*此页面从对话记录自动归档。原文可能经过人工编辑。*
"""
    path = write_article(topic, slug, content)
    update_index([{
        "title": question,
        "topic": topic,
        "slug": slug,
        "summary": f"[Archived] {answer[:80]}...",
    }])
    append_log("archive", f"Archived: {question[:80]}")
    logger.info("归档完成: %s", path)
    return path
