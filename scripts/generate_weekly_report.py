"""每周报告脚本：先自动迁移 -> 读取上周统计 -> 生成 Markdown 报告 -> 写入 weekly_reports。"""

import json
import os
import sys
from datetime import date, timedelta

from sqlalchemy import text

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)
from migrate import auto_migrate

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from services.crawler.storage.db import get_session

DIRECTION_LABELS = {
    "java_backend": "Java 后端",
    "go_backend": "Go 后端",
    "frontend": "前端开发",
    "android": "Android 开发",
    "ai_application": "AI 应用开发",
    "test_development": "测试开发",
}


def get_week_range() -> tuple:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    last_monday = monday - timedelta(days=7)
    last_sunday = monday - timedelta(days=1)
    return last_monday, last_sunday


def run():
    auto_migrate()
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
    top_dir = DIRECTION_LABELS.get(rows[0].direction, rows[0].direction) if rows else "N/A"

    salary_data = session.execute(
        text("""
            SELECT direction, AVG(salary_median) as avg_salary
            FROM daily_direction_stats
            WHERE stat_date >= :start AND stat_date <= :end AND salary_median IS NOT NULL
            GROUP BY direction
            ORDER BY avg_salary DESC
        """),
        {"start": week_start, "end": week_end},
    ).fetchall()

    skill_rows = session.execute(
        text("""
            SELECT js.skill_name, COUNT(*) as cnt
            FROM job_skills js
            JOIN jobs j ON js.job_id = j.id
            WHERE j.publish_date >= :start AND j.publish_date <= :end
            GROUP BY js.skill_name
            ORDER BY cnt DESC
            LIMIT 15
        """),
        {"start": week_start, "end": week_end},
    ).fetchall()

    md = f"""# 计算机学生技术岗位趋势报告
## {week_start.isoformat()} ~ {week_end.isoformat()}

### 一、本周总览
- **有效岗位样本**：{total_jobs}
- **覆盖技术方向**：{direction_count}
- **本周热门方向**：{top_dir}

### 二、方向热度排行
| 排名 | 方向 | 岗位数量 |
|------|------|---------|
"""
    for i, r in enumerate(rows, 1):
        label = DIRECTION_LABELS.get(r.direction, r.direction)
        md += f"| {i} | {label} | {r.total_jobs} |\n"

    md += "\n### 三、薪资中位数\n"
    md += "| 方向 | 中位薪资（月薪） |\n|------|----------------:|\n"
    for r in salary_data:
        label = DIRECTION_LABELS.get(r.direction, r.direction)
        salary = f"{int(r.avg_salary / 1000)}K" if r.avg_salary else "N/A"
        md += f"| {label} | {salary} |\n"

    md += "\n### 四、技能热度榜 Top 15\n"
    md += "| 排名 | 技能 | 出现次数 |\n|------|------|--------:|\n"
    for i, s in enumerate(skill_rows, 1):
        md += f"| {i} | {s.skill_name} | {s.cnt} |\n"

    md += "\n### 五、给学生的学习建议\n"
    md += "- 关注市场趋势，但不要盲目追热点，选择与自身基础匹配的方向。\n"
    md += "- 高频技能不等于必须全部掌握，区分必备技能和加分技能。\n"
    md += "- 将学习成果转化为可展示的项目，而非停留在\u201c我知道这个技术\u201d的层面。\n"

    md += "\n---\n*报告由系统自动生成，数据来源为公开岗位样本，仅供参考。*\n"

    report_data = {
        "total_jobs": total_jobs,
        "direction_count": direction_count,
        "top_direction": top_dir,
        "directions": [{"direction": r.direction, "jobs": r.total_jobs} for r in rows],
    }

    session.execute(
        text("""
            INSERT INTO weekly_reports (week_start, week_end, title, slug, summary, content_markdown, report_data, generated_at, published_at)
            VALUES (:start, :end, :title, :slug, :summary, :content, :rdata, now(), now())
        """),
        {
            "start": week_start,
            "end": week_end,
            "title": f"计算机学生技术岗位趋势报告 {week_start.isoformat()} ~ {week_end.isoformat()}",
            "slug": slug,
            "summary": f"本周共 {total_jobs} 条样本，覆盖 {direction_count} 个方向，{top_dir} 岗位最多。",
            "content": md,
            "rdata": json.dumps(report_data, ensure_ascii=False),
        },
    )

    session.commit()
    session.close()
    print(f"Weekly report generated: {slug} ({total_jobs} jobs, {direction_count} directions).")


if __name__ == "__main__":
    run()
