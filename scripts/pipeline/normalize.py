"""标准化脚本：处理 raw_jobs -> 写入 jobs + job_skills。"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

from sqlalchemy import text

BJ_TZ = timezone(timedelta(hours=8))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from services.crawler.storage.db import get_session
from services.analyzer.extractors.skill_extractor import extract_skills
from services.analyzer.classifiers.fresh_graduate_classifier import classify_fresh_graduate, classify_internship, classify_campus
from services.analyzer.classifiers.confidence_scorer import calc_confidence
from services.analyzer.normalizers.city_normalizer import normalize_city as normalize_city_from_rules


def parse_salary(text: str) -> dict:
    if not text:
        return {"type": "unknown"}
    text = text.strip()
    if text == "面议":
        return {"type": "negotiable"}

    m = re.search(r"(\d+)-(\d+)K", text, re.IGNORECASE)
    if m:
        lo, hi = int(m.group(1)) * 1000, int(m.group(2)) * 1000
        months = 12
        mm = re.search(r"(\d+)[薪]", text)
        if mm:
            months = int(mm.group(1))
        return {
            "min": lo, "max": hi, "median": (lo + hi) // 2,
            "months": months, "type": "monthly",
        }

    m = re.search(r"(\d+)-(\d+)万/年", text)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return {
            "min": round(lo * 10000 / 12), "max": round(hi * 10000 / 12),
            "median": round((lo + hi) * 10000 / 24), "months": 12, "type": "yearly",
        }

    m = re.search(r"(\d+)/天", text)
    if m:
        return {"type": "intern_daily"}

    return {"type": "unknown"}


def normalize_city(raw: str) -> tuple:
    return normalize_city_from_rules(raw)


def normalize_education(raw: str) -> str:
    if not raw:
        return "unknown"
    if "博士" in raw:
        return "phd"
    if "硕士" in raw or "研究生" in raw:
        return "master"
    if "本科" in raw:
        return "bachelor"
    if "大专" in raw:
        return "junior_college"
    if "不限" in raw:
        return "none"
    return "unknown"


def normalize_experience(raw: str) -> str:
    if not raw:
        return "unknown"
    if "应届" in raw:
        return "fresh"
    if "经验不限" in raw or "不限" in raw:
        return "none"
    if "1年以下" in raw or "1年以内" in raw:
        return "lt_1_year"
    if "1-3" in raw:
        return "one_to_three"
    if "3-5" in raw:
        return "three_to_five"
    if "5年" in raw:
        return "five_plus"
    return "unknown"


def _load_direction_rules() -> dict:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "direction-rules", "rules.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


_direction_rules: dict | None = None


def detect_direction(title: str, desc: str) -> str:
    global _direction_rules
    if _direction_rules is None:
        _direction_rules = _load_direction_rules()

    title_lower = (title or "").lower()
    desc_lower = (desc or "").lower()

    scores: dict[str, int] = {}
    for direction, rule in _direction_rules.items():
        score = 0
        for kw in rule.get("title_keywords", []):
            if kw in title_lower:
                score += rule.get("title_weight", 5)
        for kw in rule.get("jd_keywords", []):
            if kw in desc_lower:
                score += rule.get("jd_weight", 3)
        if score > 0:
            scores[direction] = score

    if not scores:
        return "unknown"
    return max(scores, key=scores.get)


def run():
    session = get_session()

    source_types = dict(session.execute(
        text("SELECT id, source_type FROM sources")
    ).fetchall())

    rows = session.execute(
        text("SELECT id, source_id, raw_title, raw_company, raw_city, raw_salary, raw_education, raw_experience, raw_description, publish_date FROM raw_jobs WHERE parse_status = 'pending'")
    ).fetchall()

    if not rows:
        print("No pending raw_jobs to normalize.")
        session.close()
        return

    count = 0
    for row in rows:
        rid = row.id
        source_id = row.source_id
        title = row.raw_title or ""
        company = row.raw_company or ""
        raw_city = row.raw_city or ""
        raw_salary = row.raw_salary or ""
        raw_edu = row.raw_education or ""
        raw_exp = row.raw_experience or ""
        desc = row.raw_description or ""
        publish_date = row.publish_date

        salary = parse_salary(raw_salary)
        city, district = normalize_city(raw_city)
        edu = normalize_education(raw_edu)
        exp = normalize_experience(raw_exp)
        direction = detect_direction(title, desc)

        is_friendly, fresh_score = classify_fresh_graduate(title, desc, exp, edu)
        is_internship = classify_internship(title, desc)
        is_campus = classify_campus(title, desc)

        source_type = source_types.get(source_id, "university")
        confidence = calc_confidence(source_type, title, company, city, raw_salary, desc, publish_date, direction)

        session.execute(
            text("""
                INSERT INTO jobs (raw_job_id, title, company_name, city, district, salary_text, salary_min_monthly, salary_max_monthly, salary_median_monthly, salary_months, salary_type, education_text, education_level, experience_text, experience_level, direction, is_internship, is_campus, is_fresh_graduate_friendly, fresh_graduate_score, description_clean, confidence_score, publish_date, fetched_at)
                VALUES (:rid, :title, :company, :city, :district, :stext, :smin, :smax, :smed, :smonths, :stype, :edutext, :edulevel, :exptext, :explevel, :dir, :intern, :campus, :friendly, :fresh_score, :desc, :conf, :pdate, :fetched)
                ON CONFLICT (raw_job_id) DO NOTHING
            """),
            {
                "rid": rid, "title": title, "company": company,
                "city": city, "district": district,
                "stext": raw_salary, "smin": salary.get("min"), "smax": salary.get("max"),
                "smed": salary.get("median"), "smonths": salary.get("months"), "stype": salary.get("type"),
                "edutext": raw_edu, "edulevel": edu,
                "exptext": raw_exp, "explevel": exp,
                "dir": direction, "intern": is_internship, "campus": is_campus,
                "friendly": is_friendly, "fresh_score": fresh_score,
                "desc": desc[:5000], "conf": confidence,
                "pdate": publish_date, "fetched": datetime.now(BJ_TZ),
            },
        )

        job_result = session.execute(
            text("SELECT id FROM jobs WHERE raw_job_id = :rid"),
            {"rid": rid},
        ).fetchone()

        if job_result:
            job_id = job_result.id
            skills = extract_skills(title, desc)
            for skill in skills:
                session.execute(
                    text("""
                        INSERT INTO job_skills (job_id, skill_name, skill_category, is_required, is_bonus, confidence)
                        VALUES (:job_id, :name, :category, :required, :bonus, :conf)
                    """),
                    {
                        "job_id": job_id,
                        "name": skill["skill_name"],
                        "category": skill["skill_category"],
                        "required": skill["is_required"],
                        "bonus": skill["is_bonus"],
                        "conf": skill["confidence"],
                    },
                )

        session.execute(
            text("UPDATE raw_jobs SET parse_status = 'parsed', updated_at = now() WHERE id = :id"),
            {"id": rid},
        )
        count += 1

    session.commit()
    session.close()
    print(f"Normalized {count} jobs.")


if __name__ == "__main__":
    run()
