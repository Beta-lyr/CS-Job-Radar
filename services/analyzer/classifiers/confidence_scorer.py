from datetime import date, datetime, timezone


SOURCE_SCORES = {
    "company": 95,
    "campus_recruitment": 90,
    "official_platform": 90,
    "university": 85,
    "public_report": 80,
    "user_submission": 50,
}


def calc_confidence(source_type: str, title: str, company: str, city: str, salary: str, description: str, publish_date, direction: str) -> float:
    src_score = SOURCE_SCORES.get(source_type, 70)

    age_days = 30
    if publish_date:
        try:
            if isinstance(publish_date, str):
                publish_date = datetime.fromisoformat(publish_date.replace("Z", "+00:00"))
            if publish_date.tzinfo is None:
                publish_date = publish_date.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - publish_date).days
        except Exception:
            pass
    if age_days <= 3:
        fresh = 100
    elif age_days <= 7:
        fresh = 90
    elif age_days <= 30:
        fresh = 70
    elif age_days <= 60:
        fresh = 50
    else:
        fresh = 30

    complete = 0
    if title:
        complete += 20
    if company:
        complete += 20
    if city:
        complete += 15
    if salary and not _is_undisclosed_salary(salary):
        complete += 15
    if description:
        complete += 20
    if publish_date:
        complete += 10

    dir_score = 80 if direction != "unknown" else 40

    confidence = src_score * 0.35 + fresh * 0.25 + complete * 0.25 + dir_score * 0.15
    return round(min(confidence, 100), 2)


def _is_undisclosed_salary(salary: str) -> bool:
    compact = "".join(str(salary or "").split()).lower()
    return compact in {"未公开", "薪资未公开", "暂未公开", "暂无", "无", "null", "none", "unknown", "不公开", "保密"}
