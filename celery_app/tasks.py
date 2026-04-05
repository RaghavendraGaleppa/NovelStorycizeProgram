"""
Celery task definitions — placeholder for future phases.

Future tasks will include:
- Chapter content parsing
- Story summarization / "storycizing"
- Audio generation / transcription
"""

from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "novel_storycize",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


# ---- Future task stubs ----

@celery_app.task(name="tasks.parse_chapter")
def parse_chapter(chapter_id: str):
    """Parse raw chapter content from novelbin. (Phase 2)"""
    raise NotImplementedError("parse_chapter is not yet implemented.")


@celery_app.task(name="tasks.storycize_chapter")
def storycize_chapter(chapter_id: str):
    """Summarize/storycize a parsed chapter. (Phase 3)"""
    raise NotImplementedError("storycize_chapter is not yet implemented.")
