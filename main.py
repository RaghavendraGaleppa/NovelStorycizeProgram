import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import connect_to_mongo, close_mongo_connection
from app.scraper.engine import playwright_engine
from app.routers.scraper import router as scraper_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown lifecycle events."""
    # ── Startup ──
    logger.info("Starting up Novel Storycize server...")
    await connect_to_mongo()
    await playwright_engine.startup()
    logger.info("Server ready.")

    yield

    # ── Shutdown ──
    logger.info("Shutting down...")
    await playwright_engine.shutdown()
    await close_mongo_connection()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Novel Storycize API",
    description="Scrape, summarize, and transcribe web novels into audiobooks.",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(scraper_router)


@app.get("/health", tags=["system"])
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}
