import { query } from "@/lib/db"
import type { HomeOverview, DirectionStat, SkillStat, WeeklyReportSummary } from "@/types/stats"

export async function getHomeOverview(): Promise<HomeOverview> {
  try {
    const result = await query(`
      SELECT
        COUNT(*)::int AS total_jobs,
        COALESCE(COUNT(DISTINCT direction), 0)::int AS direction_count,
        COALESCE(COUNT(DISTINCT city), 0)::int AS city_count,
        COALESCE(ROUND(COUNT(*) FILTER (WHERE is_fresh_graduate_friendly) * 100.0 / NULLIF(COUNT(*), 0))::int, 0) AS friendly_ratio
      FROM jobs
      WHERE fetched_at >= CURRENT_DATE - INTERVAL '30 days'
    `)
    const row = result.rows[0]
    return {
      totalJobs: row?.total_jobs ?? 0,
      directionCount: row?.direction_count ?? 0,
      cityCount: row?.city_count ?? 0,
      friendlyRatio: row?.friendly_ratio ?? 0,
    }
  } catch (e) {
    console.error("getHomeOverview error:", e)
    return { totalJobs: 0, directionCount: 0, cityCount: 0, friendlyRatio: 0 }
  }
}

export async function getDirectionStats(): Promise<DirectionStat[]> {
  try {
    const result = await query(`
      SELECT
        direction,
        COUNT(*)::int AS job_count,
        COUNT(*) FILTER (WHERE is_fresh_graduate_friendly)::int AS friendly_count,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary_median_monthly)::int AS salary_median
      FROM jobs
      WHERE fetched_at >= CURRENT_DATE - INTERVAL '30 days'
        AND direction IS NOT NULL
      GROUP BY direction
      ORDER BY COUNT(*) DESC
    `)
    const maxJobs = Math.max(...result.rows.map((r: { job_count: number }) => r.job_count), 1)
    return result.rows.map((row: { direction: string; job_count: number; friendly_count: number; salary_median: number | null }) => ({
      direction: row.direction,
      jobCount: row.job_count,
      friendlyCount: row.friendly_count,
      salaryMedian: row.salary_median,
      topSkills: [],
      opportunityIndex: Math.round((row.job_count / maxJobs) * 100),
    }))
  } catch (e) {
    console.error("getDirectionStats error:", e)
    return []
  }
}

export async function getTopSkills(): Promise<SkillStat[]> {
  try {
    const result = await query(`
      SELECT
        js.skill_name,
        COUNT(DISTINCT js.job_id)::int AS job_count
      FROM job_skills js
      JOIN jobs j ON js.job_id = j.id
      WHERE j.fetched_at >= CURRENT_DATE - INTERVAL '30 days'
      GROUP BY js.skill_name
      ORDER BY COUNT(DISTINCT js.job_id) DESC
      LIMIT 10
    `)
    const maxCount = result.rows.length > 0 ? Math.max(...result.rows.map((r: { job_count: number }) => r.job_count)) : 1
    return result.rows.map((row: { skill_name: string; job_count: number }) => ({
      skillName: row.skill_name,
      jobCount: row.job_count,
      percentage: Math.round((row.job_count / maxCount) * 100),
    }))
  } catch (e) {
    console.error("getTopSkills error:", e)
    return []
  }
}

export async function getLatestReport(): Promise<WeeklyReportSummary | null> {
  try {
    const result = await query(`
      SELECT title, slug, summary, week_start::text AS week_start, week_end::text AS week_end
      FROM weekly_reports
      ORDER BY week_start DESC
      LIMIT 1
    `)
    const row = result.rows[0]
    if (!row) return null
    return {
      title: row.title,
      slug: row.slug,
      summary: row.summary,
      weekStart: row.week_start,
      weekEnd: row.week_end,
    }
  } catch (e) {
    console.error("getLatestReport error:", e)
    return null
  }
}
