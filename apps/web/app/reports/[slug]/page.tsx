import Link from "next/link"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { getAllReportSlugs, getReportBySlug } from "@/lib/reports"
import { formatWeekRange } from "@/lib/format"

export const dynamicParams = false

export async function generateStaticParams() {
  const slugs = await getAllReportSlugs()
  if (slugs.length > 0) return slugs.map((s) => ({ slug: s }))
  return [{ slug: "_placeholder" }]
}

export default async function ReportDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const report = await getReportBySlug(slug)

  if (!report) {
    return (
      <main>
        <section className="hero" style={{ padding: "42px 0 24px" }}>
          <div className="container">
            <Link href="/reports" className="text-link">
              返回历史周报
            </Link>
            <h1 style={{ margin: 0, fontSize: "clamp(28px, 4vw, 42px)", lineHeight: 1.1, fontWeight: 850 }}>
              报告未找到
            </h1>
            <p style={{ margin: "12px 0 0", color: "var(--muted)", fontSize: 14 }}>
              该报告可能尚未生成或已经被移除。
            </p>
            <div style={{ marginTop: 24 }}>
              <Link className="button-primary" href="/reports">查看所有报告</Link>
            </div>
          </div>
        </section>
      </main>
    )
  }

  const markdown = report.contentMarkdown || report.summary || "暂无详细内容。"

  return (
    <main>
      <section className="hero" style={{ padding: "42px 0 24px" }}>
        <div className="container">
          <Link href="/reports" className="text-link">
            返回历史周报
          </Link>
          <div className="report-badge" style={{ marginBottom: 14, display: "inline-flex" }}>WEEKLY REPORT</div>
          <h1 style={{ margin: 0, fontSize: "clamp(28px, 4vw, 42px)", lineHeight: 1.1, fontWeight: 850, maxWidth: 800 }}>
            {report.title}
          </h1>
          <p style={{ margin: "10px 0 0", color: "var(--muted)", fontSize: 14, fontWeight: 700 }}>
            {formatWeekRange(report.weekStart, report.weekEnd)}
          </p>
        </div>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container">
          <article className="article-card report-article">
            <div className="report-markdown">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  table: ({ children }) => (
                    <div className="report-table-wrap">
                      <table>{children}</table>
                    </div>
                  ),
                }}
              >
                {markdown}
              </ReactMarkdown>
            </div>
          </article>

          <div style={{ marginTop: 24, display: "flex", gap: 10, flexWrap: "wrap" }}>
            <Link className="button-primary" href="/">返回首页</Link>
            <Link className="button-secondary" href="/reports">查看历史报告</Link>
          </div>
        </div>
      </section>
    </main>
  )
}
