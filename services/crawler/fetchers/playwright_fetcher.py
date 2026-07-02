import json
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
            timeout=90,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        if result.returncode != 0:
            err = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"Playwright fetch failed: {err}")
        return result.stdout.decode("utf-8", errors="replace")

    def fetch_batch(self, urls: list[str]) -> dict[str, str]:
        if not urls:
            return {}
        if len(urls) == 1:
            return {urls[0]: self.fetch(urls[0])}

        domain = urlparse(urls[0]).netloc
        _rate_limiter.wait(domain)

        result = subprocess.run(
            [sys.executable, _HELPER_SCRIPT, "--batch"] + urls,
            capture_output=True,
            timeout=len(urls) * 60 + 30,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        if result.returncode != 0:
            err = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"Playwright batch fetch failed: {err}")
        return json.loads(result.stdout.decode("utf-8", errors="replace"))
