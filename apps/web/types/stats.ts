export interface HomeOverview {
  totalJobs: number
  directionCount: number
  cityCount: number
  friendlyRatio: number
}

export interface DirectionStat {
  direction: string
  jobCount: number
  friendlyCount: number
  salaryMedian: number | null
  topSkills: string[]
  opportunityIndex: number
}

export interface SkillStat {
  skillName: string
  jobCount: number
  percentage: number
}

export interface WeeklyReportSummary {
  title: string
  slug: string
  summary: string
  weekStart: string
  weekEnd: string
}

export interface DirectionOverview {
  direction: string
  jobCount: number
  friendlyCount: number
  cityCount: number
  salaryMedian: number | null
  salaryP25: number | null
  salaryP75: number | null
}

export interface CityStat {
  city: string
  jobCount: number
}

export interface CityOverview {
  city: string
  jobCount: number
  directionCount: number
  friendlyRatio: number
  salaryMedian: number | null
  friendlyCount: number
}

export interface ReportDetail {
  title: string
  slug: string
  summary: string
  weekStart: string
  weekEnd: string
  contentMarkdown: string | null
}
