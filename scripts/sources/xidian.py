"""
西安电子科技大学就业信息网采集脚本。

页面结构：
- 列表页: job.xidian.edu.cn 首页，招聘信息以列表形式展示
- 详情页: 每条招聘信息有独立页面

自定义规则：
- 列表链接提取：从首页 DOM 中找到招聘信息列表区域的 <a> 标签
- 详情页解析：从详情页提取标题、公司、城市、薪资、描述等字段
"""

import re
import sys
import os
from datetime import datetime

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from services.crawler.utils.hash import url_hash, content_hash
from services.crawler.parsers.base import RawJobDTO


def crawl(session, source_id: int, list_url: str, fetcher) -> dict:
    result = {"inserted": 0, "skipped": 0, "error": ""}

    try:
        list_html = fetcher.fetch(list_url)
        detail_urls = _extract_job_links(list_html, list_url)

        if not detail_urls:
            result["error"] = "No job links found"
            return result

        detail_urls = detail_urls[:30]
        jobs: list[RawJobDTO] = []

        for detail_url in detail_urls:
            try:
                detail_html = fetcher.fetch(detail_url)
                job = _parse_detail(detail_html, detail_url)
                if job.raw_title:
                    jobs.append(job)
            except Exception:
                continue

        for job in jobs:
            uh = url_hash(job.source_url)
            ch = content_hash(job.raw_title or "", job.raw_company or "", job.raw_city or "", job.raw_description or "")
            r = _insert(session, source_id, job, uh, ch)
            if r:
                result["inserted"] += 1
            else:
                result["skipped"] += 1

    except Exception as e:
        result["error"] = str(e)[:500]

    return result


def _extract_job_links(html: str, base_url: str) -> list[str]:
    """从列表页提取招聘信息链接。"""
    from urllib.parse import urljoin, urlparse

    soup = BeautifulSoup(html, "html.parser")
    links = set()
    domain = urlparse(base_url).netloc

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue
        full_url = urljoin(base_url, href)
        if urlparse(full_url).netloc != domain:
            continue
        text = a.get_text(strip=True)
        if _looks_like_job(text, full_url):
            links.add(full_url)

    return list(links)


def _looks_like_job(text: str, url: str) -> bool:
    url_lower = url.lower()
    for kw in ["招聘", "岗位", "职位", "detail", "info", "zpxx", "zpinfo"]:
        if kw in url_lower:
            return True
    if len(text) >= 4 and any(kw in text for kw in ["工程师", "开发", "经理", "专员", "实习", "校招", "招聘"]):
        return True
    return False


def _parse_detail(html: str, url: str) -> RawJobDTO:
    """从详情页提取岗位字段。"""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n", strip=True)

    return RawJobDTO(
        source_url=url,
        raw_title=_extract_title(soup, text),
        raw_company=_extract_company(soup, text),
        raw_city=_extract_city(text),
        raw_salary=_extract_salary(text),
        raw_education=_extract_education(text),
        raw_experience=_extract_experience(text),
        raw_description=_extract_description(soup, text),
        publish_date=_extract_date(text),
    )


def _extract_title(soup, text: str) -> str:
    for selector in ["h1", "title", '[class*="title"]', '[class*="bt"]']:
        el = soup.select_one(selector)
        if el:
            t = el.get_text(strip=True)
            if 3 <= len(t) <= 120:
                return t
    m = re.search(r"(?:招聘|岗位|职位)[：:]\s*(.+)", text)
    if m:
        return m.group(1).strip()[:120]
    return ""


def _extract_company(soup, text: str) -> str:
    for sel in ['[class*="company"]', '[class*="dw"]', '[class*="corp"]']:
        el = soup.select_one(sel)
        if el:
            t = el.get_text(strip=True)
            if len(t) >= 2:
                return t
    m = re.search(r"(?:单位|公司|企业)[：:]\s*(.+)", text)
    if m:
        return m.group(1).strip()[:100]
    return ""


def _extract_city(text: str) -> str:
    for city in ["北京", "上海", "深圳", "杭州", "广州", "西安", "成都", "武汉", "南京"]:
        if city in text:
            return city
    return ""


def _extract_salary(text: str) -> str:
    m = re.search(r"(\d+[-~]\d+[Kk万wW].*?(?:薪|/月)?)", text)
    if m:
        return m.group(1).strip()
    if "面议" in text:
        return "面议"
    return ""


def _extract_education(text: str) -> str:
    for kw in ["博士", "硕士", "本科", "大专", "学历不限"]:
        if kw in text:
            return kw
    return ""


def _extract_experience(text: str) -> str:
    for kw in ["应届", "经验不限", "1-3年", "3-5年", "1年以下"]:
        if kw in text:
            return kw
    return ""


def _extract_description(soup, text: str) -> str:
    for sel in ['[class*="content"]', '[class*="detail"]', '[class*="nr"]', "article"]:
        els = soup.select(sel)
        if els:
            combined = "\n".join(el.get_text(separator="\n", strip=True) for el in els)
            if len(combined) >= 50:
                return combined[:5000]
    return text[:5000]


def _extract_date(text: str) -> datetime | None:
    m = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})", text)
    if m:
        try:
            s = m.group(1).replace("/", "-")
            return datetime.strptime(s, "%Y-%m-%d")
        except ValueError:
            pass
    return None


def _insert(session, source_id: int, job: RawJobDTO, uh: str, ch: str) -> bool:
    from sqlalchemy import text
    r = session.execute(
        text("""
            INSERT INTO raw_jobs (source_id, source_url, source_url_hash, raw_title, raw_company, raw_city, raw_salary, raw_education, raw_experience, raw_description, publish_date, raw_hash, parse_status)
            VALUES (:sid, :url, :url_hash, :title, :company, :city, :salary, :edu, :exp, :desc, :pdate, :raw_hash, 'pending')
            ON CONFLICT (source_url_hash) DO NOTHING
        """),
        {
            "sid": source_id, "url": job.source_url, "url_hash": uh,
            "title": job.raw_title or "", "company": job.raw_company or "",
            "city": job.raw_city or "", "salary": job.raw_salary or "",
            "edu": job.raw_education or "", "exp": job.raw_experience or "",
            "desc": (job.raw_description or "")[:8000].replace("\x00", ""),
            "pdate": job.publish_date or datetime.now(),
            "raw_hash": ch,
        },
    )
    return r.rowcount > 0
