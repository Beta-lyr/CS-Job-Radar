import subprocess
import sys
import os
from urllib.parse import urlparse

from .base import BaseFetcher
from ..utils.rate_limit import RateLimiter

_rate_limiter = RateLimiter(min_interval_seconds=3.0)

_HELPER_SCRIPT = os.path.join(os.path.dirname(__file__), "_playwright_fetch.py")


class PlaywrightFetcher(BaseFetcher):
    def fetch(self, url: str) -> str:
        domain = urlparse(url).netloc
        _rate_limiter.wait(domain)

        result = subprocess.run(
            [sys.executable, _HELPER_SCRIPT, url],
            capture_output=True,
            text=True,
            timeout=90,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Playwright fetch failed: {result.stderr.strip()}")
        return result.stdout
