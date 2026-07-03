import Link from "next/link"
import { notFound } from "next/navigation"
import { getAllCities, getCityOverview, getCityDirections, getCitySkills } from "@/lib/cities"
import { getDirectionLabel, getDirectionSkills, getChangeLabel, formatSalary, formatNumber } from "@/lib/format"

export async function generateStaticParams() {
  const cities = await getAllCities()
  const params = new Set<string>()
  for (const city of cities) {
    params.add(city)
    params.add(encodeURIComponent(city))
  }
  return Array.from(params).map((city) => ({ city }))
}

export default async function CityPage({
  params,
}: {
  params: Promise<{ city: string }>
}) {
  const raw = (await params).city
  const city = decodeURIComponent(raw)
  const [overview, directions, skills] = await Promise.all([
    getCityOverview(city),
    getCityDirections(city),
    getCitySkills(city),
  ])

  if (!overview) notFound()

  const friendlyRatio = overview.jobCount > 0
    ? Math.round((overview.friendlyCount / overview.jobCount) * 100)
    : 0

  return (
    <main>
      <section className="hero" style={{ padding: "42px 0 24px" }}>
        <div className="container">
          <Link href="/" style={{ display: "inline-flex", alignItems: "center", gap: 6, color: "var(--muted)", fontSize: 13, fontWeight: 750, marginBottom: 16 }}>
            ← 返回首页
          </Link>
          <h1 style={{ margin: 0, fontSize: "clamp(32px, 4vw, 48px)", lineHeight: 1.08, letterSpacing: "-0.055em", fontWeight: 850 }}>
            {city}
          </h1>
          <p style={{ margin: "12px 0 0", color: "var(--ink-2)", fontSize: 16, lineHeight: 1.8, maxWidth: 600 }}>
            {overview.directionCount} 个技术方向，{formatNumber(overview.jobCount)} 个岗位样本
          </p>
        </div>
      </section>

      <section className="stats-strip" style={{ paddingTop: 0 }}>
        <div className="container stats-grid">
          <div className="stat-card">
            <span>本周岗位样本</span>
            <strong>{formatNumber(overview.jobCount)}</strong>
            <p>近 7 天公开岗位数量。</p>
          </div>
          <div className="stat-card">
            <span>覆盖技术方向</span>
            <strong>{overview.directionCount}</strong>
            <p>该城市有岗位的方向数。</p>
          </div>
          <div className="stat-card">
            <span>中位薪资</span>
            <strong>{formatSalary(overview.salaryMedian)}</strong>
            <p>该城市所有岗位中位数。</p>
          </div>
          <div className="stat-card">
            <span>应届友好占比</span>
            <strong>{friendlyRatio}%</strong>
            <p>含校招、实习、经验不限。</p>
          </div>
        </div>
      </section>

      <div className="container analysis-grid" style={{ paddingBottom: 44 }}>
        <div className="panel">
          <div className="panel-inner">
            <div className="panel-head">
              <div>
                <h3>方向分布</h3>
                <p className="panel-subtitle">各技术方向在 {city} 的岗位数量</p>
              </div>
            </div>
            {directions.length > 0 ? (
              <div className="direction-list">
                {directions.map((d, i) => {
                  const change = getChangeLabel(d.jobCount, d.friendlyCount, d.salaryMedian)
                  return (
                    <Link key={d.direction} href={`/directions/${d.direction}`} className="direction-row">
                      <div className={`direction-index${i < 3 ? " top" : ""}`}>{i + 1}</div>
                      <div>
                        <div className="direction-main">
                          {getDirectionLabel(d.direction)}
                          <span className={`change-${change.type}`}>{change.label}</span>
                        </div>
                        <div className="direction-meta">{getDirectionSkills(d.direction)}</div>
                      </div>
                      <div className="bar-group">
                        <div className="bar-label"><span>机会指数</span><span>{d.opportunityIndex}</span></div>
                        <div className="bar-track"><span className="bar-fill" style={{ width: `${d.opportunityIndex}%` }}></span></div>
                      </div>
                      <div className="salary">{formatSalary(d.salaryMedian)}<small>中位数</small></div>
                    </Link>
                  )
                })}
              </div>
            ) : (
              <div className="panel-subtitle" style={{ textAlign: "center", padding: "40px 0" }}>暂无方向数据</div>
            )}
          </div>
        </div>

        <aside className="panel">
          <div className="panel-inner">
            <div className="panel-head">
              <div>
                <h3>高频技能要求</h3>
                <p className="panel-subtitle">{city} 岗位 JD 高频技能</p>
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

      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container">
          <Link className="button-secondary" href="/" style={{ display: "inline-flex" }}>← 返回首页</Link>
        </div>
      </section>
    </main>
  )
}
