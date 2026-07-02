import Link from "next/link"
import { getHomeOverview, getDirectionStats, getTopSkills, getLatestReport } from "@/lib/stats"
import { getDirectionLabel, getDirectionSkills, getChangeLabel, formatSalary, formatNumber } from "@/lib/format"

export default async function HomePage() {
  const [overview, directions, skills, report] = await Promise.all([
    getHomeOverview(),
    getDirectionStats(),
    getTopSkills(),
    getLatestReport(),
  ])

  const today = new Date()
  const weekNumber = Math.ceil(((today.getTime() - new Date(today.getFullYear(), 0, 1).getTime()) / 86400000 + today.getDay() + 1) / 7)

  return (
    <main>
      {/* Hero */}
      <section className="hero">
        <div className="container hero-grid">
          <div>
            <div className="overline">就业数据观察 · {today.getFullYear()} 第 {weekNumber} 周</div>
            <h1>
              用招聘数据，判断计算机学生<em>该往哪里准备</em>。
            </h1>
            <p className="hero-lead">
              我们把公开岗位样本整理成可读的方向观察：岗位热度、应届友好度、薪资区间、高频技能与项目建议。它不是招聘搜索，也不是制造焦虑，而是帮助学生做更清醒的学习规划。
            </p>

            <div className="hero-actions">
              <a className="button-primary" href="#directions">查看方向排行</a>
              <a className="button-secondary" href="/data-methodology">了解数据口径</a>
            </div>

            <div className="trust-list">
              <span className="trust-item"><i className="trust-dot">✓</i> 聚合分析，不搬运岗位详情</span>
              <span className="trust-item"><i className="trust-dot">✓</i> 面向实习、校招、应届生</span>
              <span className="trust-item"><i className="trust-dot">✓</i> 每周更新趋势报告</span>
            </div>
          </div>

          <aside className="report-preview" aria-label="本周报告预览">
            <div className="report-preview-head">
              <div className="report-preview-title">
                <strong>本周方向观察摘要</strong>
                <span>样本口径：近 7 天公开岗位信息</span>
              </div>
              <span className="report-badge">已更新</span>
            </div>

            <div className="report-preview-body">
              <div className="index-score">
                <div className="score-circle">
                  <strong>{overview.directionCount > 0 ? Math.min(overview.totalJobs, 99) : "—"}</strong>
                </div>
                <div className="score-copy">
                  <h2>技术岗位机会指数</h2>
                  <p>
                    指数综合岗位样本量、应届友好度、薪资分布和技能集中度，仅用于趋势参考。
                  </p>
                </div>
              </div>

              <table className="preview-table">
                <thead>
                  <tr>
                    <th>排名</th>
                    <th>方向</th>
                    <th>变化</th>
                    <th>中位薪资</th>
                  </tr>
                </thead>
                <tbody>
                  {directions.length > 0 ? (
                    directions.slice(0, 3).map((d, i) => {
                      const change = getChangeLabel(d.jobCount, d.friendlyCount, d.salaryMedian)
                      return (
                        <tr key={d.direction}>
                          <td><span className="rank-pill">{i + 1}</span></td>
                          <td><span className="direction-name">{getDirectionLabel(d.direction)}</span></td>
                          <td><span className={`change-${change.type}`}>{change.label}</span></td>
                          <td>{formatSalary(d.salaryMedian)}</td>
                        </tr>
                      )
                    })
                  ) : (
                    <tr>
                      <td colSpan={4} style={{ color: "var(--muted)", textAlign: "center", padding: "20px 0" }}>暂无岗位数据</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </aside>
        </div>
      </section>

      {/* Stats strip */}
      <section className="stats-strip">
        <div className="container stats-grid">
          <div className="stat-card">
            <span>本周有效岗位样本</span>
            <strong>{formatNumber(overview.totalJobs)}</strong>
            <p>已去除重复、无效和低置信岗位。</p>
          </div>

          <div className="stat-card">
            <span>覆盖技术方向</span>
            <strong>{overview.directionCount}</strong>
            <p>Java、Go、前端、Android、AI 应用、测试开发。</p>
          </div>

          <div className="stat-card">
            <span>覆盖核心城市</span>
            <strong>{overview.cityCount}</strong>
            <p>北京、上海、深圳、杭州、广州。</p>
          </div>

          <div className="stat-card">
            <span>应届友好岗位占比</span>
            <strong>{overview.friendlyRatio}%</strong>
            <p>含校招、实习、经验不限、接受应届等样本。</p>
          </div>
        </div>
      </section>

      {/* Direction analysis */}
      <section id="directions" className="section">
        <div className="container">
          <div className="section-head">
            <div>
              <p className="section-kicker">Direction Analysis</p>
              <h2 className="section-title">技术方向观察</h2>
              <p className="section-desc">
                这里不把「岗位多」直接等同于「值得学」，而是结合岗位数量、应届友好度、技能门槛和薪资区间综合判断。
              </p>
            </div>
            <a className="section-link" href="#">查看完整方向库 →</a>
          </div>

          <div className="analysis-grid">
            <div className="panel">
              <div className="panel-inner">
                <div className="panel-head">
                  <div>
                    <h3>本周方向排行</h3>
                    <p className="panel-subtitle">基于近 7 天公开岗位样本统计</p>
                  </div>
                  <span className="small-note">更新时间：{today.toISOString().slice(0, 10)}</span>
                </div>

                <div className="direction-list">
                  {directions.length > 0 ? (
                    directions.map((d, i) => {
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
                    })
                  ) : (
                    <div className="panel-subtitle" style={{ textAlign: "center", padding: "40px 0" }}>暂无方向数据</div>
                  )}
                </div>
              </div>
            </div>

            <aside id="skills" className="panel">
              <div className="panel-inner">
                <div className="panel-head">
                  <div>
                    <h3>岗位高频技能</h3>
                    <p className="panel-subtitle">按 JD 出现频次和方向相关性排序</p>
                  </div>
                </div>

                <div className="skill-list">
                  {skills.length > 0 ? (
                    skills.map((s) => (
                      <div key={s.skillName} className="skill-item">
                        <span className="skill-name">{s.skillName}</span>
                        <div className="bar-track"><span className="bar-fill" style={{ width: `${s.percentage}%` }}></span></div>
                        <span className="skill-count">{s.percentage}</span>
                      </div>
                    ))
                  ) : (
                    <div className="panel-subtitle" style={{ textAlign: "center", padding: "40px 0" }}>暂无技能数据</div>
                  )}
                </div>

                <div className="insight-box">
                  <h4>设计重点</h4>
                  <p>
                    高频技能不要做成花哨词云。学生真正需要的是排序、类别、出现率、必备/加分判断，以及对应的学习建议。
                  </p>
                </div>
              </div>
            </aside>
          </div>
        </div>
      </section>

      {/* Weekly report */}
      <section id="reports" className="report-section">
        <div className="container">
          <div className="report-grid">
            <article className="article-card">
              <div className="article-label">WEEKLY REPORT</div>
              <h2>{report ? report.title : "本周结论：Java 仍然稳，AI 应用升温，但项目门槛更高。"}</h2>
              <p>
                {report
                  ? report.summary
                  : "本周公开岗位样本显示，Java 后端仍然是最稳定的应届技术方向之一；AI 应用开发岗位增长明显，但企业更看重完整项目经验，包括数据处理、检索增强、接口封装、部署和业务闭环。"}
              </p>

              <div className="editorial-quote">
                对学生来说，不应只追热点，而要判断自己是否能在 8 到 12 周内做出能讲清楚、能部署、能被追问的项目。
              </div>

              <div className="article-actions">
                <Link className="button-primary" href={report ? `/reports/${report.slug}` : "#"}>阅读完整周报</Link>
                <a className="button-secondary" href="#">查看历史报告</a>
              </div>
            </article>

            <div className="flow-list">
              <div className="flow-item">
                <div className="flow-num">1</div>
                <div>
                  <h3>先看方向，不先看课程</h3>
                  <p>先判断市场中不同技术方向的需求，再决定自己的学习路径，而不是被单一课程路线牵着走。</p>
                </div>
              </div>

              <div className="flow-item">
                <div className="flow-num">2</div>
                <div>
                  <h3>区分必备技能和加分技能</h3>
                  <p>JD 里会出现大量技术名词，但学生需要知道哪些是入门门槛，哪些只是加分项。</p>
                </div>
              </div>

              <div className="flow-item">
                <div className="flow-num">3</div>
                <div>
                  <h3>把趋势转成项目</h3>
                  <p>最终要落到可写进简历的项目，而不是停留在「我知道这个方向很热」。</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Project suggestions */}
      <section id="projects" className="section">
        <div className="container">
          <div className="section-head">
            <div>
              <p className="section-kicker">Project Planning</p>
              <h2 className="section-title">从岗位要求反推项目选题</h2>
              <p className="section-desc">
                这个模块不做「项目大全」，而是基于近期岗位要求，给出更适合学生简历表达和面试讲解的项目方向。
              </p>
            </div>
            <a className="section-link" href="#">查看项目库 →</a>
          </div>

          <div className="project-grid">
            <article className="project-card">
              <div className="project-label">AI 应用方向</div>
              <h3>岗位匹配与简历分析系统</h3>
              <p>适合展示 RAG、文档解析、岗位匹配、报告生成和服务部署能力。</p>
              <div className="tags">
                <span>Next.js</span>
                <span>Python</span>
                <span>RAG</span>
                <span>PostgreSQL</span>
              </div>
            </article>

            <article className="project-card">
              <div className="project-label">Java 后端方向</div>
              <h3>在线判题系统简化版</h3>
              <p>适合覆盖任务队列、Docker 沙箱、判题调度、权限和日志。</p>
              <div className="tags">
                <span>Spring Boot</span>
                <span>Redis</span>
                <span>Docker</span>
                <span>MySQL</span>
              </div>
            </article>

            <article className="project-card">
              <div className="project-label">前后端综合</div>
              <h3>校园二手交易平台</h3>
              <p>适合展示完整业务链路，包括发布、搜索、订单、后台和部署。</p>
              <div className="tags">
                <span>React</span>
                <span>API</span>
                <span>权限</span>
                <span>部署</span>
              </div>
            </article>
          </div>
        </div>
      </section>

      {/* Data methodology */}
      <section id="method" className="method">
        <div className="container">
          <div className="method-card">
            <div>
              <p className="section-kicker">Data Methodology</p>
              <h2>专业感来自克制，也来自数据口径透明。</h2>
              <p>
                这版设计去掉了过度 AI 化的符号：不使用霓虹光效、终端扫描、玻璃拟态和夸张渐变。视觉重心放在报告感、数据表格、明确层级和可信表达上。
              </p>
            </div>

            <div className="method-list">
              <div className="method-item"><span>1</span> 优先展示聚合统计，不复制岗位详情</div>
              <div className="method-item"><span>2</span> 每个指标都能解释口径和样本范围</div>
              <div className="method-item"><span>3</span> 用表格、条形图、摘要卡片承载信息</div>
              <div className="method-item"><span>4</span> 文案避免「逆袭」「保 offer」「AI 预测未来」等营销表达</div>
              <div className="method-item"><span>5</span> 让学生读完后知道该学什么、做什么项目</div>
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}
