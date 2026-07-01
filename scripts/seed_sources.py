"""初始化/更新数据源到数据库。按 name 匹配：存在则更新，不存在则插入。"""

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
    inserted = 0
    updated = 0

    for s in sources:
        existing = session.execute(
            text("SELECT id FROM sources WHERE name = :name"),
            {"name": s["name"]},
        ).fetchone()

        if existing:
            session.execute(
                text("""
                    UPDATE sources SET
                        source_type = :source_type, base_url = :base_url, list_url = :list_url,
                        city = :city, industry = :industry, parser_type = :parser_type,
                        fetcher_type = :fetcher_type, risk_level = :risk_level,
                        enabled = :enabled, crawl_interval_hours = :crawl_interval_hours,
                        updated_at = now()
                    WHERE id = :id
                """),
                {**s, "id": existing.id},
            )
            updated += 1
            print(f"  Updated: {s['name']}")
        else:
            session.execute(
                text("""
                    INSERT INTO sources (name, source_type, base_url, list_url, city, industry, parser_type, fetcher_type, risk_level, enabled, crawl_interval_hours)
                    VALUES (:name, :source_type, :base_url, :list_url, :city, :industry, :parser_type, :fetcher_type, :risk_level, :enabled, :crawl_interval_hours)
                """),
                s,
            )
            inserted += 1
            print(f"  Inserted: {s['name']}")

    session.commit()
    session.close()
    print(f"\nDone. {inserted} inserted, {updated} updated.")


if __name__ == "__main__":
    seed()
