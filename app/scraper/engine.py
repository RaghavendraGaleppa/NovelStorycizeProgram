import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

logger = logging.getLogger(__name__)

# Stealth-ish configuration
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
_VIEWPORT = {"width": 1280, "height": 720}
_NAVIGATION_TIMEOUT = 60_000  # 60 seconds
_DEFAULT_TIMEOUT = 30_000     # 30 seconds


class PlaywrightEngine:
    """
    Manages a singleton Playwright browser instance.

    Usage:
        engine = PlaywrightEngine()
        await engine.startup()

        async with engine.new_page() as page:
            await page.goto("https://example.com")
            # ... do scraping ...

        await engine.shutdown()
    """

    def __init__(self):
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    async def startup(self) -> None:
        """Launch Playwright and the Chromium browser."""
        logger.info("Starting Playwright engine...")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        logger.info("Playwright engine started (Chromium, headless).")

    async def shutdown(self) -> None:
        """Close the browser and Playwright."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Playwright engine shut down.")

    @asynccontextmanager
    async def new_page(self) -> AsyncGenerator[Page, None]:
        """
        Create a new browser page with stealth settings.
        Automatically closes the context when done.
        """
        if self._browser is None:
            raise RuntimeError("PlaywrightEngine not started. Call startup() first.")

        context: BrowserContext = await self._browser.new_context(
            user_agent=_USER_AGENT,
            viewport=_VIEWPORT,
            java_script_enabled=True,
            ignore_https_errors=True,
        )
        context.set_default_navigation_timeout(_NAVIGATION_TIMEOUT)
        context.set_default_timeout(_DEFAULT_TIMEOUT)

        page = await context.new_page()

        # Mask webdriver detection
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        try:
            yield page
        finally:
            await context.close()


# Singleton instance used across the app
playwright_engine = PlaywrightEngine()
