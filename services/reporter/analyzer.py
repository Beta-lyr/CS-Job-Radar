"""LLM 分析模块：接收结构化数据，生成周报分析段落。"""

import json
import os
import sys
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
PROMPT_TEMPLATE = os.path.join(TEMPLATE_DIR, "analysis_prompt.txt")


@dataclass
class AnalysisResult:
    trend_summary: str = ""
    direction_analysis: str = ""
    skill_insight: str = ""
    learning_advice: str = ""


def is_llm_configured() -> bool:
    return bool(os.getenv("LLM_API_KEY", "").strip())


def generate_analysis(data: dict) -> AnalysisResult | None:
    if not is_llm_configured():
        return None

    try:
        prompt = _build_prompt(data)
        content = _call_llm(prompt)
        return _parse_response(content)
    except Exception:
        return None


def _build_prompt(data: dict) -> str:
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("analysis_prompt.txt")
    return template.render(**data)


def _call_llm(prompt: str) -> str:
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.getenv("LLM_BASE_URL"),
        model=os.getenv("LLM_MODEL", "deepseek-chat"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
    )
    response = llm.invoke(prompt)
    return response.content if hasattr(response, "content") else str(response)


def _parse_response(content: str) -> AnalysisResult | None:
    for attempt in range(2):
        try:
            text = content.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            data = json.loads(text)
            return AnalysisResult(
                trend_summary=data.get("trend_summary", ""),
                direction_analysis=data.get("direction_analysis", ""),
                skill_insight=data.get("skill_insight", ""),
                learning_advice=data.get("learning_advice", ""),
            )
        except (json.JSONDecodeError, AttributeError):
            if attempt == 0:
                content = _call_llm(
                    prompt=f"你上次返回了非法的 JSON。请严格返回纯 JSON（不要 ```json``` 包裹）：\n\n前一次的回复：\n{content}"
                )
    return None
