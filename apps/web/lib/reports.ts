import { query } from "@/lib/db"
import type { ReportDetail } from "@/types/stats"

export async function getAllReportSlugs(): Promise<string[]> {
  try {
    const result = await query(`SELECT slug FROM weekly_reports ORDER BY week_start DESC`)
    return result.rows.map((r: { slug: string }) => r.slug)
  } catch (e) {
    console.error("getAllReportSlugs error:", e)
    return []
  }
}

export async function getReportBySlug(slug: string): Promise<ReportDetail | null> {
  try {
    const result = await query(`
      SELECT title, slug, summary, week_start::text AS week_start, week_end::text AS week_end, content_markdown
      FROM weekly_reports
      WHERE slug = $1
    `, [slug])
    const row = result.rows[0]
    if (!row) return null
    return {
      title: row.title,
      slug: row.slug,
      summary: row.summary,
      weekStart: row.week_start,
      weekEnd: row.week_end,
      contentMarkdown: row.content_markdown,
    }
  } catch (e) {
    console.error("getReportBySlug error:", e)
    return null
  }
}
