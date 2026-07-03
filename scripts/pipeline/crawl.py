"""每日采集脚本：读取启用的数据源 → 按 slug 路由到专属脚本 → 写入 raw_jobs。"""

import os
import sys
import time
import traceback
from datetime import datetime, timezone, timedelta

from sqlalchemy import text

BJ_TZ = timezone(timedelta(hours=8))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from services.crawler.storage.db import get_session
from services.crawler.fetchers.static_fetcher import StaticFetcher
from services.crawler.fetchers.playwright_fetcher import PlaywrightFetcher
from services.crawler.fetchers.base import BaseFetcher
from scripts.sources import load_source_script


def get_fetcher(fetcher_type: str) -> BaseFetcher:
    if fetcher_type == "playwright":
        return PlaywrightFetcher()
    return StaticFetcher()


def log_crawl(session, source_id: int, status: str, fetched: int, inserted: int, skipped: int = 0, error: str = ""):
    now = datetime.now(BJ_TZ)
    session.execute(
        text("""
            INSERT INTO crawl_logs (source_id, status, started_at, finished_at, fetched_count, inserted_count, skipped_count, error_message)
            VALUES (:sid, :st, :started, :finished, :fetched, :inserted, :skipped, :error)
        """),
        {
            "sid": source_id, "st": status,
            "started": now, "finished": now,
            "fetched": fetched, "inserted": inserted, "skipped": skipped, "error": error,
        },
    )


def run():
    session = get_session()
    t0_total = time.time()

    sources = session.execute(
        text("SELECT id, slug, name, list_url, fetcher_type FROM sources WHERE enabled = true")
    ).fetchall()

    total_inserted = 0
    total_skipped = 0

    for src in sources:
        sid, slug, name, list_url, fetcher_type = src
        print(f"[{name}] Crawling {list_url} ...")

        if not list_url:
            print(f"[{name}] Skipped (no URL)")
            log_crawl(session, sid, "failed", 0, 0, 0, "No list_url configured")
            session.commit()
            continue

        if not slug:
            print(f"  -> skipped (no slug configured)")
            log_crawl(session, sid, "failed", 0, 0, 0, "No slug configured in sources table")
            session.commit()
            continue

        script = load_source_script(slug)

        if not script:
            print(f"  -> skipped (no source script at scripts/sources/{slug}.py)")
            log_crawl(session, sid, "failed", 0, 0, 0, f"Source script not found: sources/{slug}.py")
            session.commit()
            continue

        t0 = time.time()
        fetcher = get_fetcher(fetcher_type or "static")
        try:
            r = script.crawl(session, sid, list_url, fetcher)
        except Exception as e:
            traceback.print_exc()
            session.rollback()
            r = {"inserted": 0, "skipped": 0, "error": str(e)[:500]}

        elapsed = time.time() - t0
        total_inserted += r.get("inserted", 0)
        total_skipped += r.get("skipped", 0)

        status = "success" if not r.get("error") else ("partial_success" if r.get("inserted", 0) > 0 else "failed")
        fcount = r.get("inserted", 0) + r.get("skipped", 0)
        log_crawl(session, sid, status, fcount, r.get("inserted", 0), r.get("skipped", 0), r.get("error", ""))
        session.commit()

        print(f"  -> inserted={r.get('inserted', 0)} skipped={r.get('skipped', 0)} elapsed={elapsed:.1f}s {'error=' + r['error'] if r.get('error') else ''}")

    session.close()
    total_elapsed = time.time() - t0_total
    print(f"Done. Sources: {len(sources)}, Inserted: {total_inserted}, Skipped: {total_skipped}, Total: {total_elapsed:.1f}s.")


if __name__ == "__main__":
    run()
