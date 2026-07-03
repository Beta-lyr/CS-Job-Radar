"""每周报告脚本：先自动迁移 -> 读取最近 7 天岗位样本 -> 生成 Markdown 报告。"""

import json
import os
import sys
from datetime import date, timedelta

from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db.migrate import auto_migrate

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from services.crawler.storage.db import get_session
from services.reporter.analyzer import generate_analysis, is_llm_configured

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
_TEMPLATE_DIR = os.path.join(_REPO_ROOT, "services", "reporter", "templates")

DIRECTION_LABELS = {
    "java_backend": "Java 后端",
    "go_backend": "Go 后端",
    "frontend": "前端开发",
    "android": "Android 开发",
    "ai_application": "AI 应用开发",
    "test_development": "测试开发",
    "cpp_system": "C++ / 系统开发",
    "embedded": "嵌入式开发",
    "hardware": "硬件开发",
    "semiconductor": "半导体 / 芯片",
    "communication": "通信网络",
    "it_support_implementation": "实施 / 技术支持",
    "product_manager": "技术产品",
    "unknown": "未归类",
}


def get_report_range(session) -> tuple[date, date]:
    row = session.execute(text("SELECT MAX(fetched_at)::date AS max_date FROM jobs")).fetchone()
    end = row.max_date if row and row.max_date else date.today()
    start = end - timedelta(days=6)
    return start, end


def _direction_counts(session, start: date, end: date) -> list:
    return session.execute(
        text("""
            SELECT direction, COUNT(*)::int as total_jobs
            FROM jobs
            WHERE fetched_at >= :start
              AND fetched_at < (:end + INTERVAL '1 day')
              AND direction IS NOT NULL
              AND direction != 'unknown'
            GROUP BY direction
            ORDER BY total_jobs DESC
        """),
        {"start": start, "end": end},
    ).fetchall()


def query_current_week(session, start: date, end: date) -> dict:
    rows = _direction_counts(session, start, end)
    total_jobs = sum(r.total_jobs for r in rows)
    direction_count = len(rows)

    directions = [
        {
            "direction": r.direction,
            "label": DIRECTION_LABELS.get(r.direction, r.direction),
            "count": r.total_jobs,
        }
        for r in rows
    ]

    salary_rows = session.execute(
        text("""
            SELECT
                direction,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary_median_monthly)::int as median_salary,
                COUNT(salary_median_monthly)::int as salary_sample_count
            FROM jobs
            WHERE fetched_at >= :start
              AND fetched_at < (:end + INTERVAL '1 day')
              AND direction IS NOT NULL
              AND direction != 'unknown'
              AND salary_median_monthly IS NOT NULL
            GROUP BY direction
            ORDER BY median_salary DESC
        """),
        {"start": start, "end": end},
    ).fetchall()

    salaries = []
    for r in salary_rows:
        label = DIRECTION_LABELS.get(r.direction, r.direction)
        salaries.append({
            "direction": r.direction,
            "label": label,
            "median": r.median_salary or 0,
            "median_text": f"{int(r.median_salary / 1000)}K" if r.median_salary else "N/A",
            "sample_count": r.salary_sample_count,
        })

    skill_rows = session.execute(
        text("""
            SELECT js.skill_name, COUNT(*) as cnt
            FROM job_skills js
            JOIN jobs j ON js.job_id = j.id
            WHERE j.fetched_at >= :start
              AND j.fetched_at < (:end + INTERVAL '1 day')
              AND j.direction IS NOT NULL
              AND j.direction != 'unknown'
            GROUP BY js.skill_name
            ORDER BY cnt DESC
            LIMIT 15
        """),
        {"start": start, "end": end},
    ).fetchall()

    skills = [{"name": r.skill_name, "count": r.cnt} for r in skill_rows]

    return {
        "total_jobs": total_jobs,
        "direction_count": direction_count,
        "directions": directions,
        "salaries": salaries,
        "skills": skills,
    }


def query_previous_week(session, start: date, end: date) -> dict:
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=6)
    rows = _direction_counts(session, prev_start, prev_end)
    direction_map = {r.direction: r.total_jobs for r in rows}
    return {"directions": direction_map}


def _calc_change(curr: int, prev: int | None) -> str:
    if prev is None or prev == 0:
        return "-"
    delta = (curr - prev) / prev * 100
    return f"{delta:+.0f}%"


