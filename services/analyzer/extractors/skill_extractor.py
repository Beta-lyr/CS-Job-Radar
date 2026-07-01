import json
import os
import re


_skill_dict: list[dict] | None = None


def _load_skill_dict() -> list[dict]:
    global _skill_dict
    if _skill_dict is None:
        paths = [
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "skill-dict", "skills.json"),
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "skill-dict", "skills.json"),
        ]
        for path in paths:
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    _skill_dict = json.load(f)
                break
        if _skill_dict is None:
            _skill_dict = []
    return _skill_dict


def extract_skills(title: str, description: str) -> list[dict]:
    text = ((title or "") + " " + (description or "")).lower()
    skills = _load_skill_dict()
    results: list[dict] = []
    seen: set[str] = set()

    for skill in skills:
        for alias in skill.get("aliases", []):
            if alias.lower() in text and skill["name"] not in seen:
                required, bonus = _classify_required_bonus(text, alias.lower())
                results.append({
                    "skill_name": skill["name"],
                    "skill_category": skill["category"],
                    "is_required": required,
                    "is_bonus": bonus,
                    "confidence": 0.8,
                })
                seen.add(skill["name"])
                break

    return results


def _classify_required_bonus(text: str, keyword: str) -> tuple[bool, bool]:
    required_prefixes = ["熟悉", "掌握", "精通", "必须", "要求", "具备", "能够", "需要"]
    bonus_prefixes = ["加分", "优先", "了解", "有经验者优先", "熟悉者优先"]

    for prefix in required_prefixes:
        if re.search(re.escape(prefix) + r"\s*" + re.escape(keyword), text):
            return (True, False)

    for prefix in bonus_prefixes:
        if re.search(re.escape(prefix) + r"\s*" + re.escape(keyword), text):
            return (False, True)

    return (False, False)
