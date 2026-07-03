# CS Job Radar

CS 岗位采集、分析、推送一站式工具。自动抓取各大企业校招/社招岗位，标准化薪资与城市数据，按技术方向分类聚合，提供 Web 端浏览与周报推送。

## 系统架构

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  data sources│───▶│  normalize   │───▶│   stats     │
│  (crawlers) │    │  (解析/分类) │    │  (聚合统计) │
└─────────────┘    └──────────────┘    └─────────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  PostgreSQL      │
                                    │ raw_jobs → jobs  │
                                    │ → daily_direction│
                                    │ _stats          │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  Next.js Web    │
                                    │  前端展示        │
                                    └─────────────────┘
```

## 项目结构

```
apps/web/            Next.js 前端（岗位浏览、城市详情、方向统计）
scripts/
  pipeline/         采集流水线（seed → crawl → normalize → stats）
    crawl.py        执行所有启用的数据源脚本，写入 raw_jobs
    normalize.py    raw_jobs → jobs（解析薪资/城市/学历/方向/技能）
    stats.py        聚合 jobs → daily_direction_stats（含中位数、分位数）
    seed.py         初始化数据源/方向等基础数据
  sources/          数据源爬虫脚本
    tencent.py      腾讯校招
    ncss.py         国家大学生就业服务平台
    xidian.py       西安电子科技大学就业网
  db/               数据库迁移管理
  report/           周报生成与推送
services/
  crawler/          爬虫基础设施（DB 会话、HTTP/Playwright 抓取器）
  analyzer/         岗位解析、过滤、分类（城市、方向、技能提取、置信度）
  reporter/         报告模板与推送渠道
data/
  source-registry/  数据源注册表
  crawl-presets/    采集预设配置
  geo/              城市与地区编码
  direction-rules/  技术方向关键词规则
```

## 快速开始

```bash
# 安装前端依赖
npm install

# 复制环境变量
cp .env.example .env
# 编辑 .env 设置 DATABASE_URL

# 初始化数据库
python scripts/init_db.py

# 运行完整采集流水线
python scripts/run_pipeline.py

# 启动前端
npm run dev
```

## 数据流水线

流水线按 `seed → crawl → normalize → stats` 顺序执行：

| 阶段 | 说明 | 输出 |
|------|------|------|
| **seed** | 初始化数据源、技术方向等基础数据到 DB | — |
| **crawl** | 遍历启用的数据源脚本，列表抓取 + 详情抓取，写入 `raw_jobs` | 每个源统计插入/跳过数 |
| **normalize** | 解析原始数据（薪资、城市、学历、方向、技能），写入 `jobs` 和 `job_skills` | 处理的岗位总数 |
| **stats** | 按方向 × 城市聚合统计（岗位数、中位薪资、分位数、Top 技能/公司），写入 `daily_direction_stats` | 聚合的组合数 |

## 脚本输出规范

### 数据源脚本（scripts/sources/）

列表阶段逐页输出统计，详情阶段汇总：

```
  page 1: 50 positions, 27 accepted, 0 duplicate, 23 filtered
  page 2: 50 positions, 19 accepted, 0 duplicate, 31 filtered
  total accepted positions: 235
```

- **positions** — 该页 API 返回的总岗位数
- **accepted** — 通过去重和相关度初筛，进入详情抓取的岗位数
- **duplicate** — 因 post_id 重复被跳过的岗位数
- **filtered** — 经 `is_relevant_cs_job()` 判定为非相关 CS 岗位数

### 流水线脚本（scripts/pipeline/）

```
[crawl] 腾讯: crawling https://join.qq.com/...
[crawl] 腾讯: insert=235 skip=0 | 81.2s
[crawl] 国家大学生就业服务平台: insert=512 skip=3 | 120.5s
[crawl] done: sources=2 insert=747 skip=3 | 201.7s

Normalized 400 jobs.

Generated stats for 24 direction-city combinations on 2026-07-03.
```

## Web 前端

基于 Next.js，页面路由：

| 路由 | 内容 |
|------|------|
| `/` | 首页总览 |
| `/cities/[city]` | 城市详情（各方向中位薪资、岗位分布） |
| `/directions/[direction]` | 方向详情（各城市薪资、技能排行、公司排行） |
