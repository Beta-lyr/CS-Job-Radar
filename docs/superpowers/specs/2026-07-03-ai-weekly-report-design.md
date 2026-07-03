# AI 周报分析系统设计

## 目标

用 LLM 将周报中硬编码的分析段落替换为基于真实数据的智能文案，保持表格由 SQL 直接生成。

## env 配置

```env
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=0.3
```

- 四个变量覆盖任意 OpenAI 兼容 API（DeepSeek、OpenAI、Ollama、vLLM）
- `LLM_API_KEY` 为空时跳过 AI 生成，回退硬编码模板
- 通过 `python-dotenv` 加载

## 目录结构

```
services/reporter/
  requirements.txt              # 更新：新增 langchain-openai, jinja2
  analyzer.py                   # 新增：LLM 调用封装
  templates/
    analysis_prompt.txt         # 新增：AI prompt 模板
    weekly_report.md.j2         # 新增：报告 Markdown Jinja2 模板

scripts/report/
  weekly.py                     # 修改：拆函数 + 集成 analyzer
```

## 模块设计

### `services/reporter/analyzer.py`

**输入**：结构化 dict（方向排行、薪资、技能、环比变化）
**输出**：`AnalysisResult` dataclass（4 段 markdown）或 `None`（LLM 不可用时）

核心函数：

| 函数 | 职责 |
|------|------|
| `is_llm_configured()` | 检查 `LLM_API_KEY` 是否非空 |
| `generate_analysis(data: dict) -> AnalysisResult or None` | 主入口 |
| `_build_prompt(data)` | Jinja2 渲染 `analysis_prompt.txt` |
| `_call_llm(prompt)` | LangChain `ChatOpenAI.invoke()` |
| `_parse_response(text)` | 解析 JSON 返回，失败重试 1 次 |

使用 `langchain-openai` 的 `ChatOpenAI`（轻量，只装这一个模块）：

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    model=os.getenv("LLM_MODEL", "deepseek-chat"),
    temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
)
response = llm.invoke(prompt)
```

**错误处理**：
- LLM 返回非 JSON → 重试 1 次
- 两次失败 → 返回 `None`
- 网络超时 → 返回 `None`

### `services/reporter/templates/analysis_prompt.txt`

Jinja2 模板，注入当周 + 环比数据。要求 LLM 严格返回 JSON（不含 markdown 代码块包裹），字段：

```json
{
  "trend_summary": "本周整体趋势总结，1-2 段",
  "direction_analysis": "各方向对比解读，含变化原因推测，1-2 段",
  "skill_insight": "技能需求洞察，技能-方向关联分析，1-2 段",
  "learning_advice": "给计算机专业学生的学习建议，2-3 条"
}
```

### `services/reporter/templates/weekly_report.md.j2`

Jinja2 模板，渲染完整 Markdown 报告。包含 7 个部分：
1. 本周趋势总结（AI / 默认）
2. 方向热度排行（表格）
3. 方向薪资中位数（表格）
4. 方向对比解读（AI / 默认）
5. 技能热度榜 Top 15（表格）
6. 技能洞察（AI / 默认）
7. 学习建议（AI / 默认）

表格占位由 Jinja2 循环渲染，AI 段落通过 `{{ analysis.trend_summary or default }}` 注入。

### `scripts/report/weekly.py` 改造

当前 `run()` 拆为 6 个函数：

| 函数 | 职责 |
|------|------|
| `get_report_range(session)` | 确定 7 天时间范围 |
| `query_current_week(session, start, end)` | 当周方向热度、薪资、技能 |
| `query_previous_week(session, start, end)` | 上周数据（用于计算环比） |
| `build_report_data(current, previous)` | 合并为传给 AI 和模板的 dict |
| `generate_report_markdown(data, analysis, start, end)` | Jinja2 渲染模板 |
| `save_report(session, markdown, data, start, end)` | UPSERT `weekly_reports` 表 |

`run()` 只做编排：

```python
def run():
    auto_migrate()
    session = get_session()
    week_start, week_end = get_report_range(session)
    current = query_current_week(session, week_start, week_end)
    previous = query_previous_week(session, week_start, week_end)
    report_data = build_report_data(current, previous)
    analysis = generate_analysis(report_data) if is_llm_configured() else None
    markdown = generate_report_markdown(report_data, analysis, week_start, week_end)
    save_report(session, markdown, report_data, week_start, week_end)
```

**环比计算**：查上周同口径数据，计算变化率：

```python
def _calc_change(curr, prev):
    if not prev: return "-"
    return f"{(curr - prev) / prev * 100:+.0f}%"
```

**summary 字段**：由 `analysis.trend_summary` 前 120 字符代替硬编码。

## 前端影响

**零改动**。前端只消费 `weekly_reports.content_markdown` 字符串，用 `react-markdown` 渲染。AI 生成的是标准 Markdown，和之前完全兼容。

## GitHub Actions

`weekly-report.yml` 新增 env secrets：

```yaml
env:
  LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
  LLM_BASE_URL: ${{ secrets.LLM_BASE_URL }}
  LLM_MODEL: ${{ secrets.LLM_MODEL }}
```

## 兜底机制

`LLM_API_KEY` 为空时回退硬编码模板，报告仍正常生成，只是分析段落为固定文字。

## 新增依赖

```txt
langchain-openai>=0.2.0
jinja2>=3.1.0
```
