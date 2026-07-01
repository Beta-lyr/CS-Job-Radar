"""每日采集脚本：读取启用的数据源 -> 采集 -> 写入 raw_jobs。"""

import json
import os
import sys
from datetime import datetime, timezone

from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "crawler"))
from storage.db import get_session


def log_crawl(session, source_id: int, status: str, fetched: int, inserted: int, error: str = ""):
    session.execute(
        text("""
            INSERT INTO crawl_logs (source_id, status, started_at, finished_at, fetched_count, inserted_count, error_message)
            VALUES (:sid, :st, :started, :finished, :fetched, :inserted, :error)
        """),
        {
            "sid": source_id,
            "st": status,
            "started": datetime.now(timezone.utc),
            "finished": datetime.now(timezone.utc),
            "fetched": fetched,
            "inserted": inserted,
            "error": error,
        },
    )


def load_sample_jobs():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "samples", "jobs.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def insert_sample_jobs(session):
    sample_jobs = load_sample_jobs()
    if not sample_jobs:
        print("No sample data found. Create data/samples/jobs.json to test.")
        return 0

    count = 0
    for job in sample_jobs:
        result = session.execute(
            text("""
                INSERT INTO raw_jobs (source_id, source_url, source_url_hash, raw_title, raw_company, raw_city, raw_salary, raw_description, publish_date, parse_status)
                VALUES (:sid, :url, :hash, :title, :company, :city, :salary, :desc, :pdate, 'pending')
                ON CONFLICT (source_url_hash) DO NOTHING
            """),
            {
                "sid": 1,
                "url": job.get("source_url", ""),
                "hash": job.get("source_url", ""),
                "title": job.get("raw_title", ""),
                "company": job.get("raw_company", ""),
                "city": job.get("raw_city", ""),
                "salary": job.get("raw_salary", ""),
                "desc": job.get("raw_description", ""),
                "pdate": datetime.now(timezone.utc),
            },
        )
        if result.rowcount > 0:
            count += 1
    return count


def run():
    session = get_session()

    sample_count = insert_sample_jobs(session)
    if sample_count > 0:
        session.commit()
        print(f"Inserted {sample_count} sample jobs.")
    else:
        print("No new sample jobs to insert.")

    sources = session.execute(
        text("SELECT id, name FROM sources WHERE enabled = true")
    ).fetchall()
    for src in sources:
        sid, name = src
        print(f"[{name}] Source registered, fetch logic pending.")
        log_crawl(session, sid, "success", 0, 0)
        session.commit()

    session.close()
    print(f"Done. Sources: {len(sources)}, Sample jobs: {sample_count}.")


if __name__ == "__main__":
    run()
