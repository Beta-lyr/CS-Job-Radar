import Link from "next/link"

export default function MethodologyPage() {
  return (
    <main>
      <section className="hero" style={{ padding: "42px 0 24px" }}>
        <div className="container">
          <Link href="/" style={{ display: "inline-flex", alignItems: "center", gap: 6, color: "var(--muted)", fontSize: 13, fontWeight: 750, marginBottom: 16 }}>
            ← 返回首页
          </Link>
          <p className="section-kicker" style={{ marginBottom: 12 }}>Data Methodology</p>
          <h1 style={{ margin: 0, fontSize: "clamp(36px, 5vw, 56px)", lineHeight: 1.05, letterSpacing: "-0.06em", fontWeight: 850 }}>
            数据口径与方法说明
          </h1>
          <p className="hero-lead">
            每个指标、排名、建议背后都有具体的数据来源、判断逻辑和局限性。我们优先保持透明，而不是让数据看起来比实际更可信。
          </p>
        </div>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container" style={{ display: "grid", gap: 18 }}>
          <MethodPanel
            number={1}
            title="数据来源"
            content={[
              "当前数据来自公开招聘网站的信息整理，覆盖技术研发类岗位。",
              "数据采集周期为近 7 天，每周更新一次分析结果。",
              "我们只做聚合统计，不搬运、不缓存完整的岗位详情文本。",
            ]}
          />
          <MethodPanel
            number={2}
            title="技术方向分类"
            content={[
              "方向分类基于岗位标题和职位描述中的关键词匹配，使用标题权重 5x、描述权重 3x 的评分机制。",
              "当前覆盖 Java 后端、Go 后端、前端、Android、AI 应用、测试开发、C++ / 系统开发、嵌入式、硬件、半导体、通信网络、实施 / 技术支持、技术产品等方向。",
              "部分跨方向岗位会按标题和描述关键词得分归入最匹配方向，结果用于趋势观察而非精确职业定义。",
            ]}
          />
          <MethodPanel
            number={3}
            title="城市范围"
            content={[
              "城市标准化基于城市与省份别名表，将招聘来源中的地区文本归一到可统计的城市或省级区域。",
              "当来源只提供省级地区时，保留为省级标签；无法识别的地区才归入 other。",
            ]}
          />
          <MethodPanel
            number={4}
            title="薪资处理"
            content={[
              "岗位薪资以月薪中位数（P50）为主要参考指标，辅以 P25 / P75 展示分布。",
              "薪资单位为千元（K），年薪 / 日薪 / 时薪岗位按标准换算为月薪。",
              "'未公开'、'暂无'、'面议' 岗位不纳入薪资统计。薪资区间取中值计算。",
            ]}
          />
          <MethodPanel
            number={5}
            title="应届友好判断"
            content={[
              "岗位标题或描述中包含 '校招'、'实习'、'应届'、'经验不限'、'接受应届' 等关键词时标记为应届友好。",
              "应届友好岗位占比 = 标记为应届友好的岗位数 / 总岗位数。",
              "该标记仅反映岗位描述中的明确表述，不表示实际录取偏好。",
            ]}
          />
          <MethodPanel
            number={6}
            title="机会指数"
            content={[
              "机会指数 = (该方向岗位数 / 最大方向岗位数) × 100，反映不同方向间的相对岗位规模。",
              "仅用于方向间横向对比，不反映绝对机会多少。",
              "建议结合岗位数量、应届友好度、薪资区间和自身兴趣综合判断。",
            ]}
          />
          <MethodPanel
            number={7}
            title="技能频次"
            content={[
              "技能频次 = (包含该技能的岗位数 / 最多岗位包含的技能数) × 100。",
              "技能从职位描述中通过关键词匹配提取，仅统计明确提及的技能名词。",
              "不区分 '必备' 和 '加分'，只反映企业提及频次。",
            ]}
          />
          <MethodPanel
            number={8}
            title="局限性说明"
            content={[
              "样本量有限，统计结果受采集周期和来源网站覆盖范围影响。",
              "方向分类为关键词规则匹配，非 NLP 语义理解，可能存在误分类。",
              "数据不构成就业建议，仅供学习规划参考。",
              "我们优先展示聚合统计，不搬运岗位详情，尊重数据来源。",
            ]}
          />
        </div>
      </section>
    </main>
  )
}

function MethodPanel({ number, title, content }: { number: number; title: string; content: string[] }) {
  return (
    <div className="panel">
      <div className="panel-inner" style={{ display: "grid", gridTemplateColumns: "42px 1fr", gap: 16, alignItems: "start" }}>
        <div className="flow-num" style={{ width: 42, height: 42, fontSize: 16 }}>{number}</div>
        <div>
          <h3 style={{ margin: "0 0 12px", fontSize: 18, letterSpacing: "-0.035em" }}>{title}</h3>
          <div style={{ display: "grid", gap: 8 }}>
            {content.map((line, i) => (
              <p key={i} style={{ margin: 0, color: "var(--ink-2)", fontSize: 14, lineHeight: 1.85, paddingLeft: 16, borderLeft: "2px solid var(--line-2)" }}>
                {line}
              </p>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
