import { query } from "@/lib/db"
import type { CityOverview, DirectionStat, SkillStat } from "@/types/stats"

export async function getAllCities(): Promise<string[]> {
  try {
    const result = await query(`
      SELECT DISTINCT city FROM jobs
      WHERE city IS NOT NULL AND city != ''
      ORDER BY city
    `)
    return result.rows.map((r: { city: string }) => r.city)
  } catch (e) {
    console.error("getAllCities error:", e)
    return []
  }
}

export async function getCityOverview(city: string): Promise<CityOverview | null> {
  try {
    const result = await query(`
      SELECT
        COUNT(*)::int AS job_count,
        COUNT(DISTINCT direction)::int AS direction_count,
        COUNT(*) FILTER (WHERE is_fresh_graduate_friendly)::int AS friendly_count,
        ROUND(COUNT(*) FILTER (WHERE is_fresh_graduate_friendly) * 100.0 / NULLIF(COUNT(*), 0))::int AS friendly_ratio,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary_median_monthly)::int AS salary_median
      FROM jobs
      WHERE city = $1 AND fetched_at >= CURRENT_DATE - INTERVAL '30 days'
    `, [city])
    const row = result.rows[0]
    if (!row || row.job_count === 0) return null
    return {
      city,
      jobCount: row.job_count,
      directionCount: row.direction_count,
      friendlyCount: row.friendly_count,
      friendlyRatio: row.friendly_ratio,
      salaryMedian: row.salary_median,
    }
  } catch (e) {
    console.error("getCityOverview error:", e)
    return null
  }
}

export async function getCityDirections(city: string): Promise<DirectionStat[]> {
  try {
    const result = await query(`
      SELECT
        direction,
        COUNT(*)::int AS job_count,
        COUNT(*) FILTER (WHERE is_fresh_graduate_friendly)::int AS friendly_count,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary_median_monthly)::int AS salary_median
      FROM jobs
      WHERE city = $1 AND fetched_at >= CURRENT_DATE - INTERVAL '30 days'
        AND direction IS NOT NULL
      GROUP BY direction
      ORDER BY COUNT(*) DESC
    `, [city])
    const maxJobs = Math.max(...result.rows.map((r: { job_count: number }) => r.job_count), 1)
    return result.rows.map((r: { direction: string; job_count: number; friendly_count: number; salary_median: number | null }) => ({
      direction: r.direction,
      jobCount: r.job_count,
      friendlyCount: r.friendly_count,
      salaryMedian: r.salary_median,
      topSkills: [],
      opportunityIndex: Math.round((r.job_count / maxJobs) * 100),
    }))
  } catch (e) {
    console.error("getCityDirections error:", e)
    return []
  }
}

export async function getCitySkills(city: string): Promise<SkillStat[]> {
  try {
    const result = await query(`
      SELECT
        js.skill_name,
        COUNT(DISTINCT js.job_id)::int AS job_count
      FROM job_skills js
      JOIN jobs j ON js.job_id = j.id
      WHERE j.city = $1 AND j.fetched_at >= CURRENT_DATE - INTERVAL '30 days'
      GROUP BY js.skill_name
      ORDER BY COUNT(DISTINCT js.job_id) DESC
      LIMIT 10
    `, [city])
    const maxCount = result.rows.length > 0 ? Math.max(...result.rows.map((r: { job_count: number }) => r.job_count)) : 1
    return result.rows.map((r: { skill_name: string; job_count: number }) => ({
      skillName: r.skill_name,
      jobCount: r.job_count,
      percentage: Math.round((r.job_count / maxCount) * 100),
    }))
  } catch (e) {
    console.error("getCitySkills error:", e)
    return []
  }
}
