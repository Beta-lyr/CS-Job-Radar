"""
西安电子科技大学就业信息网采集脚本。

页面结构：
- 列表页: /campus，JS 动态渲染，需 Playwright
- 详情页: /campus/view/id/{id}，标题/公司/日期为静态 HTML，正文 JS 渲染
"""

import re
import sys
import os
from datetime import datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from services.crawler.utils.hash import url_hash, content_hash

BASE_URL = "https://job.xidian.edu.cn"
MAX_PAGES = 20
MAX_JOBS_TOTAL = 200


def crawl(session, source_id: int, list_url: str, fetcher) -> dict:
    result = {"inserted": 0, "skipped": 0, "error": ""}

    try:
        all_links: set[str] = set()

        for page in range(1, MAX_PAGES + 1):
            if len(all_links) >= MAX_JOBS_TOTAL:
                break

            page_url = _paginated_url(list_url, page)
            try:
                html = fetcher.fetch(page_url)
                page_links = set(_extract_job_links(html))
                new_links = page_links - all_links
                if not new_links and page > 1:
                    break
                all_links.update(page_links)
            except Exception:
                if page == 1:
                    raise
                break

        detail_urls = list(all_links)[:MAX_JOBS_TOTAL]

        for detail_url in detail_urls:
            try:
                detail_html = fetcher.fetch(detail_url)
                job = _parse_detail(detail_html, detail_url)
                if not job.get("raw_title"):
                    continue

                uh = url_hash(detail_url)
                ch = content_hash(job["raw_title"], job.get("raw_company", ""), job.get("raw_city", ""), job.get("raw_description", ""))
                r = _insert(session, source_id, job, uh, ch)
                if r:
                    result["inserted"] += 1
                else:
                    result["skipped"] += 1
            except Exception:
                continue

    except Exception as e:
        result["error"] = str(e)[:500]

    return result


def _paginated_url(list_url: str, page: int) -> str:
    if page == 1:
        return list_url
    return f"{list_url.rstrip('/')}/index/do1/job.xidian.edu.cn/domain/xidian/city//page/{page}"


def _extract_job_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        m = re.search(r"/campus/view/id/(\d+)", href)
        if m:
            full_url = urljoin(BASE_URL, href)
            links.add(full_url)

    return list(links)


def _parse_detail(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    title_el = soup.select_one(".details-title .title-message h5")
    title = title_el.get_text(strip=True) if title_el else ""

    company_el = soup.select_one(".details-title .title-message .name.text-primary")
    company = company_el.get_text(strip=True) if company_el else ""

    date_str = ""
    date_el = soup.find("li", string=re.compile(r"发布时间："))
    if date_el:
        date_str = date_el.get_text(strip=True)
        date_str = date_str.replace("发布时间：", "").strip()

    city = _extract_city(soup)

    salary_text = ""
    salary_sel = soup.find(string=re.compile(r"薪资|月薪|待遇"))
    if salary_sel:
        salary_text = salary_sel.strip()

    content_el = soup.select_one(".details-mge .info .aContent")
    description = content_el.get_text(separator="\n", strip=True) if content_el else ""

    warning_el = soup.select_one(".common-view-tips")
    if warning_el:
        warning_el.decompose()
    if not description:
        description = soup.select_one(".details-mge .info")
        description = description.get_text(separator="\n", strip=True) if description else ""

    body_text = soup.get_text()
    education = _first_match(body_text, [r"学历[要求]?[：:]\s*(\S+)", r"学历(\S{2,4})"])
    experience = _first_match(body_text, [r"经验[要求]?[：:]\s*(\S+)", r"工作年限[：:]\s*(\S+)"])

    publish_date = _parse_date(date_str)

    return {
        "source_url": url,
        "raw_title": title,
        "raw_company": company,
        "raw_city": city,
        "raw_salary": salary_text,
        "raw_education": education,
        "raw_experience": experience,
        "raw_description": description[:8000] if description else body_text[:8000],
        "publish_date": publish_date,
    }


def _extract_city(soup) -> str:
    body = soup.get_text()
    for c in ["西安", "北京", "上海", "深圳", "杭州", "广州", "成都", "武汉", "南京"]:
        if c in body:
            return c
    return "西安"


def _first_match(text: str, patterns: list[str]) -> str:
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1).strip()[:30]
    return ""


def _parse_date(s: str) -> datetime | None:
    if not s:
        return None
    m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def _insert(session, source_id: int, job: dict, uh: str, ch: str) -> bool:
    from sqlalchemy import text
    r = session.execute(
        text("""
            INSERT INTO raw_jobs (source_id, source_url, source_url_hash, raw_title, raw_company, raw_city, raw_salary, raw_education, raw_experience, raw_description, publish_date, raw_hash, parse_status)
            VALUES (:sid, :url, :url_hash, :title, :company, :city, :salary, :edu, :exp, :desc, :pdate, :raw_hash, 'pending')
            ON CONFLICT (source_url_hash) DO NOTHING
        """),
        {
            "sid": source_id, "url": job.get("source_url", ""), "url_hash": uh,
            "title": job.get("raw_title", ""), "company": job.get("raw_company", ""),
            "city": job.get("raw_city", ""), "salary": job.get("raw_salary", ""),
            "edu": job.get("raw_education", ""), "exp": job.get("raw_experience", ""),
            "desc": (job.get("raw_description", "") or "")[:8000].replace("\x00", ""),
            "pdate": job.get("publish_date") or datetime.now(),
            "raw_hash": ch,
        },
    )
    return r.rowcount > 0
