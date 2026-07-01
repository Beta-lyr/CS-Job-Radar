from .base import BaseFetcher
from ..utils.rate_limit import RateLimiter
from urllib.parse import urlparse

_rate_limiter = RateLimiter(min_interval_seconds=3.0)


class PlaywrightFetcher(BaseFetcher):
    def fetch(self, url: str) -> str:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError("playwright not installed. Run: pip install playwright && playwright install chromium")

        domain = urlparse(url).netloc
        _rate_limiter.wait(domain)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=60000)
            html = page.content()
            browser.close()
            return html
