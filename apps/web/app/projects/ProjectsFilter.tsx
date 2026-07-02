"use client"

import { useState } from "react"
import type { ProjectPreset } from "@/lib/projects"
import { DIRECTION_LABELS } from "@/lib/format"

interface Props {
  allProjects: ProjectPreset[]
  allDirections: string[]
}

const difficultyOrder: Record<string, number> = { "入门": 0, "进阶": 1, "挑战": 2 }

export function ProjectsFilter({ allProjects, allDirections }: Props) {
  const [selectedDirection, setSelectedDirection] = useState("")

  const filteredProjects = selectedDirection
    ? allProjects.filter((p) => p.directions.includes(selectedDirection))
    : allProjects

  return (
    <>
      <section className="section" style={{ paddingTop: 0, paddingBottom: 0 }}>
        <div className="container">
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 32 }}>
            <button
              onClick={() => setSelectedDirection("")}
              className={!selectedDirection ? "button-primary" : "button-secondary"}
              style={{ fontSize: 13, padding: "6px 16px", cursor: "pointer" }}
            >
              全部
            </button>
            {allDirections.map((d) => (
              <button
                key={d}
                onClick={() => setSelectedDirection(d)}
                className={selectedDirection === d ? "button-primary" : "button-secondary"}
                style={{ fontSize: 13, padding: "6px 16px", cursor: "pointer" }}
              >
                {DIRECTION_LABELS[d] || d}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container">
          {filteredProjects.length > 0 ? (
            <div className="project-grid">
              {filteredProjects
                .sort((a, b) => (difficultyOrder[a.difficulty] ?? 1) - (difficultyOrder[b.difficulty] ?? 1))
                .map((p) => (
                  <article key={p.title} className="project-card">
                    <div className="project-label">
                      {p.directions.map((d) => DIRECTION_LABELS[d] || d).join(" / ")}
                    </div>
                    <h3>{p.title}</h3>
                    <p>{p.description}</p>
                    <div style={{ display: "flex", gap: 8, marginBottom: 10, flexWrap: "wrap" }}>
                      <span style={{
                        fontSize: 11,
                        fontWeight: 700,
                        padding: "2px 8px",
                        borderRadius: 6,
                        background: p.difficulty === "入门" ? "var(--green-soft)" : p.difficulty === "进阶" ? "var(--amber-soft)" : "var(--red-soft)",
                        color: p.difficulty === "入门" ? "var(--green)" : p.difficulty === "进阶" ? "var(--amber)" : "var(--red)",
                      }}>
                        {p.difficulty}
                      </span>
                      <span style={{
                        fontSize: 11,
                        fontWeight: 700,
                        padding: "2px 8px",
                        borderRadius: 6,
                        background: p.resume_value === "高" ? "var(--blue-soft)" : "var(--muted-light)",
                        color: p.resume_value === "高" ? "var(--blue)" : "var(--muted)",
                      }}>
                        简历价值 {p.resume_value}
                      </span>
                    </div>
                    <div className="tags">
                      {p.tags.map((t) => <span key={t}>{t}</span>)}
                    </div>
                  </article>
                ))}
            </div>
          ) : (
            <div className="article-card" style={{ padding: "48px 36px", textAlign: "center" }}>
              <div className="article-label" style={{ marginBottom: 16 }}>暂无项目</div>
              <p style={{ color: "var(--muted)", fontSize: 15, margin: 0 }}>
                该方向暂无项目建议，我们会持续扩充项目库。
              </p>
            </div>
          )}
        </div>
      </section>
    </>
  )
}
