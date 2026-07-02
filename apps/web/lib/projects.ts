import projectPresets from "../../../data/project-presets/cs_projects.json"

export interface ProjectPreset {
  directions: string[]
  required_skills: string[]
  title: string
  description: string
  tags: string[]
  difficulty: string
  resume_value: string
}

const projects: ProjectPreset[] = projectPresets

export function getAllProjects(): ProjectPreset[] {
  return projects
}

export function getProjectsByDirection(direction: string): ProjectPreset[] {
  return projects.filter((p) => p.directions.includes(direction))
}

export function getFeaturedProjects(
  hotDirections: string[],
  topSkills: string[],
  limit: number = 3
): ProjectPreset[] {
  const scored = projects.map((p) => {
    let score = 0
    for (const d of p.directions) {
      if (hotDirections.includes(d)) score += 2
    }
    for (const s of p.required_skills) {
      if (topSkills.some((ts) => ts.toLowerCase() === s.toLowerCase())) score += 1
    }
    const distinctCount = new Set(p.directions.filter((d) => hotDirections.includes(d))).size
    if (distinctCount >= 1) score += 1
    return { project: p, score }
  })

  scored.sort((a, b) => b.score - a.score)

  return scored.slice(0, limit).map((s) => s.project)
}

export function getAllDirections(): string[] {
  const set = new Set<string>()
  for (const p of projects) {
    for (const d of p.directions) {
      set.add(d)
    }
  }
  return Array.from(set)
}
