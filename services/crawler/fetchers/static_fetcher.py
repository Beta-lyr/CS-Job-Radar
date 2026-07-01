import requests
from urllib.parse import urlparse

from .base import BaseFetcher
from ..utils.rate_limit import RateLimiter

USER_AGENT = "Mozilla/5.0 (compatible; CSJobRadar/1.0; +https://cs-job-radar.pages.dev)"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 2

_rate_limiter = RateLimiter(min_interval_seconds=2.0)


class StaticFetcher(BaseFetcher):
    def fetch(self, url: str) -> str:
        domain = urlparse(url).netloc
        _rate_limiter.wait(domain)

        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    url,
                    headers={"User-Agent": USER_AGENT},
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True,
                )
                resp.raise_for_status()
                resp.encoding = resp.apparent_encoding or "utf-8"
                return resp.text
            except requests.RequestException as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    _rate_limiter.wait(domain)

        raise RuntimeError(f"Failed to fetch {url} after {MAX_RETRIES + 1} attempts: {last_error}")
