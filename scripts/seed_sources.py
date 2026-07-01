"""初始化数据源到数据库。"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from services.crawler.storage.db import get_session
from sqlalchemy import text

SOURCES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "source-registry", "sources.json"
)


def load_sources():
    with open(SOURCES_PATH, encoding="utf-8") as f:
        return json.load(f)


def seed():
    session = get_session()
    sources = load_sources()
    count = 0
    for s in sources:
        existing = session.execute(
            text("SELECT id FROM sources WHERE list_url = :url"),
            {"url": s["list_url"]},
        ).fetchone()
        if existing:
            print(f"  Skip existing: {s['name']}")
            continue
        session.execute(
            text("""
                INSERT INTO sources (name, source_type, base_url, list_url, city, industry, parser_type, fetcher_type, risk_level, enabled, crawl_interval_hours)
                VALUES (:name, :source_type, :base_url, :list_url, :city, :industry, :parser_type, :fetcher_type, :risk_level, :enabled, :crawl_interval_hours)
            """),
            s,
        )
        count += 1
        print(f"  Inserted: {s['name']}")
    session.commit()
    session.close()
    print(f"\nDone. {count} sources seeded.")


if __name__ == "__main__":
    seed()
