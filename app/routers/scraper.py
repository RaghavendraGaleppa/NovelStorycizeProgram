import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.database import get_database
from app.models.novel import Novel
from app.models.chapter_info import ChapterInfo
from app.scraper.novelbin import novelbin_scraper, NovelBinScraper

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["scraper"])


class ScrapeRequest(BaseModel):
    """Request body for the scrape endpoint."""
    novel_url: str = Field(
        ...,
        description="URL of a novelbin.me novel page",
        json_schema_extra={"examples": ["https://novelbin.me/novel-book/cultivating-disciples-to-breakthrough"]},
    )


class ScrapeResponse(BaseModel):
    """Response from the scrape endpoint."""
    status: str = Field(..., description="'created' or 'already_exists'")
    novel: dict = Field(..., description="Novel metadata")
    chapters_count: int = Field(..., description="Number of chapters")


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_novel(request: ScrapeRequest):
    """
    Scrape a novel from novelbin.me and save to database.

    - If the novel already exists in the database, returns existing data.
    - If not, scrapes metadata + chapter list and persists everything.
    """
    db = get_database()

    # Normalize the URL
    normalized_url = NovelBinScraper.normalize_url(request.novel_url)

    # Validate it's a novelbin URL
    if "novelbin.me/novel-book/" not in normalized_url:
        raise HTTPException(
            status_code=400,
            detail="Invalid URL. Must be a novelbin.me novel page URL "
                   "(e.g., https://novelbin.me/novel-book/novel-name).",
        )

    # Check if already scraped
    existing = await db.novels.find_one({"novel_url": normalized_url})
    if existing:
        logger.info("Novel already exists: %s", normalized_url)
        # Count chapters using ObjectId before converting to string
        chapter_count = await db.chapter_info.count_documents(
            {"novel_id": existing["_id"]}
        )
        # Convert ObjectId to string for JSON serialization
        existing["_id"] = str(existing["_id"])
        return ScrapeResponse(
            status="already_exists",
            novel=existing,
            chapters_count=chapter_count,
        )

    # Scrape the novel
    try:
        logger.info("Starting scrape for: %s", normalized_url)
        novel_data = await novelbin_scraper.scrape_all(normalized_url)
    except Exception as e:
        logger.error("Scraping failed for %s: %s", normalized_url, str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scrape novel: {str(e)}",
        )

    # Create Novel document
    novel = Novel(
        title=novel_data.title,
        novel_url=novel_data.novel_url,
        author=novel_data.author,
        description=novel_data.description,
        n_chapters=novel_data.n_chapters,
    )

    # Insert novel into DB
    novel_result = await db.novels.insert_one(novel.to_mongo_dict())
    novel_id = novel_result.inserted_id
    logger.info("Novel inserted with _id: %s", novel_id)

    # Build chapter documents
    chapter_docs = []
    for ch in novel_data.chapters:
        chapter = ChapterInfo(
            novel_id=novel_id,
            chapter_num=ch.chapter_num,
            chapter_url=ch.chapter_url,
            chapter_title=ch.chapter_title,
        )
        chapter_docs.append(chapter.to_mongo_dict())

    # Bulk insert chapters
    if chapter_docs:
        result = await db.chapter_info.insert_many(chapter_docs)
        logger.info("Inserted %d chapters for novel '%s'.", len(result.inserted_ids), novel_data.title)

    # Build response
    response_novel = novel.to_mongo_dict()
    response_novel["_id"] = str(novel_id)

    return ScrapeResponse(
        status="created",
        novel=response_novel,
        chapters_count=len(chapter_docs),
    )
