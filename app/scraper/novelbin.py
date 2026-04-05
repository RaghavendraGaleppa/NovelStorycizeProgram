import logging
import re
from dataclasses import dataclass, field
from playwright.async_api import Page

from app.scraper.engine import playwright_engine

logger = logging.getLogger(__name__)


@dataclass
class ChapterData:
    """Raw chapter data scraped from the page."""
    chapter_num: int
    chapter_title: str
    chapter_url: str


@dataclass
class NovelData:
    """Raw novel data scraped from the page."""
    title: str
    author: str
    description: str
    novel_url: str
    n_chapters: int
    chapters: list[ChapterData] = field(default_factory=list)


class NovelBinScraper:
    """
    Scraper specialized for novelbin.me novel pages.

    Expected page structure (CSS selectors):
        Title:          h3.title
        Author:         div.info > div:nth-child(1) > a
        Genres:         div.info > div:nth-child(2) > a
        Status:         div.info > div:nth-child(3) > a
        Description:    div.desc-text
        Chapter Tab:    a#tab-chapters-title
        Chapters:       ul.list-chapter li a
    """

    @staticmethod
    def normalize_url(url: str) -> str:
        """
        Normalize a novelbin URL by stripping fragments and trailing slashes.
        e.g. https://novelbin.me/novel-book/xyz#tab-description-title
          -> https://novelbin.me/novel-book/xyz
        """
        # Remove fragment
        url = url.split("#")[0]
        # Remove trailing slash
        url = url.rstrip("/")
        return url

    async def scrape_novel_metadata(self, page: Page) -> dict:
        """
        Extract novel metadata from a novelbin.me novel page.
        Page should already be navigated to the novel URL.

        Returns dict with: title, author, description
        """
        # Title
        title_el = await page.query_selector("h3.title")
        title = (await title_el.inner_text()).strip() if title_el else "Unknown Title"

        # Author — link with href containing /novelbin-author/
        author = "Unknown"
        try:
            author_el = await page.query_selector("a[href*='/novelbin-author/']")
            if author_el:
                author = (await author_el.inner_text()).strip()
        except Exception:
            logger.warning("Could not extract author, defaulting to 'Unknown'.")

        # Description
        description = ""
        try:
            desc_el = await page.query_selector("div.desc-text")
            if desc_el:
                # Get inner text to strip HTML tags
                description = (await desc_el.inner_text()).strip()
        except Exception:
            logger.warning("Could not extract description.")

        return {
            "title": title,
            "author": author,
            "description": description,
        }

    async def scrape_chapter_list(self, page: Page) -> list[ChapterData]:
        """
        Click the 'Chapter List' tab and scrape all chapter links.
        Page should already be navigated to the novel URL.

        Returns a list of ChapterData sorted by chapter_num.
        """
        # Click the Chapter List tab
        tab = await page.query_selector("a#tab-chapters-title")
        if tab:
            await tab.click()
            logger.info("Clicked 'Chapter List' tab.")
        else:
            logger.warning("Could not find 'Chapter List' tab, attempting to parse anyway.")

        # Wait for chapter list to load
        await page.wait_for_selector("ul.list-chapter li a", state="attached", timeout=30_000)

        # Small delay to ensure all chapters are rendered
        await page.wait_for_timeout(2000)

        # Extract all chapter links
        chapter_elements = await page.query_selector_all("ul.list-chapter li a")
        logger.info("Found %d chapter elements in the DOM.", len(chapter_elements))

        chapters: list[ChapterData] = []
        for idx, el in enumerate(chapter_elements, start=1):
            href = await el.get_attribute("href")
            title_attr = await el.get_attribute("title")

            # Fallback to inner text if title attribute is missing
            if not title_attr:
                span = await el.query_selector("span")
                title_attr = (await span.inner_text()).strip() if span else f"Chapter {idx}"

            # Build absolute URL if needed
            if href and not href.startswith("http"):
                href = f"https://novelbin.me{href}"

            chapters.append(ChapterData(
                chapter_num=idx,
                chapter_title=title_attr.strip() if title_attr else f"Chapter {idx}",
                chapter_url=href or "",
            ))

        logger.info("Scraped %d chapters.", len(chapters))
        return chapters

    async def scrape_all(self, novel_url: str) -> NovelData:
        """
        Full scrape: navigate to the novel page, extract metadata + chapter list.

        Args:
            novel_url: The normalized novelbin.me novel URL.

        Returns:
            NovelData with all scraped information.
        """
        normalized_url = self.normalize_url(novel_url)
        logger.info("Starting full scrape for: %s", normalized_url)

        async with playwright_engine.new_page() as page:
            # Navigate to the novel page
            await page.goto(normalized_url, wait_until="networkidle")
            logger.info("Page loaded: %s", normalized_url)

            # Wait for the main content to be in the DOM
            await page.wait_for_selector("h3.title", state="attached", timeout=30_000)

            # Extract metadata
            metadata = await self.scrape_novel_metadata(page)
            logger.info("Metadata extracted: %s by %s", metadata["title"], metadata["author"])

            # Extract chapter list
            chapters = await self.scrape_chapter_list(page)

        novel_data = NovelData(
            title=metadata["title"],
            author=metadata["author"],
            description=metadata["description"],
            novel_url=normalized_url,
            n_chapters=len(chapters),
            chapters=chapters,
        )

        logger.info(
            "Scrape complete: '%s' — %d chapters found.",
            novel_data.title,
            novel_data.n_chapters,
        )
        return novel_data


# Module-level instance
novelbin_scraper = NovelBinScraper()
