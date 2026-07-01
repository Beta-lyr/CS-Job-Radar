from .base import BaseFetcher
from ..utils.rate_limit import RateLimiter
from urllib.parse import urlparse

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

_rate_limiter = RateLimiter(min_interval_seconds=3.0)


class PlaywrightFetcher(BaseFetcher):
    def __init__(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError("playwright not installed. Run: pip install playwright && playwright install chromium")
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)

    def fetch(self, url: str) -> str:
        domain = urlparse(url).netloc
        _rate_limiter.wait(domain)

        page = self._browser.new_page()
        try:
            page.set_viewport_size({"width": 1920, "height": 1080})
            page.set_extra_http_headers({"User-Agent": USER_AGENT})
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            try:
                page.wait_for_timeout(2000)
            except Exception:
                pass
            return page.content()
        finally:
            page.close()

    def close(self):
        try:
            self._browser.close()
            self._playwright.stop()
        except Exception:
            pass

    def __del__(self):
        self.close()
