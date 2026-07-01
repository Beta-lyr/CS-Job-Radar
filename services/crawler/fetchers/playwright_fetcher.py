import asyncio
import threading
from urllib.parse import urlparse

from .base import BaseFetcher
from ..utils.rate_limit import RateLimiter

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

_rate_limiter = RateLimiter(min_interval_seconds=3.0)


def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result = {}
    error = {}

    def _target():
        try:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            result["value"] = new_loop.run_until_complete(coro)
            new_loop.close()
        except Exception as e:
            error["value"] = e

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join()
    if error:
        raise error["value"]
    return result["value"]


class PlaywrightFetcher(BaseFetcher):
    def __init__(self):
        self._browser = None
        self._playwright = None
        self._start()

    def _start(self):
        from playwright.async_api import async_playwright

        async def _init():
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)

        _run_async(_init())

    def fetch(self, url: str) -> str:
        domain = urlparse(url).netloc
        _rate_limiter.wait(domain)

        async def _fetch():
            page = await self._browser.new_page()
            try:
                await page.set_viewport_size({"width": 1920, "height": 1080})
                await page.set_extra_http_headers({"User-Agent": USER_AGENT})
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
                return await page.content()
            finally:
                await page.close()

        return _run_async(_fetch())

    def close(self):
        if self._browser is None:
            return

        async def _close():
            await self._browser.close()
            await self._playwright.stop()

        try:
            _run_async(_close())
        except Exception:
            pass

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
