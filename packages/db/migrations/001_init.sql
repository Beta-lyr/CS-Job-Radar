-- 001_init.sql
-- CS Job Radar 数据库初始化脚本

-- 数据源表
CREATE TABLE IF NOT EXISTS sources (
  id BIGSERIAL PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  source_type TEXT NOT NULL,
  base_url TEXT,
  list_url TEXT NOT NULL,
  city TEXT,
  industry TEXT,
  parser_type TEXT NOT NULL DEFAULT 'generic',
  fetcher_type TEXT NOT NULL DEFAULT 'static',
  risk_level TEXT NOT NULL DEFAULT 'low',
  enabled BOOLEAN NOT NULL DEFAULT true,
  crawl_interval_hours INT NOT NULL DEFAULT 24,
  last_crawled_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- 采集日志表
CREATE TABLE IF NOT EXISTS crawl_logs (
  id BIGSERIAL PRIMARY KEY,
  source_id BIGINT REFERENCES sources(id),
  status TEXT NOT NULL,
  started_at TIMESTAMP NOT NULL DEFAULT now(),
  finished_at TIMESTAMP,
  fetched_count INT DEFAULT 0,
  inserted_count INT DEFAULT 0,
  skipped_count INT DEFAULT 0,
  error_message TEXT
);

-- 原始岗位表
CREATE TABLE IF NOT EXISTS raw_jobs (
  id BIGSERIAL PRIMARY KEY,
  source_id BIGINT REFERENCES sources(id),
  source_url TEXT NOT NULL,
  source_url_hash TEXT NOT NULL UNIQUE,
  raw_title TEXT,
  raw_company TEXT,
  raw_city TEXT,
  raw_salary TEXT,
  raw_education TEXT,
  raw_experience TEXT,
  raw_description TEXT,
  publish_date TIMESTAMP,
  fetched_at TIMESTAMP NOT NULL DEFAULT now(),
  raw_hash TEXT,
  parse_status TEXT NOT NULL DEFAULT 'pending',
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_raw_jobs_source_id ON raw_jobs(source_id);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_fetched_at ON raw_jobs(fetched_at);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_publish_date ON raw_jobs(publish_date);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_parse_status ON raw_jobs(parse_status);

-- 标准化岗位表
CREATE TABLE IF NOT EXISTS jobs (
  id BIGSERIAL PRIMARY KEY,
  raw_job_id BIGINT UNIQUE REFERENCES raw_jobs(id),
  title TEXT,
  company_name TEXT,
  city TEXT,
  district TEXT,
  salary_text TEXT,
  salary_min_monthly INT,
  salary_max_monthly INT,
  salary_median_monthly INT,
  salary_months INT,
  salary_type TEXT,
  education_text TEXT,
  education_level TEXT,
  experience_text TEXT,
  experience_level TEXT,
  direction TEXT,
  sub_direction TEXT,
  is_internship BOOLEAN NOT NULL DEFAULT false,
  is_campus BOOLEAN NOT NULL DEFAULT false,
  is_fresh_graduate_friendly BOOLEAN NOT NULL DEFAULT false,
  fresh_graduate_score NUMERIC(5,2),
  description_clean TEXT,
  confidence_score NUMERIC(5,2),
  publish_date TIMESTAMP,
  fetched_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jobs_direction ON jobs(direction);
CREATE INDEX IF NOT EXISTS idx_jobs_city ON jobs(city);
CREATE INDEX IF NOT EXISTS idx_jobs_publish_date ON jobs(publish_date);
CREATE INDEX IF NOT EXISTS idx_jobs_fetched_at ON jobs(fetched_at);
CREATE INDEX IF NOT EXISTS idx_jobs_salary_median ON jobs(salary_median_monthly);
CREATE INDEX IF NOT EXISTS idx_jobs_fresh_friendly ON jobs(is_fresh_graduate_friendly);
CREATE INDEX IF NOT EXISTS idx_jobs_direction_city ON jobs(direction, city);

-- 岗位技能表
CREATE TABLE IF NOT EXISTS job_skills (
  id BIGSERIAL PRIMARY KEY,
  job_id BIGINT REFERENCES jobs(id) ON DELETE CASCADE,
  skill_name TEXT NOT NULL,
  skill_category TEXT,
  is_required BOOLEAN,
  is_bonus BOOLEAN,
  confidence NUMERIC(5,2),
  created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_job_skills_job_id ON job_skills(job_id);
CREATE INDEX IF NOT EXISTS idx_job_skills_skill_name ON job_skills(skill_name);
CREATE INDEX IF NOT EXISTS idx_job_skills_category ON job_skills(skill_category);

-- 每日方向统计表
CREATE TABLE IF NOT EXISTS daily_direction_stats (
  id BIGSERIAL PRIMARY KEY,
  stat_date DATE NOT NULL,
  direction TEXT NOT NULL,
  city TEXT,
  job_count INT NOT NULL DEFAULT 0,
  fresh_graduate_job_count INT NOT NULL DEFAULT 0,
  internship_job_count INT NOT NULL DEFAULT 0,
  salary_median INT,
  salary_p25 INT,
  salary_p75 INT,
  top_skills JSONB,
  top_companies JSONB,
  source_count INT DEFAULT 0,
  sample_confidence NUMERIC(5,2),
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  UNIQUE(stat_date, direction, city)
);

-- 每周报告表
CREATE TABLE IF NOT EXISTS weekly_reports (
  id BIGSERIAL PRIMARY KEY,
  week_start DATE NOT NULL,
  week_end DATE NOT NULL,
  title TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  summary TEXT,
  content_markdown TEXT,
  report_data JSONB,
  generated_at TIMESTAMP NOT NULL DEFAULT now(),
  published_at TIMESTAMP
);

-- 数据质量问题表
CREATE TABLE IF NOT EXISTS data_quality_issues (
  id BIGSERIAL PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_id BIGINT NOT NULL,
  issue_type TEXT NOT NULL,
  issue_message TEXT,
  severity TEXT NOT NULL DEFAULT 'medium',
  resolved BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMP NOT NULL DEFAULT now()
);
