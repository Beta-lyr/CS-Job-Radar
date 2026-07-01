import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .base import BaseParser, RawJobDTO


class GenericParser(BaseParser):
    def parse_list(self, html: str, base_url: str) -> list[str]:
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
            if self._looks_like_job_link(full_url, text):
                links.add(full_url)

        return list(links)

    def parse_detail(self, html: str, url: str) -> RawJobDTO:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)

        title = self._extract_title(soup, text)
        company = self._extract_company(soup, text)
        city = self._extract_city(soup, text)
        salary = self._extract_salary(text)
        education = self._extract_education(text)
        experience = self._extract_experience(text)
        description = self._extract_description(soup, text)
        publish_date = self._extract_date(soup, text)

        return RawJobDTO(
            source_url=url,
            raw_title=title,
            raw_company=company,
            raw_city=city,
            raw_salary=salary,
            raw_education=education,
            raw_experience=experience,
            raw_description=description,
            publish_date=publish_date,
        )

    def _looks_like_job_link(self, url: str, text: str) -> bool:
        url_lower = url.lower()
        text_lower = text.lower()
        job_keywords = ["招聘", "岗位", "职位", "job", "career", "position", "detail", "info"]
        for kw in job_keywords:
            if kw in url_lower or kw in text_lower:
                return True
        if len(text) >= 4 and any(kw in text for kw in ["工程师", "开发", "经理", "专员", "实习", "校招"]):
            return True
        return False

    def _extract_title(self, soup, text: str) -> str:
        for selector in ["h1", "title", '[class*="title"]', '[class*="job-name"]', '[class*="position"]']:
            el = soup.select_one(selector)
            if el:
                t = el.get_text(strip=True)
                if len(t) >= 3:
                    return t

        patterns = [
            r"岗位[名称]?[：:]\s*(.+)",
            r"职位[名称]?[：:]\s*(.+)",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return m.group(1).strip()[:120]

        lines = [l.strip() for l in text.split("\n") if 3 <= len(l.strip()) <= 80]
        job_keywords = ["工程师", "开发", "经理", "专员", "实习", "校招", "前端", "后端", "测试", "Android", "AI"]
        for line in lines:
            if any(kw in line for kw in job_keywords):
                return line[:120]
        return lines[0][:120] if lines else ""

    def _extract_company(self, soup, text: str) -> str:
        for selector in ['[class*="company"]', '[class*="corp"]', '[class*="employer"]']:
            el = soup.select_one(selector)
            if el:
                t = el.get_text(strip=True)
                if len(t) >= 2:
                    return t

        patterns = [r"公司[名称]?[：:]\s*(.+)", r"企业[：:]\s*(.+)"]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return m.group(1).strip()[:100]
        return ""

    def _extract_city(self, soup, text: str) -> str:
        for selector in ['[class*="city"]', '[class*="location"]', '[class*="address"]']:
            el = soup.select_one(selector)
            if el:
                t = el.get_text(strip=True)
                for city in ["北京", "上海", "深圳", "杭州", "广州"]:
                    if city in t:
                        return city
                return t[:20]

        patterns = [
            r"(?:工作)?地点[：:]\s*(.+)",
            r"(?:所在)?城市[：:]\s*(.+)",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                loc = m.group(1).strip()
                for city in ["北京", "上海", "深圳", "杭州", "广州"]:
                    if city in loc:
                        return city
                return loc[:20]
        return ""

    def _extract_salary(self, text: str) -> str:
        patterns = [
            r"(\d+[-~]\d+[Kk万wW].*?(?:薪|/月|/年)?)",
            r"(面议)",
            r"(\d+[-~]\d+[元]/[天日])",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return m.group(1).strip()
        return ""

    def _extract_education(self, text: str) -> str:
        patterns = [
            r"学历[要求]?[：:]\s*(.+)",
            r"教育[程度]?[：:]\s*(.+)",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return m.group(1).strip()[:20]

        edu_keywords = ["博士", "硕士", "本科", "大专", "学历不限", "研究生"]
        for kw in edu_keywords:
            if kw in text:
                return kw
        return ""

    def _extract_experience(self, text: str) -> str:
        patterns = [
            r"(?:工作)?经验[要求]?[：:]\s*(.+)",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return m.group(1).strip()[:30]

        exp_keywords = ["应届", "经验不限", "1-3年", "3-5年", "1年以下"]
        for kw in exp_keywords:
            if kw in text:
                return kw
        return ""

    def _extract_description(self, soup, text: str) -> str:
        for selector in [
            '[class*="description"]',
            '[class*="content"]',
            '[class*="detail"]',
            '[class*="requirement"]',
            '[class*="duty"]',
            "article",
        ]:
            els = soup.select(selector)
            if els:
                combined = "\n".join(el.get_text(separator="\n", strip=True) for el in els)
                if len(combined) >= 50:
                    return combined[:5000]

        patterns = [
            r"(?:岗位职责|工作内容|任职要求|职位描述|岗位要求)[：:](.+)",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.DOTALL)
            if m:
                return m.group(1).strip()[:5000]

        cleaned = text[:5000]
        for prefix in ["岗位描述", "职位描述", "Job Description"]:
            idx = cleaned.find(prefix)
            if idx >= 0:
                return cleaned[idx + len(prefix):].strip()[:5000]
        return cleaned

    def _extract_date(self, soup, text: str) -> datetime | None:
        for selector in ["time", '[class*="date"]', '[class*="time"]', '[class*="publish"]']:
            el = soup.select_one(selector)
            if el:
                dt_str = el.get("datetime") or el.get_text(strip=True)
                return _try_parse_date(dt_str)

        patterns = [
            r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
            r"发布(?:时间|于)[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return _try_parse_date(m.group(1))

        return None


def _try_parse_date(s: str) -> datetime | None:
    if not s:
        return None
    s = s.strip().replace("/", "-")
    for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None
