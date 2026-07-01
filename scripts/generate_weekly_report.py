"""每周报告脚本：读取上周统计 -> 生成 Markdown 报告 -> 写入 weekly_reports。"""

import os
import sys
from datetime import date, timedelta

from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "crawler"))
from storage.db import get_session


def get_week_range() -> tuple:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    last_monday = monday - timedelta(days=7)
    last_sunday = monday - timedelta(days=1)
    return last_monday, last_sunday


def run():
    session = get_session()
    week_start, week_end = get_week_range()
    slug = f"{week_start.isoformat()}-to-{week_end.isoformat()}"

    existing = session.execute(
        text("SELECT id FROM weekly_reports WHERE slug = :slug"),
        {"slug": slug},
    ).fetchone()
    if existing:
        print(f"Report for {week_start} ~ {week_end} already exists. Skipping.")
        session.close()
        return

    rows = session.execute(
        text("""
            SELECT direction, SUM(job_count) as total_jobs
            FROM daily_direction_stats
            WHERE stat_date >= :start AND stat_date <= :end
            GROUP BY direction
            ORDER BY total_jobs DESC
        """),
        {"start": week_start, "end": week_end},
    ).fetchall()

    total_jobs = sum(r.total_jobs for r in rows)
    direction_count = len(rows)
    top_dir = rows[0].direction if rows else "N/A"

    md = f"""# 计算机学生技术岗位趋势报告
## {week_start.isoformat()} ~ {week_end.isoformat()}

### 本周总览
- 本周有效岗位样本：{total_jobs}
- 覆盖方向数：{direction_count}
- 热门方向：{top_dir}

### 方向热度排行
| 方向 | 岗位数量 |
|------|---------|
"""
    for r in rows:
        md += f"| {r.direction} | {r.total_jobs} |\n"

    md += "\n---\n*报告自动生成，仅供参考。*\n"

    session.execute(
        text("""
            INSERT INTO weekly_reports (week_start, week_end, title, slug, summary, content_markdown, generated_at, published_at)
            VALUES (:start, :end, :title, :slug, :summary, :content, now(), now())
        """),
        {
            "start": week_start,
            "end": week_end,
            "title": f"计算机学生技术岗位趋势报告 {week_start.isoformat()} ~ {week_end.isoformat()}",
            "slug": slug,
            "summary": f"本周共 {total_jobs} 条样本，覆盖 {direction_count} 个方向，{top_dir} 岗位最多。",
            "content": md,
        },
    )

    session.commit()
    session.close()
    print(f"Weekly report generated: {slug} ({total_jobs} jobs, {direction_count} directions).")


if __name__ == "__main__":
    run()