def build_report_data(current: dict, previous: dict) -> dict:
    prev_map = previous.get("directions", {})
    for d in current["directions"]:
        prev_count = prev_map.get(d["direction"])
        d["change"] = _calc_change(d["count"], prev_count)

    if current["directions"]:
        current["top_direction"] = current["directions"][0]["label"]
    else:
        current["top_direction"] = "N/A"

    return current


def generate_report_markdown(data: dict, analysis, week_start: date, week_end: date) -> str:
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR))
    template = env.get_template("weekly_report.md.j2")

    default_summary = (
        f"本周共采集 {data['total_jobs']} 条有效岗位样本，"
        f"覆盖 {data['direction_count']} 个技术方向，"
        f"{data['top_direction']} 岗位数量最多。"
    )

    dir_labels = ", ".join(d["label"] for d in data["directions"][:5])
    default_direction = (
        f"本周岗位主要集中在 {dir_labels} 等方向。"
        f"建议学生关注岗位数量较多且增长明显的方向，结合自身专业基础选择深耕领域。"
    )

    top_skills = ", ".join(s["name"] for s in data["skills"][:5])
    default_skill = (
        f"本周需求最高的技能为 {top_skills}。"
        f"这些技能横跨多个技术方向，体现了企业在招聘中对工程能力的通用要求。"
    )

    default_advice = (
        '- 关注市场趋势，但不要盲目追热点，选择与自身基础匹配的方向。\n'
        '- 高频技能不等于必须全部掌握，区分必备技能和加分技能。\n'
        '- 将学习成果转化为可展示的项目，而非停留在"我知道这个技术"的层面。'
    )

    return template.render(
        week_start=week_start.isoformat(),
        week_end=week_end.isoformat(),
        total_jobs=data["total_jobs"],
        direction_count=data["direction_count"],
        directions=data["directions"],
        salaries=data["salaries"],
        skills=data["skills"],
        analysis=analysis,
        default_summary=default_summary,
        default_direction=default_direction,
        default_skill=default_skill,
        default_advice=default_advice,
    )


def save_report(session, markdown: str, data: dict, week_start: date, week_end: date):
    slug = f"{week_start.isoformat()}-to-{week_end.isoformat()}"
    title = f"计算机学生技术岗位趋势报告 {week_start.isoformat()} ~ {week_end.isoformat()}"
    summary = data.get("top_direction", "")

    report_data = {
        "total_jobs": data["total_jobs"],
        "direction_count": data["direction_count"],
        "top_direction": data["top_direction"],
        "directions": data["directions"],
        "salaries": data["salaries"],
        "skills": data["skills"],
    }

    session.execute(
        text("""
            INSERT INTO weekly_reports (week_start, week_end, title, slug, summary, content_markdown, report_data, generated_at, published_at)
            VALUES (:start, :end, :title, :slug, :summary, :content, :rdata, now(), now())
            ON CONFLICT (slug) DO UPDATE SET
                title = EXCLUDED.title,
                summary = EXCLUDED.summary,
                content_markdown = EXCLUDED.content_markdown,
                report_data = EXCLUDED.report_data,
                generated_at = now(),
                published_at = now()
        """),
        {
            "start": week_start,
            "end": week_end,
            "title": title,
            "slug": slug,
            "summary": summary,
            "content": markdown,
            "rdata": json.dumps(report_data, ensure_ascii=False),
        },
    )
    session.commit()
    return slug


def run():
    auto_migrate()
    session = get_session()

    try:
        week_start, week_end = get_report_range(session)

        current = query_current_week(session, week_start, week_end)
        previous = query_previous_week(session, week_start, week_end)
        report_data = build_report_data(current, previous)
        report_data["week_start"] = week_start.isoformat()
        report_data["week_end"] = week_end.isoformat()

        analysis = generate_analysis(report_data) if is_llm_configured() else None

        markdown = generate_report_markdown(report_data, analysis, week_start, week_end)
        slug = save_report(session, markdown, report_data, week_start, week_end)

        llm_status = "with AI" if analysis else "without AI"
        print(f"[report] {slug}: {report_data['total_jobs']} jobs, {report_data['direction_count']} directions {llm_status}")
    finally:
        session.close()


if __name__ == "__main__":
    run()
