"""Crawler for 国家大学生就业服务平台 computer/internet jobs."""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from html import unescape

import requests
from bs4 import BeautifulSoup
from sqlalchemy.exc import SQLAlchemyError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from services.crawler.utils.hash import content_hash, url_hash
from services.analyzer.filters.job_relevance import is_relevant_cs_job

BJ_TZ = timezone(timedelta(hours=8))

BASE_URL = "https://www.ncss.cn"
LIST_API = f"{BASE_URL}/student/jobs/jobslist/ajax/"
DETAIL_URL = f"{BASE_URL}/student/jobs/{{job_id}}/detail.html"

MAX_PAGES_PER_QUERY = 10
PAGE_SIZE = 20
MAX_JOBS_TOTAL = 1200
REQUEST_TIMEOUT = 30
MAX_RETRIES = 2
MAX_DB_RETRIES = 2
LIST_REQUEST_INTERVAL_SECONDS = 0.3

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NCSS_PRESET_PATH = os.path.join(REPO_ROOT, "data", "source-presets", "ncss.json")
CS_CRAWL_PRESET_PATH = os.path.join(REPO_ROOT, "data", "crawl-presets", "cs_jobs.json")
CITY_PRESET_PATH = os.path.join(REPO_ROOT, "data", "geo", "cities.json")

DEFAULT_INDUSTRIES = [
    {"code": "000101", "name": "计算机软件"},
    {"code": "000102", "name": "计算机硬件"},
    {"code": "000103", "name": "系统/数据/维护/安全"},
    {"code": "000104", "name": "互联网/电子商务"},
    {"code": "000105", "name": "网络游戏"},
    {"code": "000106", "name": "通信/电信服务"},
    {"code": "000108", "name": "通信技术开发及应用"},
    {"code": "000109", "name": "电子/半导体/集成电路"},
]

DEFAULT_KEYWORD_QUERIES = [
    "Java",
    "后端",
    "前端",
    "测试",
    "运维",
    "实施",
    "C++",
    "嵌入式",
    "硬件",
    "通信",
    "射频",
    "半导体",
    "芯片",
    "人工智能",
    "大模型",
    "数据分析",
    "数据开发",
    "产品经理",
]

DEFAULT_AREA_CODES = {
    "北京": "11",
    "上海": "31",
    "江苏": "32",
    "浙江": "33",
    "广东": "44",
    "四川": "51",
    "湖北": "42",
    "陕西": "61",
}

DEFAULT_JOB_TYPES = {
    "全职": "01",
    "实习": "03",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
    ),
    "Referer": f"{BASE_URL}/student/jobs/index.html",
}


def crawl(session, source_id: int, list_url: str, fetcher) -> dict:
    result = {"inserted": 0, "skipped": 0, "error": ""}
    http = requests.Session()
    http.headers.update(HEADERS)

    try:
        seen: set[str] = set()
        rows = []
        filtered_count = 0

        for query in _build_query_plan():
            label = query["label"]
            for page in range(1, MAX_PAGES_PER_QUERY + 1):
                data = _fetch_list(http, page, query)
                jobs = (((data or {}).get("data") or {}).get("list") or [])
                if not jobs:
                    break

                accepted, duplicate_count, query_filtered = _collect_page_jobs(jobs, seen, rows)
                filtered_count += query_filtered

                print(
                    f"  {label} page {page}: "
                    f"{len(jobs)} jobs, {accepted} accepted, {duplicate_count} duplicate"
                )
                if len(rows) >= MAX_JOBS_TOTAL:
                    break

                page_info = ((data or {}).get("data") or {}).get("pagenation") or {}
                total = int(page_info.get("total") or 0)
                if total and page >= total:
                    break
            if len(rows) >= MAX_JOBS_TOTAL:
                break

        print(f"  total accepted jobs: {len(rows)}, filtered out: {filtered_count}")

        for item in rows:
            try:
                job = _build_job(http, item)
                if not job.get("raw_title"):
                    result["skipped"] += 1
                    continue
                if not is_relevant_cs_job(
                    title=job.get("raw_title", ""),
                    description=job.get("raw_description", ""),
                ):
                    filtered_count += 1
                    continue

                detail_url = job["source_url"]
                uh = url_hash(detail_url)
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
        result["error"] = str(exc)[:500]

    return result


