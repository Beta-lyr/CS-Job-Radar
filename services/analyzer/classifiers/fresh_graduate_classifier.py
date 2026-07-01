import re


POSITIVE_KEYWORDS = [
    "应届生", "校招", "校园招聘", "毕业生", "经验不限", "接受应届",
    "实习", "可转正", "初级", "助理",
]

NEGATIVE_KEYWORDS = [
    "3年以上", "5年以上", "高级", "专家", "架构师", "负责人",
    "团队管理", "资深",
]


def classify_fresh_graduate(title: str, description: str, experience_level: str, education_level: str) -> tuple[bool, int]:
    text = ((title or "") + " " + (description or "")).lower()
    score = 50

    if "校招" in title.lower():
        score += 30
    if "实习" in title.lower():
        score += 25
    if "应届生" in text:
        score += 25
    if experience_level == "fresh":
        score += 30
    if experience_level == "none":
        score += 15
    if education_level == "bachelor":
        score += 5

    for kw in NEGATIVE_KEYWORDS:
        if kw in text:
            if kw in ("3年以上",):
                score -= 30
            elif kw in ("5年以上",):
                score -= 40
            else:
                score -= 30

    is_friendly = score >= 70
    return (is_friendly, score)


def classify_internship(title: str, description: str) -> bool:
    text = ((title or "") + " " + (description or "")).lower()
    intern_keywords = ["实习", "intern", "internship"]
    return any(kw in text for kw in intern_keywords)


def classify_campus(title: str, description: str) -> bool:
    text = ((title or "") + " " + (description or "")).lower()
    campus_keywords = ["校招", "校园招聘", "campus recruit", "campus hire"]
    return any(kw in text for kw in campus_keywords)
