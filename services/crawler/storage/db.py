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
        engine_options = {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_pre_ping": True,
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE_SECONDS", "300")),
            "pool_timeout": 30,
        }
        if DATABASE_URL.startswith(("postgresql://", "postgresql+psycopg2://")):
            engine_options["connect_args"] = {
                "keepalives": 1,
                "keepalives_idle": int(os.getenv("DB_KEEPALIVES_IDLE", "30")),
                "keepalives_interval": int(os.getenv("DB_KEEPALIVES_INTERVAL", "10")),
                "keepalives_count": int(os.getenv("DB_KEEPALIVES_COUNT", "5")),
            }
        _engine = create_engine(DATABASE_URL, **engine_options)
    return _engine


def get_session():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()


Base = declarative_base()