def _build_query_plan() -> list[dict]:
    preset = _load_crawl_config()
    industries = preset["industries"]
    keyword_queries = preset["keyword_queries"]
    area_codes = preset["area_codes"]
    job_types = preset["job_types"]

    queries: list[dict] = []
    seen_keys: set[tuple] = set()

    def add(label: str, industry_code: str = "", job_name: str = "", area_code: str = "", job_type: str = ""):
        key = (industry_code, job_name, area_code, job_type)
        if key in seen_keys:
            return
        seen_keys.add(key)
        queries.append({
            "label": label,
            "industry_code": industry_code,
            "job_name": job_name,
            "area_code": area_code,
            "job_type": job_type,
        })

    for industry in industries:
        industry_code = industry["code"]
        industry_name = industry["name"]
        add(f"行业:{industry_name}", industry_code=industry_code)
        for job_type_name, job_type in job_types.items():
            add(f"行业:{industry_name}/{job_type_name}", industry_code=industry_code, job_type=job_type)

    for keyword in keyword_queries:
        add(f"关键词:{keyword}", job_name=keyword)
        for area_name, area_code in area_codes.items():
            add(f"关键词:{keyword}/{area_name}", job_name=keyword, area_code=area_code)
        for job_type_name, job_type in job_types.items():
            add(f"关键词:{keyword}/{job_type_name}", job_name=keyword, job_type=job_type)

    for area_name, area_code in area_codes.items():
        for industry in industries:
            industry_code = industry["code"]
            industry_name = industry["name"]
            add(f"地区:{area_name}/{industry_name}", industry_code=industry_code, area_code=area_code)

    return queries


def _load_crawl_config() -> dict:
    source_preset = _read_json(NCSS_PRESET_PATH, {})
    crawl_preset = _read_json(CS_CRAWL_PRESET_PATH, {})
    city_preset = _read_json(CITY_PRESET_PATH, {})

    industries = _normalize_industries(source_preset.get("industries")) or DEFAULT_INDUSTRIES
    keyword_queries = _normalize_string_list(crawl_preset.get("search_keywords")) or DEFAULT_KEYWORD_QUERIES
    area_codes = _normalize_string_map(
        (((city_preset.get("__source_codes") or {}).get("ncss") or {}).get("area_codes") or {})
    ) or DEFAULT_AREA_CODES
    job_types = _normalize_string_map(source_preset.get("job_types")) or DEFAULT_JOB_TYPES

    return {
        "industries": industries,
        "keyword_queries": keyword_queries,
        "area_codes": area_codes,
        "job_types": job_types,
    }


def _read_json(path: str, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def _normalize_industries(value) -> list[dict]:
    industries = []
    for item in value or []:
        if not isinstance(item, dict):
            continue
        code = _clean_text(item.get("code"))
        name = _clean_text(item.get("name")) or code
        if code:
            industries.append({"code": code, "name": name})
    return industries


def _normalize_string_list(value) -> list[str]:
    normalized = []
    seen = set()
    for item in value or []:
        text = _clean_text(item)
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            normalized.append(text)
    return normalized


def _normalize_string_map(value) -> dict[str, str]:
    normalized = {}
    for key, val in (value or {}).items():
        name = _clean_text(key)
        code = _clean_text(val)
        if name and code:
            normalized[name] = code
    return normalized


def _collect_page_jobs(jobs: list[dict], seen: set[str], rows: list[dict]) -> tuple[int, int, int]:
    accepted = 0
    duplicate_count = 0
    filtered_count = 0
    for item in jobs:
        job_id = str(item.get("jobId") or "").strip()
        if not job_id:
            continue
        if job_id in seen:
            duplicate_count += 1
            continue
        seen.add(job_id)

        if not _is_relevant_it_job(item):
            filtered_count += 1
            continue

        rows.append(item)
        accepted += 1
        if len(rows) >= MAX_JOBS_TOTAL:
            break
    return accepted, duplicate_count, filtered_count


def _fetch_list(http: requests.Session, page: int, query: dict | None = None) -> dict:
    query = query or {}
    industry_code = query.get("industry_code", "")
    industry_sectors = f"{industry_code}," if industry_code else ""
    params = {
        "jobType": "",
        "areaCode": "",
        "jobName": "",
        "monthPay": "",
        "industrySectors": industry_sectors,
        "recruitType": "",
        "property": "",
        "categoryCode": "",
        "memberLevel": "",
        "offset": str(page),
        "limit": str(PAGE_SIZE),
        "keyUnits": "",
        "degreeCode": "",
        "sourcesName": "0",
        "sourcesType": "",
    }
    if query.get("job_name"):
        params["jobName"] = query["job_name"]
    if query.get("area_code"):
        params["areaCode"] = query["area_code"]
    if query.get("job_type"):
        params["jobType"] = query["job_type"]

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = _get_with_retries(http, LIST_API, params=params)
            time.sleep(LIST_REQUEST_INTERVAL_SECONDS)
            return resp.json()
        except ValueError as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"NCSS list API returned non-JSON response: {last_error}")


