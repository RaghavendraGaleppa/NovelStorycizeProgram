import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings

logger = logging.getLogger(__name__)

# Module-level references managed by lifespan
_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> None:
    """Initialize MongoDB connection and create indexes."""
    global _client, _database
    settings = get_settings()

    logger.info("Connecting to MongoDB at %s:%s ...", settings.MONGO_HOST, settings.MONGO_PORT)
    _client = AsyncIOMotorClient(settings.mongo_uri)
    _database = _client[settings.MONGO_DB]

    # Create indexes
    await _database.novels.create_index("novel_url", unique=True)
    await _database.chapter_info.create_index("novel_id")
    await _database.chapter_info.create_index(
        [("novel_id", 1), ("chapter_num", 1)], unique=True
    )

    logger.info("MongoDB connected. Database: %s", settings.MONGO_DB)


async def close_mongo_connection() -> None:
    """Close MongoDB connection."""
    global _client, _database
    if _client is not None:
        _client.close()
        _client = None
        _database = None
        logger.info("MongoDB connection closed.")


def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance. Must be called after connect_to_mongo()."""
    if _database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return _database
