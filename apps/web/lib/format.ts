export const DIRECTION_LABELS: Record<string, string> = {
  java_backend: "Java 后端",
  go_backend: "Go 后端",
  frontend: "前端开发",
  android: "Android 开发",
  ai_application: "AI 应用开发",
  test_development: "测试开发",
  cpp_system: "C++ / 系统开发",
  embedded: "嵌入式开发",
  hardware: "硬件开发",
  semiconductor: "半导体 / 芯片",
  communication: "通信网络",
  it_support_implementation: "实施 / 技术支持",
  product_manager: "技术产品",
}

export const DIRECTION_SKILLS: Record<string, string> = {
  java_backend: "Spring Boot / Redis / MySQL / Docker / 接口设计",
  go_backend: "Go / Gin / gRPC / 微服务 / 云原生",
  frontend: "React / Vue / TypeScript / 工程化 / 可视化",
  android: "Kotlin / Jetpack / Compose / Gradle",
  ai_application: "LLM / RAG / Agent / Python / 向量数据库",
  test_development: "自动化测试 / 接口测试 / 性能测试 / CI",
  cpp_system: "C++ / Linux / MFC / QT / 性能优化",
  embedded: "C / C++ / ARM / MCU / RTOS / 驱动",
  hardware: "PCB / 原理图 / BOM / 示波器 / 硬件调试",
  semiconductor: "FPGA / Verilog / EDA / 射频 / 集成电路",
  communication: "5G / 网络优化 / TCP/IP / 路由交换",
  it_support_implementation: "系统部署 / ERP / 故障排查 / Linux",
  product_manager: "需求分析 / PRD / 原型 / 数据分析",
}

export function getDirectionLabel(direction: string): string {
  return DIRECTION_LABELS[direction] || direction
}

export function getDirectionSkills(direction: string): string {
  return DIRECTION_SKILLS[direction] || ""
}

export function getChangeLabel(jobCount: number, friendlyCount: number, salaryMedian: number | null): { label: string; type: "up" | "stable" | "risk" } {
  if (salaryMedian && salaryMedian > 18000) {
    return { label: "上升", type: "up" }
  }
  if (friendlyCount > 0 && (friendlyCount / jobCount) > 0.3) {
    return { label: "稳定", type: "stable" }
  }
  return { label: "竞争高", type: "risk" }
}

export function formatSalary(median: number | null): string {
  if (!median) return "—"
  if (median >= 1000) {
    return `${Math.round(median / 1000)}K`
  }
  return `${median}K`
}

export function formatNumber(n: number): string {
  return n.toLocaleString("zh-CN")
}

export function formatWeekRange(start: string, end: string): string {
  const s = new Date(start)
  const e = new Date(end)
  const options: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" }
  return `${s.toLocaleDateString("zh-CN", options)} - ${e.toLocaleDateString("zh-CN", options)}`
}

export interface ProjectSuggestion {
  label: string
  title: string
  description: string
  tags: string[]
}

