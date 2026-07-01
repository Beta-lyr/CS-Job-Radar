import os
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()
RAW_URL = os.getenv("DATABASE_URL", "")

_PSYCOPG2_IGNORE_PARAMS = {"pooled", "pgbouncer", "uselibpqcompat"}


def _clean_url(url: str) -> str:
    if not url or "?" not in url:
        return url
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    cleaned = {k: v for k, v in params.items() if k not in _PSYCOPG2_IGNORE_PARAMS}
    new_query = urlencode(cleaned, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


DATABASE_URL = _clean_url(RAW_URL)

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is not set")
        _engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)
    return _engine


def get_session():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()


Base = declarative_base()
