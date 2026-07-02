import json
import os
import re
from functools import lru_cache


CITY_RULE_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "data",
    "geo",
    "cities.json",
)


@lru_cache(maxsize=4)
def load_city_aliases(path: str = CITY_RULE_PATH) -> dict[str, list[str]]:
    with open(path, encoding="utf-8") as f:
        raw_rules = json.load(f)

    aliases = {}
    for city, rule in raw_rules.items():
        if city.startswith("__"):
            continue
        if isinstance(rule, list):
            aliases[city] = rule
        elif isinstance(rule, dict):
            aliases[city] = rule.get("aliases", [])
    return aliases


def normalize_city(raw: str) -> tuple[str, str]:
    if not raw:
        return ("", "")

    text = _clean(raw)
    if not text:
        return ("", "")

    aliases = load_city_aliases()
    best_match = None
    for city, names in aliases.items():
        for name in names:
            if name and name in text:
                index = text.find(name)
                score = (index, len(name))
                if best_match is None or score > best_match["score"]:
                    best_match = {"city": city, "name": name, "index": index, "score": score}
    if best_match:
        district = _extract_district(text, best_match["name"], best_match["index"])
        return (best_match["city"], district)

    compact = re.sub(r"[省市区县]", "", text)
    for city, names in aliases.items():
        for name in names:
            if re.sub(r"[省市区县]", "", name) == compact:
                return (city, "")

    return ("other", text)


def _clean(raw: str) -> str:
    text = str(raw).strip()
    text = re.sub(r"\s+", "", text)
    return text.replace("／", "/")


def _extract_district(text: str, matched_name: str, matched_index: int = 0) -> str:
    rest = text[matched_index + len(matched_name):].strip(" /,，;；|")
    if not rest:
        return ""
    rest = re.sub(r"^(省|市)", "", rest)
    return rest[:40]
