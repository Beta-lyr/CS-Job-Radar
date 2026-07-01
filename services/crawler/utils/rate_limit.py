import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, min_interval_seconds: float = 2.0):
        self._min_interval = min_interval_seconds
        self._last_request: dict[str, float] = defaultdict(float)

    def wait(self, domain: str):
        now = time.time()
        elapsed = now - self._last_request.get(domain, 0)
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request[domain] = time.time()
