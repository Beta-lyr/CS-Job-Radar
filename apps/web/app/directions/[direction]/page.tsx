import Link from "next/link"
import { getDirectionOverview, getDirectionCities, getDirectionSkills, getAllDirections } from "@/lib/directions"
import { getDirectionLabel, getDirectionSkills as getMetaSkills, getDirectionProjects, formatSalary, formatNumber } from "@/lib/format"
import { notFound } from "next/navigation"

export async function generateStaticParams() {
  const directions = await getAllDirections()
  return directions.map((d) => ({ direction: d }))
}

export default async function DirectionDetailPage({
  params,
}: {
  params: Promise<{ direction: string }>
}) {
  const { direction } = await params
  const [overview, cities, skills] = await Promise.all([
    getDirectionOverview(direction),
    getDirectionCities(direction),
    getDirectionSkills(direction),
  ])

  if (!overview) notFound()

  const label = getDirectionLabel(direction)
  const metaSkills = getMetaSkills(direction)
  const projects = getDirectionProjects(direction)
  const friendlyRatio = overview.jobCount > 0
    ? Math.round((overview.friendlyCount / overview.jobCount) * 100)
    : 0

  return (
    <main>
      {/* Header */}
      <section className="hero" style={{ padding: "42px 0 24px" }}>
        <div className="container">
          <Link href="/" style={{ display: "inline-flex", alignItems: "center", gap: 6, color: "var(--muted)", fontSize: 13, fontWeight: 750, marginBottom: 16 }}>
            ← 返回首页
          </Link>
          <h1 style={{ margin: 0, fontSize: "clamp(32px, 4vw, 48px)", lineHeight: 1.08, letterSpacing: "-0.055em", fontWeight: 850 }}>
            {label}
          </h1>
          <p style={{ margin: "12px 0 0", color: "var(--ink-2)", fontSize: 16, lineHeight: 1.8, maxWidth: 600 }}>
            {metaSkills}
          </p>
        </div>
      </section>

      {/* Stats */}
      <section className="stats-strip" style={{ paddingTop: 0 }}>
        <div className="container stats-grid">
          <div className="stat-card">
            <span>本周岗位样本</span>
            <strong>{formatNumber(overview.jobCount)}</strong>
            <p>近 7 天公开岗位数量。</p>
          </div>
          <div className="stat-card">
            <span>应届友好占比</span>
            <strong>{friendlyRatio}%</strong>
            <p>含校招、实习、经验不限。</p>
          </div>
          <div className="stat-card">
            <span>中位薪资</span>
            <strong>{formatSalary(overview.salaryMedian)}</strong>
            <p>{overview.salaryP25 ? `P25: ${formatSalary(overview.salaryP25)}` : ""}{overview.salaryP75 ? ` / P75: ${formatSalary(overview.salaryP75)}` : ""}</p>
          </div>
          <div className="stat-card">
            <span>覆盖城市</span>
            <strong>{overview.cityCount}</strong>
            <p>该方向有岗位数据的城市。</p>
          </div>
        </div>
      </section>

      <div className="container analysis-grid" style={{ paddingBottom: 44 }}>
        {/* City distribution */}
        <div className="panel">
          <div className="panel-inner">
            <div className="panel-head">
              <div>
                <h3>城市分布</h3>
                <p className="panel-subtitle">各城市岗位数量分布</p>
              </div>
            </div>
            {cities.length > 0 ? (
              <div className="direction-list">
                {cities.map((c, i) => (
                  <Link key={c.city} href={`/cities/${encodeURIComponent(c.city)}`} className="direction-row" style={{ gridTemplateColumns: "42px minmax(0, 1fr) 84px" }}>
                    <div className={`direction-index${i < 3 ? " top" : ""}`}>{i + 1}</div>
                    <div>
                      <div className="direction-main">{c.city}</div>
                    </div>
                    <div className="salary" style={{ textAlign: "right" }}>{c.jobCount}<small>个岗位</small></div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="panel-subtitle" style={{ textAlign: "center", padding: "40px 0" }}>暂无城市数据</div>
            )}
          </div>
        </div>

        {/* Top skills */}
        <aside className="panel">
          <div className="panel-inner">
            <div className="panel-head">
              <div>
                <h3>高频技能要求</h3>
                <p className="panel-subtitle">按 JD 中出现频次排序</p>
              </div>
            </div>
            {skills.length > 0 ? (
              <div className="skill-list">
                {skills.map((s) => (
                  <div key={s.skillName} className="skill-item">
                    <span className="skill-name">{s.skillName}</span>
                    <div className="bar-track"><span className="bar-fill" style={{ width: `${s.percentage}%` }}></span></div>
                    <span className="skill-count">{s.percentage}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="panel-subtitle" style={{ textAlign: "center", padding: "40px 0" }}>暂无技能数据</div>
            )}
          </div>
        </aside>
      </div>

      {/* Project suggestions */}
      {projects.length > 0 && (
        <section className="section" style={{ paddingTop: 0 }}>
          <div className="container">
            <div className="section-head">
              <div>
                <p className="section-kicker">Project Planning</p>
                <h2 className="section-title" style={{ fontSize: 28 }}>推荐项目方向</h2>
                <p className="section-desc">基于该方向岗位要求反推的项目选题，适合简历表达和面试讲解。</p>
              </div>
            </div>
            <div className="project-grid">
              {projects.map((p) => (
                <article key={p.title} className="project-card">
                  <div className="project-label">{p.label}</div>
                  <h3>{p.title}</h3>
                  <p>{p.description}</p>
                  <div className="tags">
                    {p.tags.map((t) => <span key={t}>{t}</span>)}
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>
      )}
    </main>
  )
}