def _build_job(http: requests.Session, item: dict) -> dict:
    job_id = str(item.get("jobId") or "").strip()
    detail_url = DETAIL_URL.format(job_id=job_id)
    detail_html = _fetch_text(http, detail_url)
    detail = _parse_detail(detail_html)

    title = _clean_text(item.get("jobName")) or detail.get("title", "")
    company = _clean_text(item.get("recName")) or detail.get("company", "")
    city = _clean_text(item.get("areaCodeName")) or detail.get("city", "")
    salary = _format_salary(item.get("lowMonthPay"), item.get("highMonthPay"))
    education = _clean_text(item.get("degreeName")) or detail.get("education", "")

    description_parts = [
        detail.get("description", ""),
        f"专业要求：{_clean_text(item.get('major'))}" if _clean_text(item.get("major")) else "",
        f"福利标签：{_clean_text(item.get('recTags'))}" if _clean_text(item.get("recTags")) else "",
        f"招聘人数：{item.get('headCount')}人" if item.get("headCount") not in (None, "", "0", 0) else "",
        f"企业性质：{_clean_text(item.get('recProperty'))}" if _clean_text(item.get("recProperty")) else "",
        f"企业规模：{_clean_text(item.get('recScale'))}" if _clean_text(item.get("recScale")) else "",
    ]
    description = "\n".join(p for p in description_parts if p).strip()

    return {
        "source_url": detail_url,
        "raw_title": title,
        "raw_company": company,
        "raw_city": city,
        "raw_salary": salary,
        "raw_education": education,
        "raw_experience": detail.get("experience", ""),
        "raw_description": description[:8000],
        "publish_date": _parse_timestamp(item.get("publishDate") or item.get("updateDate")),
    }


def _fetch_text(http: requests.Session, url: str) -> str:
    resp = _get_with_retries(http, url)
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def _get_with_retries(http: requests.Session, url: str, params: dict | None = None) -> requests.Response:
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = http.get(url, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def _parse_detail(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = _text_first(soup, [".job-title", "h1", "title"])
    company = _text_first(soup, [".corp-name", ".company-name", ".rec-name"])
    description = _text_first(soup, [".mainContent-geshi", ".mainContent", ".job-detail", ".con-left"])

    all_text = soup.get_text("\n", strip=True)
    if not description:
        description = all_text

    return {
        "title": _strip_title_suffix(title),
        "company": company,
        "city": _extract_label_value(all_text, ["工作地点", "工作地区", "地点"]),
        "education": _extract_label_value(all_text, ["学历要求", "学历"]),
        "experience": _extract_label_value(all_text, ["工作经验", "经验"]),
        "description": _clean_text(description),
    }


def _is_relevant_it_job(item: dict) -> bool:
    return is_relevant_cs_job(
        title=_clean_text(item.get("jobName")),
        description=_clean_text(item.get("recTags")),
        major=_clean_text(item.get("major")),
        tags=_clean_text(item.get("recTags")),
    )


def _format_salary(low, high) -> str:
    try:
        low_f = float(low or 0)
        high_f = float(high or 0)
    except (TypeError, ValueError):
        return ""
    if low_f <= 0 and high_f <= 0:
        return "面议"
    if low_f > 0 and high_f > 0:
        return f"{low_f:g}-{high_f:g}K/月"
    return f"{max(low_f, high_f):g}K/月"


def _parse_timestamp(value) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        ts = float(value)
    except (TypeError, ValueError):
        return None
    if ts > 10_000_000_000:
        ts = ts / 1000
    return datetime.fromtimestamp(ts, BJ_TZ)


def _text_first(soup: BeautifulSoup, selectors: list[str]) -> str:
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            text = node.get_text("\n", strip=True)
            if text:
                return _clean_text(text)
    return ""


def _extract_label_value(text: str, labels: list[str]) -> str:
    for label in labels:
        pattern = rf"{re.escape(label)}[：:\s]*([^\n|；;，,]{{1,40}})"
        match = re.search(pattern, text)
        if match:
            return _clean_text(match.group(1))
    return ""


def _strip_title_suffix(text: str) -> str:
    text = _clean_text(text)
    return re.sub(r"-国家大学生就业服务平台$", "", text).strip()


def _clean_text(value) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
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
