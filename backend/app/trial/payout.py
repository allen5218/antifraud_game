"""試測發錢的條件。匯出時逐條檢查，不合格的原因用中文寫進 CSV。"""

from app.trial.survey import MIN_SECONDS as SURVEY_MIN_SECONDS

PRETEST_MIN_SECONDS = 60
"""入門前測 20 題，少於一分鐘交卷就是沒看題目。"""

EXAM_MIN_SECONDS = 180
"""檢測要考到三分鐘以上；只用時最長的那一次正常交卷來看。"""

CsvRow = dict[str, str | int]


def _seconds(value: str | int) -> float | None:
    return float(value) if value != "" else None


def payout_reasons(row: CsvRow) -> list[str]:
    """`row` 是成員 CSV 的一列（前測、檢測、問卷的摘要已經合進來）。"""
    reasons: list[str] = []
    if row["pretest_done"] != "true":
        reasons.append("前測沒做")
    else:
        seconds = _seconds(row["pretest_seconds"])
        if seconds is None:
            reasons.append("前測沒有計時")
        elif seconds < PRETEST_MIN_SECONDS:
            reasons.append("前測太快")
    if row["exam_completed"] != "true":
        reasons.append("檢測沒有交卷")
    else:
        seconds = _seconds(row["exam_seconds"])
        if seconds is None or seconds < EXAM_MIN_SECONDS:
            reasons.append("檢測太快")
    if row["survey_done"] != "true":
        reasons.append("問卷沒填")
    else:
        if row["survey_attention_ok"] != "true":
            reasons.append("問卷注意力題答錯")
        seconds = _seconds(row["survey_seconds"])
        if seconds is None or seconds < SURVEY_MIN_SECONDS:
            reasons.append("問卷太快")
    return reasons
