import hashlib
import re


def normalize_url(url: str) -> str:
    url = url.strip().rstrip("/")
    url = re.sub(r"https?://", "https://", url)
    return url.lower()


def url_hash(url: str) -> str:
    return hashlib.sha256(normalize_url(url).encode()).hexdigest()


def content_hash(title: str, company: str, city: str, description: str) -> str:
    raw = f"{title or ''}|{company or ''}|{city or ''}|{description or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()
