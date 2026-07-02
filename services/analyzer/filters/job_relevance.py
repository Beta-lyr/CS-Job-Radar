import json
import os
import re
from functools import lru_cache
from html import unescape


RULE_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "data",
    "job-filter-rules",
    "cs_jobs.json",
)


@lru_cache(maxsize=8)
def load_rules(path: str = RULE_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def is_relevant_cs_job(title: str = "", description: str = "", major: str = "", tags: str = "", rules: dict | None = None) -> bool:
    rules = rules or load_rules()
    title_text = _clean(title)
    desc_text = _clean(description)
    major_text = _clean(major)
    tags_text = _clean(tags)

    if not title_text and not desc_text:
        return False

    if _contains_any(title_text, rules.get("exclude_title_keywords", [])):
        return False

    strong_title = _contains_any(title_text, rules.get("strong_title_keywords", []))
    weak_title = _contains_any(title_text, rules.get("weak_title_keywords", []))
    desc_match = _contains_any(desc_text, rules.get("description_keywords", []))
    tag_match = _contains_any(tags_text, rules.get("description_keywords", []))
    major_match = _contains_any(major_text, rules.get("major_only_keywords", []))

    options = rules.get("rules", {})
    if options.get("generic_posting_requires_strong_title", True):
        if _contains_any(title_text, rules.get("generic_posting_keywords", [])) and not strong_title:
            return False

    if strong_title:
        return True

    if weak_title:
        if options.get("weak_title_requires_description", True):
            return desc_match or tag_match
        return True

    if major_match and options.get("major_only_cannot_accept", True):
        return desc_match

    return desc_match


def _contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(_keyword_match(lowered, kw.lower()) for kw in keywords if kw)


def _keyword_match(text: str, keyword: str) -> bool:
    if re.fullmatch(r"[a-z0-9+#.]+", keyword):
        return re.search(rf"(?<![a-z0-9+#.]){re.escape(keyword)}(?![a-z0-9+#.])", text) is not None
    return keyword in text


def _clean(value) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    value = unescape(value)
    return re.sub(r"\s+", " ", value.replace("\x00", " ")).strip()
