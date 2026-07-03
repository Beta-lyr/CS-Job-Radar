"""Crawler for Tencent campus recruitment technology jobs."""

import re
import sys
import os
import time
from datetime import datetime, timezone, timedelta
from html import unescape
from urllib.parse import quote

import requests
from sqlalchemy.exc import SQLAlchemyError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from services.crawler.utils.hash import content_hash, url_hash
from services.analyzer.filters.job_relevance import is_relevant_cs_job

BJ_TZ = timezone(timedelta(hours=8))

BASE_URL = "https://join.qq.com"
LIST_API = f"{BASE_URL}/api/v1/position/searchPosition"
DETAIL_API = f"{BASE_URL}/api/v1/jobDetails/getJobDetailsByPostId"
DETAIL_URL = f"{BASE_URL}/jobdesc.html?postId={{post_id}}"

PAGE_SIZE = 50
MAX_PAGES = 12
MAX_POSTS_TOTAL = 320
REQUEST_TIMEOUT = 30
MAX_RETRIES = 2
MAX_DB_RETRIES = 2
REQUEST_INTERVAL_SECONDS = 0.25

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
    ),
    "Referer": f"{BASE_URL}/post.html?query=p_2",
}


def crawl(session, source_id: int, list_url: str, fetcher) -> dict:
    result = {"inserted": 0, "skipped": 0, "error": ""}
    http = requests.Session()
    http.headers.update(HEADERS)

    try:
        posts = []
        seen_post_ids = set()

        for page in range(1, MAX_PAGES + 1):
            data = _fetch_positions(http, page)
            items = (((data or {}).get("data") or {}).get("positionList") or [])
            if not items:
                break

            accepted = 0
            duplicate = 0
            filtered = 0
            for item in items:
                post_id = _clean_text(item.get("postId"))
                if not post_id:
                    continue
                if post_id in seen_post_ids:
                    duplicate += 1
                    continue
                seen_post_ids.add(post_id)

                if not _is_relevant_item(item):
                    filtered += 1
                    continue
                posts.append(item)
                accepted += 1
                if len(posts) >= MAX_POSTS_TOTAL:
                    break

            print(
                f"  page {page}: {len(items)} positions, "
                f"{accepted} accepted, {duplicate} duplicate, {filtered} filtered"
            )
            if len(posts) >= MAX_POSTS_TOTAL:
                break

            count = int(((data or {}).get("data") or {}).get("count") or 0)
            if count and page * PAGE_SIZE >= count:
                break

        print(f"  total accepted positions: {len(posts)}")

        for item in posts:
            try:
                detail = _fetch_detail(http, _clean_text(item.get("postId")))
                jobs = _build_jobs(item, detail)
                for job in jobs:
                    if not is_relevant_cs_job(
                        title=job.get("raw_title", ""),
                        description=job.get("raw_description", ""),
                    ):
                        result["skipped"] += 1
                        continue

                    uh = url_hash(job["source_url"])
                    ch = content_hash(
                        job.get("raw_title", ""),
                        job.get("raw_company", ""),
                        job.get("raw_city", ""),
                        job.get("raw_description", ""),
                    )
                    if _insert_with_retry(session, source_id, job, uh, ch):
                        result["inserted"] += 1
                    else:
                        result["skipped"] += 1
            except Exception as exc:
                _rollback_session(session)
                result["skipped"] += 1
                print(f"  detail skipped: {exc}")

    except Exception as exc:
        _rollback_session(session)
        result["error"] = str(exc)[:500]

    return result


def _fetch_positions(http: requests.Session, page: int) -> dict:
    payload = {
        "pageIndex": page,
        "pageSize": PAGE_SIZE,
        "type": 2,
        "keyword": "",
        "language": "zh-cn",
    }
    resp = _request_with_retries(http, "POST", LIST_API, json=payload)
    time.sleep(REQUEST_INTERVAL_SECONDS)
    return resp.json()


def _fetch_detail(http: requests.Session, post_id: str) -> dict:
    resp = _request_with_retries(
        http,
        "GET",
        DETAIL_API,
        params={"postId": post_id, "lang": "zh-cn"},
    )
    time.sleep(REQUEST_INTERVAL_SECONDS)
    data = resp.json()
    if data.get("status") != 0:
        raise RuntimeError(data.get("message") or f"Tencent detail API failed for {post_id}")
    return data.get("data") or {}


