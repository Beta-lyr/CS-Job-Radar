"""每日统计脚本：聚合 jobs 写入 daily_direction_stats。"""

import os
import sys
from datetime import date, datetime, timezone

from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "crawler"))
from storage.db import get_session


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
                session.execute(
                    text("""
                        INSERT INTO daily_direction_stats (stat_date, direction, city, job_count, fresh_graduate_job_count, internship_job_count, salary_median, salary_p25, salary_p75)
                        VALUES (:date, :dir, :city, :count, :fresh, :intern, :med, :p25, :p75)
                        ON CONFLICT (stat_date, direction, city) DO UPDATE SET
                            job_count = EXCLUDED.job_count,
                            fresh_graduate_job_count = EXCLUDED.fresh_graduate_job_count,
                            internship_job_count = EXCLUDED.internship_job_count,
                            salary_median = EXCLUDED.salary_median,
                            salary_p25 = EXCLUDED.salary_p25,
                            salary_p75 = EXCLUDED.salary_p75
                    """),
                    {
                        "date": today, "dir": direction, "city": city,
                        "count": rows.job_count, "fresh": rows.fresh_count,
                        "intern": rows.intern_count, "med": rows.med,
                        "p25": rows.p25, "p75": rows.p75,
                    },
                )
                total += 1

    session.commit()
    session.close()
    print(f"Generated stats for {total} direction-city combinations on {today}.")


if __name__ == "__main__":
    run()
