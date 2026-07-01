"""每日统计脚本：聚合 jobs 写入 daily_direction_stats，含 top_skills 和 top_companies。"""

import json
import os
import sys
from datetime import date, datetime, timezone

from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from services.crawler.storage.db import get_session


def _fetch_top_skills(session, direction: str, city: str | None, limit: int = 10):
    if city:
        rows = session.execute(
            text("""
                SELECT js.skill_name, COUNT(*) as cnt
                FROM job_skills js
                JOIN jobs j ON js.job_id = j.id
                WHERE j.direction = :dir AND j.city = :city
                GROUP BY js.skill_name
                ORDER BY cnt DESC
                LIMIT :lim
            """),
            {"dir": direction, "city": city, "lim": limit},
        ).fetchall()
    else:
        rows = session.execute(
            text("""
                SELECT js.skill_name, COUNT(*) as cnt
                FROM job_skills js
                JOIN jobs j ON js.job_id = j.id
                WHERE j.direction = :dir
                GROUP BY js.skill_name
                ORDER BY cnt DESC
                LIMIT :lim
            """),
            {"dir": direction, "lim": limit},
        ).fetchall()

    total = sum(r.cnt for r in rows) or 1
    return [
        {"skill": r.skill_name, "count": r.cnt, "ratio": round(r.cnt / total, 2)}
        for r in rows
    ]


def _fetch_top_companies(session, direction: str, city: str | None, limit: int = 10):
    if city:
        rows = session.execute(
            text("""
                SELECT j.company_name, COUNT(*) as cnt
                FROM jobs j
                WHERE j.direction = :dir AND j.city = :city AND j.company_name IS NOT NULL AND j.company_name != ''
                GROUP BY j.company_name
                ORDER BY cnt DESC
                LIMIT :lim
            """),
            {"dir": direction, "city": city, "lim": limit},
        ).fetchall()
    else:
        rows = session.execute(
            text("""
                SELECT j.company_name, COUNT(*) as cnt
                FROM jobs j
                WHERE j.direction = :dir AND j.company_name IS NOT NULL AND j.company_name != ''
                GROUP BY j.company_name
                ORDER BY cnt DESC
                LIMIT :lim
            """),
            {"dir": direction, "lim": limit},
        ).fetchall()

    total = sum(r.cnt for r in rows) or 1
    return [
        {"company": r.company_name, "count": r.cnt, "ratio": round(r.cnt / total, 2)}
        for r in rows
    ]


def run():
    session = get_session()
    today = date.today()

    directions = session.execute(
        text("SELECT DISTINCT direction FROM jobs WHERE direction IS NOT NULL AND direction != 'unknown'")
    ).scalars().all()

    cities = ["北京", "上海", "深圳", "杭州", "广州", None]

    total = 0
    for direction in directions:
        for city in cities:
            if city:
                rows = session.execute(
                    text("""
                        SELECT
                            COUNT(*) as job_count,
                            COUNT(*) FILTER (WHERE is_fresh_graduate_friendly) as fresh_count,
                            COUNT(*) FILTER (WHERE is_internship) as intern_count,
                            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary_median_monthly) as med,
                            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY salary_median_monthly) as p25,
                            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY salary_median_monthly) as p75
                        FROM jobs
                        WHERE direction = :dir AND city = :city
                    """),
                    {"dir": direction, "city": city},
                ).fetchone()
            else:
                rows = session.execute(
                    text("""
                        SELECT
                            COUNT(*) as job_count,
                            COUNT(*) FILTER (WHERE is_fresh_graduate_friendly) as fresh_count,
                            COUNT(*) FILTER (WHERE is_internship) as intern_count,
                            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary_median_monthly) as med,
                            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY salary_median_monthly) as p25,
                            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY salary_median_monthly) as p75
                        FROM jobs
                        WHERE direction = :dir
                    """),
                    {"dir": direction},
                ).fetchone()

            if rows and rows.job_count > 0:
                top_skills = _fetch_top_skills(session, direction, city)
                top_companies = _fetch_top_companies(session, direction, city)

                session.execute(
                    text("""
                        INSERT INTO daily_direction_stats (stat_date, direction, city, job_count, fresh_graduate_job_count, internship_job_count, salary_median, salary_p25, salary_p75, top_skills, top_companies)
                        VALUES (:date, :dir, :city, :count, :fresh, :intern, :med, :p25, :p75, :skills, :companies)
                        ON CONFLICT (stat_date, direction, city) DO UPDATE SET
                            job_count = EXCLUDED.job_count,
                            fresh_graduate_job_count = EXCLUDED.fresh_graduate_job_count,
                            internship_job_count = EXCLUDED.internship_job_count,
                            salary_median = EXCLUDED.salary_median,
                            salary_p25 = EXCLUDED.salary_p25,
                            salary_p75 = EXCLUDED.salary_p75,
                            top_skills = EXCLUDED.top_skills,
                            top_companies = EXCLUDED.top_companies
                    """),
                    {
                        "date": today, "dir": direction, "city": city,
                        "count": rows.job_count, "fresh": rows.fresh_count,
                        "intern": rows.intern_count, "med": rows.med,
                        "p25": rows.p25, "p75": rows.p75,
                        "skills": json.dumps(top_skills, ensure_ascii=False),
                        "companies": json.dumps(top_companies, ensure_ascii=False),
                    },
                )
                total += 1

    session.commit()
    session.close()
    print(f"Generated stats for {total} direction-city combinations on {today}.")


if __name__ == "__main__":
    run()
