import json
import subprocess
import sys
import os
import tempfile
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

        all_results: dict[str, str] = {}
        chunk_size = 20

        for i in range(0, len(urls), chunk_size):
            chunk = urls[i:i + chunk_size]
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                result = subprocess.run(
                    [sys.executable, _HELPER_SCRIPT, "--batch", tmp_path] + chunk,
                    capture_output=True,
                    timeout=len(chunk) * 60 + 30,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                )
                if result.returncode != 0:
                    err = result.stderr.decode("utf-8", errors="replace").strip()
                    raise RuntimeError(f"Playwright batch fetch failed: {err}")

                with open(tmp_path, "r", encoding="utf-8") as f:
                    all_results.update(json.load(f))
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        return all_results