export const DIRECTION_PROJECTS: Record<string, ProjectSuggestion[]> = {
  java_backend: [
    { label: "Java 后端方向", title: "在线判题系统简化版", description: "适合覆盖任务队列、Docker 沙箱、判题调度、权限和日志。", tags: ["Spring Boot", "Redis", "Docker", "MySQL"] },
    { label: "Java 后端方向", title: "API 网关与权限中心", description: "适合展示路由转发、限流熔断、OAuth2 认证和审计日志。", tags: ["Spring Cloud", "Redis", "JWT", "PostgreSQL"] },
  ],
  go_backend: [
    { label: "Go 后端方向", title: "云原生微服务监控平台", description: "适合展示服务发现、指标采集、告警规则和仪表盘。", tags: ["Go", "gRPC", "Prometheus", "K8s"] },
    { label: "Go 后端方向", title: "分布式任务调度系统", description: "适合展示 DAG 编排、worker 池、失败重试和日志追踪。", tags: ["Go", "Redis", "gRPC", "MongoDB"] },
  ],
  frontend: [
    { label: "前端方向", title: "组件库与文档站搭建", description: "适合展示组件设计、TypeScript 类型、Storybook 和自动化测试。", tags: ["React", "TypeScript", "Storybook", "Vitest"] },
    { label: "前端方向", title: "低代码表单引擎", description: "适合展示拖拽渲染、JSON Schema、表达式引擎和自定义组件。", tags: ["React", "TypeScript", "Zustand", "Tailwind"] },
  ],
  android: [
    { label: "Android 方向", title: "音乐播放器 App", description: "适合展示 Media3 播放、通知栏控制、后台服务和缓存策略。", tags: ["Kotlin", "Jetpack Compose", "Media3", "Room"] },
    { label: "Android 方向", title: "钱包账单管理 App", description: "适合展示图表统计、分类标签、搜索过滤和数据导出。", tags: ["Kotlin", "Compose", "MPAndroidChart", "SQLite"] },
  ],
  ai_application: [
    { label: "AI 应用方向", title: "岗位匹配与简历分析系统", description: "适合展示 RAG、文档解析、岗位匹配、报告生成和服务部署能力。", tags: ["Next.js", "Python", "RAG", "PostgreSQL"] },
    { label: "AI 应用方向", title: "知识库问答机器人", description: "适合展示文档切片、向量检索、Prompt 管理和多轮对话。", tags: ["Python", "LangChain", "Milvus", "FastAPI"] },
  ],
  test_development: [
    { label: "测试开发方向", title: "接口自动化测试平台", description: "适合展示用例管理、数据驱动、断言库和报告生成。", tags: ["Python", "Pytest", "Flask", "Docker"] },
    { label: "测试开发方向", title: "性能压测与监控平台", description: "适合展示分布式压测、指标采集、报告聚合和告警。", tags: ["Python", "JMeter", "InfluxDB", "Grafana"] },
  ],
  cpp_system: [
    { label: "C++ / 系统开发", title: "桌面端设备控制工具", description: "适合展示 C++ 工程能力、设备通信、日志追踪和异常处理。", tags: ["C++", "QT", "TCP/IP", "SQLite"] },
    { label: "C++ / 系统开发", title: "高性能日志检索器", description: "适合覆盖文件索引、多线程、内存管理和性能优化。", tags: ["C++", "多线程", "索引", "性能优化"] },
  ],
  embedded: [
    { label: "嵌入式方向", title: "环境监测终端", description: "适合展示传感器采集、串口通信、数据上报和低功耗设计。", tags: ["C", "STM32", "RTOS", "MQTT"] },
  ],
  hardware: [
    { label: "硬件方向", title: "开发板外设测试平台", description: "适合展示原理图阅读、硬件调试、测试记录和问题定位。", tags: ["PCB", "示波器", "串口", "硬件测试"] },
  ],
  semiconductor: [
    { label: "半导体方向", title: "FPGA 信号处理 Demo", description: "适合展示 Verilog、仿真、时序约束和测试报告。", tags: ["FPGA", "Verilog", "EDA", "仿真"] },
  ],
  communication: [
    { label: "通信网络方向", title: "网络质量监测工具", description: "适合展示链路探测、指标采集、告警和可视化分析。", tags: ["TCP/IP", "Linux", "网络优化", "Grafana"] },
  ],
  it_support_implementation: [
    { label: "实施 / 技术支持方向", title: "企业系统部署与运维手册", description: "适合展示部署脚本、故障排查流程、监控和客户培训文档。", tags: ["Linux", "ERP", "部署", "故障排查"] },
  ],
  product_manager: [
    { label: "技术产品方向", title: "岗位数据看板 PRD", description: "适合展示需求分析、指标设计、原型说明和数据口径。", tags: ["PRD", "原型", "数据分析", "SQL"] },
  ],
}

export function getDirectionProjects(direction: string): ProjectSuggestion[] {
  return DIRECTION_PROJECTS[direction] || []
}
