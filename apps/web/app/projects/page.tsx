import Link from "next/link"
import { getAllProjects, getAllDirections } from "@/lib/projects"
import { ProjectsFilter } from "./ProjectsFilter"

export default function ProjectsPage() {
  const allProjects = getAllProjects()
  const allDirections = getAllDirections()

  return (
    <main>
      <section className="hero" style={{ padding: "42px 0 24px" }}>
        <div className="container">
          <Link href="/" style={{ display: "inline-flex", alignItems: "center", gap: 6, color: "var(--muted)", fontSize: 13, fontWeight: 750, marginBottom: 16 }}>
            ← 返回首页
          </Link>
          <h1 style={{ margin: 0, fontSize: "clamp(32px, 4vw, 48px)", lineHeight: 1.08, letterSpacing: "-0.055em", fontWeight: 850 }}>
            项目选题库
          </h1>
          <p style={{ margin: "12px 0 0", color: "var(--ink-2)", fontSize: 16, lineHeight: 1.8, maxWidth: 600 }}>
            基于岗位要求反推的项目选题，按技术方向分类。每个项目都标注了建议难度和简历价值。
          </p>
        </div>
      </section>

      <ProjectsFilter
        allProjects={JSON.parse(JSON.stringify(allProjects))}
        allDirections={JSON.parse(JSON.stringify(allDirections))}
      />
    </main>
  )
}
