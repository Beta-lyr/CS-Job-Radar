"""每日采集脚本：读取启用的数据源 -> 采集 -> 写入 raw_jobs。"""

import json
import os
import sys
import traceback
from datetime import datetime, timezone

from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from services.crawler.storage.db import get_session
from services.crawler.utils.hash import url_hash, content_hash
from services.crawler.fetchers.static_fetcher import StaticFetcher
from services.crawler.fetchers.base import BaseFetcher
from services.crawler.parsers.generic_parser import GenericParser
from services.crawler.parsers.base import BaseParser, RawJobDTO

MAX_DETAIL_PAGES = 30
MAX_JOBS_PER_SOURCE = 100


def get_fetcher(fetcher_type: str) -> BaseFetcher:
    if fetcher_type == "static":
        return StaticFetcher()
    return StaticFetcher()


def get_parser(parser_type: str) -> BaseParser:
    return GenericParser()


def log_crawl(session, source_id: int, status: str, fetched: int, inserted: int, skipped: int = 0, error: str = ""):
    session.execute(
        text("""
            INSERT INTO crawl_logs (source_id, status, started_at, finished_at, fetched_count, inserted_count, skipped_count, error_message)
            VALUES (:sid, :st, :started, :finished, :fetched, :inserted, :skipped, :error)
        """),
        {
            "sid": source_id,
            "st": status,
            "started": datetime.now(timezone.utc),
            "finished": datetime.now(timezone.utc),
            "fetched": fetched,
            "inserted": inserted,
            "skipped": skipped,
            "error": error,
        },
    )


def insert_raw_job(session, source_id: int, job: RawJobDTO, source_url_hash: str, raw_hash_val: str) -> bool:
    result = session.execute(
        text("""
            INSERT INTO raw_jobs (source_id, source_url, source_url_hash, raw_title, raw_company, raw_city, raw_salary, raw_education, raw_experience, raw_description, publish_date, raw_hash, parse_status)
            VALUES (:sid, :url, :url_hash, :title, :company, :city, :salary, :edu, :exp, :desc, :pdate, :raw_hash, 'pending')
            ON CONFLICT (source_url_hash) DO NOTHING
        """),
        {
            "sid": source_id,
            "url": job.source_url,
            "url_hash": source_url_hash,
            "title": job.raw_title or "",
            "company": job.raw_company or "",
            "city": job.raw_city or "",
            "salary": job.raw_salary or "",
            "edu": job.raw_education or "",
            "exp": job.raw_experience or "",
            "desc": (job.raw_description or "")[:8000],
            "pdate": job.publish_date or datetime.now(timezone.utc),
            "raw_hash": raw_hash_val,
        },
    )
    return result.rowcount > 0


def load_sample_jobs():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "samples", "jobs.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def insert_sample_jobs(session):
    sample_jobs = load_sample_jobs()
    if not sample_jobs:
        return 0
    count = 0
    for job in sample_jobs:
        url = job.get("source_url", "")
        uh = url_hash(url)
        ch = content_hash(job.get("raw_title", ""), job.get("raw_company", ""), job.get("raw_city", ""), job.get("raw_description", ""))
        result = session.execute(
            text("""
                INSERT INTO raw_jobs (source_id, source_url, source_url_hash, raw_title, raw_company, raw_city, raw_salary, raw_description, publish_date, raw_hash, parse_status)
                VALUES (:sid, :url, :hash, :title, :company, :city, :salary, :desc, :pdate, :raw_hash, 'pending')
                ON CONFLICT (source_url_hash) DO NOTHING
            """),
            {
                "sid": 1,
                "url": url,
                "hash": uh,
                "title": job.get("raw_title", ""),
                "company": job.get("raw_company", ""),
                "city": job.get("raw_city", ""),
                "salary": job.get("raw_salary", ""),
                "desc": job.get("raw_description", ""),
                "pdate": datetime.now(timezone.utc),
                "raw_hash": ch,
            },
        )
        if result.rowcount > 0:
            count += 1
    return count


def crawl_source(session, source_id: int, name: str, list_url: str, fetcher_type: str, parser_type: str) -> dict:
    result = {"inserted": 0, "skipped": 0, "error": ""}

    try:
        fetcher = get_fetcher(fetcher_type)
        parser = get_parser(parser_type)

        list_html = fetcher.fetch(list_url)
        detail_urls = parser.parse_list(list_html, list_url)

        if not detail_urls:
            result["error"] = "No job links found on list page"
            return result

        detail_urls = detail_urls[:MAX_DETAIL_PAGES]
        jobs: list[RawJobDTO] = []

        for detail_url in detail_urls:
            if len(jobs) >= MAX_JOBS_PER_SOURCE:
                break
            try:
                detail_html = fetcher.fetch(detail_url)
                job = parser.parse_detail(detail_html, detail_url)
                if job.raw_title:
                    jobs.append(job)
            except Exception:
                continue

        for job in jobs:
            uh = url_hash(job.source_url)
            ch = content_hash(job.raw_title or "", job.raw_company or "", job.raw_city or "", job.raw_description or "")
            if insert_raw_job(session, source_id, job, uh, ch):
                result["inserted"] += 1
            else:
                result["skipped"] += 1

    except Exception as e:
        result["error"] = str(e)[:500]
        traceback.print_exc()

    return result


def run():
    session = get_session()

    sample_count = insert_sample_jobs(session)
    if sample_count > 0:
        session.commit()
        print(f"[sample] Inserted {sample_count} sample jobs.")

    sources = session.execute(
        text("SELECT id, name, list_url, fetcher_type, parser_type FROM sources WHERE enabled = true")
    ).fetchall()

    total_inserted = sample_count
    total_skipped = 0
    source_count = 0

    for src in sources:
        sid, name, list_url, fetcher_type, parser_type = src
        source_count += 1
        print(f"[{name}] Crawling {list_url} ...")

        if not list_url or list_url.startswith("http://example") or "example" in list_url:
            print(f"[{name}] Skipped (example/test URL)")
            log_crawl(session, sid, "success", 0, 0, 0)
            session.commit()
            continue

        r = crawl_source(session, sid, name, list_url, fetcher_type or "static", parser_type or "generic")
        total_inserted += r["inserted"]
        total_skipped += r["skipped"]

        status = "success" if not r["error"] else ("partial_success" if r["inserted"] > 0 else "failed")
        log_crawl(session, sid, status, r["inserted"] + r["skipped"], r["inserted"], r["skipped"], r["error"])
        session.commit()

        print(f"  -> inserted={r['inserted']} skipped={r['skipped']} {'error=' + r['error'] if r['error'] else ''}")

    session.close()
    print(f"Done. Sources: {source_count}, Inserted: {total_inserted}, Skipped: {total_skipped}.")


if __name__ == "__main__":
    run()
