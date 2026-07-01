import { query } from "@/lib/db"
import type { DirectionOverview, CityStat, SkillStat } from "@/types/stats"

export async function getDirectionOverview(direction: string): Promise<DirectionOverview | null> {
  try {
    const result = await query(`
      SELECT
        direction,
        COUNT(*)::int AS job_count,
        COUNT(*) FILTER (WHERE is_fresh_graduate_friendly)::int AS friendly_count,
        COUNT(DISTINCT city)::int AS city_count,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary_median_monthly)::int AS salary_median,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY salary_median_monthly)::int AS salary_p25,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY salary_median_monthly)::int AS salary_p75
      FROM jobs
      WHERE direction = $1 AND fetched_at >= CURRENT_DATE - INTERVAL '30 days'
      GROUP BY direction
    `, [direction])
    const row = result.rows[0]
    if (!row) return null
    return {
      direction: row.direction,
      jobCount: row.job_count,
      friendlyCount: row.friendly_count,
      cityCount: row.city_count,
      salaryMedian: row.salary_median,
      salaryP25: row.salary_p25,
      salaryP75: row.salary_p75,
    }
  } catch (e) {
    console.error("getDirectionOverview error:", e)
    return null
  }
}

export async function getDirectionCities(direction: string): Promise<CityStat[]> {
  try {
    const result = await query(`
      SELECT city, COUNT(*)::int AS job_count
      FROM jobs
      WHERE direction = $1 AND fetched_at >= CURRENT_DATE - INTERVAL '30 days'
      GROUP BY city
      ORDER BY COUNT(*) DESC
    `, [direction])
    return result.rows.map((r: { city: string; job_count: number }) => ({
      city: r.city,
      jobCount: r.job_count,
    }))
  } catch (e) {
    console.error("getDirectionCities error:", e)
    return []
  }
}

export async function getDirectionSkills(direction: string): Promise<SkillStat[]> {
  try {
    const result = await query(`
      SELECT
        js.skill_name,
        COUNT(DISTINCT js.job_id)::int AS job_count
      FROM job_skills js
      JOIN jobs j ON js.job_id = j.id
      WHERE j.direction = $1 AND j.fetched_at >= CURRENT_DATE - INTERVAL '30 days'
      GROUP BY js.skill_name
      ORDER BY COUNT(DISTINCT js.job_id) DESC
      LIMIT 10
    `, [direction])
    const maxCount = result.rows.length > 0 ? Math.max(...result.rows.map((r: { job_count: number }) => r.job_count)) : 1
    return result.rows.map((r: { skill_name: string; job_count: number }) => ({
      skillName: r.skill_name,
      jobCount: r.job_count,
      percentage: Math.round((r.job_count / maxCount) * 100),
    }))
  } catch (e) {
    console.error("getDirectionSkills error:", e)
    return []
  }
}

export async function getAllDirections(): Promise<string[]> {
  try {
    const result = await query(`
      SELECT DISTINCT direction FROM jobs WHERE direction IS NOT NULL
    `)
    return result.rows.map((r: { direction: string }) => r.direction)
  } catch (e) {
    console.error("getAllDirections error:", e)
    return []
  }
}