def _request_with_retries(http: requests.Session, method: str, url: str, **kwargs) -> requests.Response:
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = http.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def _build_jobs(item: dict, detail: dict) -> list[dict]:
    post_id = _clean_text(item.get("postId")) or _clean_text(detail.get("postId"))
    title = _clean_text(detail.get("title")) or _clean_text(item.get("positionTitle"))
    cities = _extract_cities(detail.get("workCityList") or item.get("workCities"))
    if not cities:
        cities = ["深圳"]

    description_parts = [
        _clean_text(detail.get("desc")),
        _clean_text(detail.get("request")),
        f"事业群：{_clean_text(item.get('bgs'))}" if _clean_text(item.get("bgs")) else "",
        f"招聘项目：{_clean_text(item.get('projectName'))}" if _clean_text(item.get("projectName")) else "",
        f"岗位类型：{_clean_text(detail.get('tidName'))}" if _clean_text(detail.get("tidName")) else "",
    ]
    description = "\n".join(p for p in description_parts if p).strip()

    jobs = []
    for city in cities:
        source_url = f"{DETAIL_URL.format(post_id=post_id)}&city={quote(city)}"
        jobs.append({
            "source_url": source_url,
            "raw_title": title,
            "raw_company": "腾讯",
            "raw_city": city,
            "raw_salary": "未公开",
            "raw_education": "本科及以上",
            "raw_experience": "应届/实习",
            "raw_description": description[:8000],
            "publish_date": datetime.now(BJ_TZ),
        })
    return jobs


def _extract_cities(value) -> list[str]:
    if isinstance(value, list):
        raw_items = value
    else:
        raw_items = re.split(r"[\s,，/]+", _clean_text(value))

    cities = []
    seen = set()
    for item in raw_items:
        city = _clean_city(item)
        if city and city not in seen:
            seen.add(city)
            cities.append(city)
    return cities


def _clean_city(value) -> str:
    text = _clean_text(value)
    if not text:
        return ""
    text = text.replace("总部", "").replace("市", "").strip()
    if text in {"远程面试", "线上", "不限"}:
        return ""
    if text == "中国香港":
        return "香港"
    return text


def _is_relevant_item(item: dict) -> bool:
    return is_relevant_cs_job(
        title=_clean_text(item.get("positionTitle")),
        description=" ".join([
            _clean_text(item.get("bgs")),
            _clean_text(item.get("projectName")),
            _clean_text(item.get("recruitLabelName")),
        ]),
    )


def _clean_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = " ".join(str(v) for v in value)
    elif not isinstance(value, str):
        value = str(value)
    value = unescape(value)
    value = re.sub(r"\s+", " ", value.replace("\x00", " ")).strip()
    return value


def _insert(session, source_id: int, job: dict, uh: str, ch: str) -> bool:
    from sqlalchemy import text

    result = session.execute(
        text("""
            INSERT INTO raw_jobs (
                source_id, source_url, source_url_hash, raw_title, raw_company,
                raw_city, raw_salary, raw_education, raw_experience,
                raw_description, publish_date, raw_hash, parse_status
            )
            VALUES (
                :sid, :url, :url_hash, :title, :company, :city, :salary,
                :edu, :exp, :desc, :pdate, :raw_hash, 'pending'
            )
            ON CONFLICT (source_url_hash) DO NOTHING
        """),
        {
            "sid": source_id,
            "url": job.get("source_url", ""),
            "url_hash": uh,
            "title": job.get("raw_title", ""),
            "company": job.get("raw_company", ""),
            "city": job.get("raw_city", ""),
            "salary": job.get("raw_salary", ""),
            "edu": job.get("raw_education", ""),
            "exp": job.get("raw_experience", ""),
            "desc": (job.get("raw_description", "") or "")[:8000].replace("\x00", ""),
            "pdate": job.get("publish_date") or datetime.now(BJ_TZ),
            "raw_hash": ch,
        },
    )
    return result.rowcount > 0


def _insert_with_retry(session, source_id: int, job: dict, uh: str, ch: str) -> bool:
    last_error = None
    for attempt in range(MAX_DB_RETRIES + 1):
        try:
            inserted = _insert(session, source_id, job, uh, ch)
            _commit_session(session)
            return inserted
        except SQLAlchemyError as exc:
            last_error = exc
            _rollback_session(session)
            if attempt < MAX_DB_RETRIES:
                time.sleep(1.5 * (attempt + 1))
                continue
    raise last_error


def _commit_session(session) -> None:
    commit = getattr(session, "commit", None)
    if commit:
        commit()


def _rollback_session(session) -> None:
    rollback = getattr(session, "rollback", None)
    if rollback:
        rollback()
