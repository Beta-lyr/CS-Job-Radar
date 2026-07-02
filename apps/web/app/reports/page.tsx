import Link from "next/link"
import { getAllReports } from "@/lib/reports"
import { formatWeekRange } from "@/lib/format"

export default async function ReportsPage() {
  const reports = await getAllReports()

  return (
    <main>
      <section className="hero" style={{ padding: "42px 0 24px" }}>
        <div className="container">
          <Link href="/" style={{ display: "inline-flex", alignItems: "center", gap: 6, color: "var(--muted)", fontSize: 13, fontWeight: 750, marginBottom: 16 }}>
            ← 返回首页
          </Link>
          <h1 style={{ margin: 0, fontSize: "clamp(32px, 4vw, 48px)", lineHeight: 1.08, letterSpacing: "-0.055em", fontWeight: 850 }}>
            历史周报
          </h1>
          <p style={{ margin: "12px 0 0", color: "var(--ink-2)", fontSize: 16, lineHeight: 1.8, maxWidth: 600 }}>
            CS Job Radar 每周自动生成的岗位趋势报告存档。
          </p>
        </div>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container">
          {reports.length > 0 ? (
            <div className="direction-list" style={{ display: "block" }}>
              {reports.map((r) => (
                <Link
                  key={r.slug}
                  href={`/reports/${r.slug}`}
                  className="direction-row"
                  style={{ gridTemplateColumns: "minmax(0, 1fr) auto", padding: "20px 24px" }}
                >
                  <div>
                    <div className="direction-main" style={{ fontSize: 16, fontWeight: 750 }}>
                      {r.title}
                    </div>
                    <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 4, fontWeight: 600 }}>
                      {formatWeekRange(r.weekStart, r.weekEnd)}
                    </div>
                    {r.summary && (
                      <div style={{ fontSize: 14, color: "var(--ink-2)", marginTop: 6, lineHeight: 1.6 }}>
                        {r.summary}
                      </div>
                    )}
                  </div>
                  <span style={{ color: "var(--blue)", fontSize: 13, fontWeight: 750, whiteSpace: "nowrap" }}>
                    阅读 →
                  </span>
                </Link>
              ))}
            </div>
          ) : (
            <div className="article-card" style={{ padding: "48px 36px", textAlign: "center" }}>
              <div className="article-label" style={{ marginBottom: 16 }}>暂无内容</div>
              <p style={{ color: "var(--muted)", fontSize: 15, margin: 0 }}>
                还没有生成周报。周报会在每周一自动生成，也可以在 GitHub Actions 中手动触发。
              </p>
            </div>
          )}
        </div>
      </section>
    </main>
  )
}
