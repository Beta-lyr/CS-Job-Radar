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
        return json.load(f)


def normalize_city(raw: str) -> tuple[str, str]:
    if not raw:
        return ("", "")

    text = _clean(raw)
    if not text:
        return ("", "")

    aliases = load_city_aliases()
    for city, names in aliases.items():
        for name in names:
            if name and name in text:
                district = _extract_district(text, name)
                return (city, district)

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


def _extract_district(text: str, matched_name: str) -> str:
    rest = text.replace(matched_name, "", 1).strip(" /,，;；|")
    if not rest:
        return ""
    rest = re.sub(r"^(省|市)", "", rest)
    return rest[:40]
