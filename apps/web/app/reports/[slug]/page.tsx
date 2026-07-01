import Link from "next/link"
import { notFound } from "next/navigation"
import { getAllReportSlugs, getReportBySlug } from "@/lib/reports"
import { formatWeekRange } from "@/lib/format"

export async function generateStaticParams() {
  const slugs = await getAllReportSlugs()
  return slugs.map((slug) => ({ slug }))
}

export default async function ReportPage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const report = await getReportBySlug(slug)
  if (!report) notFound()

  const lines = report.contentMarkdown
    ? report.contentMarkdown.split("\n").filter(Boolean)
    : report.summary
      ? report.summary.split("。").filter(Boolean).map((s) => s + "。")
      : ["暂无详细内容。"]

  return (
    <main>
      <section className="hero" style={{ padding: "42px 0 24px" }}>
        <div className="container">
          <Link href="/" style={{ display: "inline-flex", alignItems: "center", gap: 6, color: "var(--muted)", fontSize: 13, fontWeight: 750, marginBottom: 16 }}>
            ← 返回首页
          </Link>
          <div className="report-badge" style={{ marginBottom: 14, display: "inline-flex" }}>WEEKLY REPORT</div>
          <h1 style={{ margin: 0, fontSize: "clamp(28px, 4vw, 42px)", lineHeight: 1.1, letterSpacing: "-0.055em", fontWeight: 850, maxWidth: 800 }}>
            {report.title}
          </h1>
          <p style={{ margin: "10px 0 0", color: "var(--muted)", fontSize: 14, fontWeight: 700 }}>
            {formatWeekRange(report.weekStart, report.weekEnd)}
          </p>
        </div>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container">
          <div className="article-card" style={{ padding: "32px 36px" }}>
            <div style={{ display: "grid", gap: 18 }}>
              {lines.map((line, i) => (
                <p key={i} style={{ margin: 0, color: "var(--ink-2)", fontSize: 15, lineHeight: 2 }}>
                  {line}
                </p>
              ))}
            </div>
          </div>

          <div style={{ marginTop: 24, display: "flex", gap: 10, flexWrap: "wrap" }}>
            <Link className="button-primary" href="/">返回首页</Link>
            <a className="button-secondary" href="#">查看历史报告</a>
          </div>
        </div>
      </section>
    </main>
  )
}
