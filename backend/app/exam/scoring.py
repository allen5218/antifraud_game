"""檢測計分、終止與補考條件。純函式，不讀寫資料庫。"""

from collections.abc import Sequence
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.core.weakness import WEAKNESS_TAGS
from app.exam.config import (
    EXAM_PASS_SCORE,
    MODES,
    RETAKE_CORRECT,
    RETAKE_QUIZ,
    RETAKE_RECENT,
    RETAKE_SCENARIO,
    RETAKE_SWIPE,
)


def tactics_fraction(correct: set[str], selected: Sequence[str]) -> float:
    chosen = set(selected)
    if not correct or not chosen or chosen >= WEAKNESS_TAGS:
        return 0.0
    wrong = WEAKNESS_TAGS - correct
    return max(
        0.0,
        len(chosen & correct) / len(correct)
        - (len(chosen - correct) / len(wrong) if wrong else 0.0),
    )


def part_score(mode: str, part: str, correct: Sequence[bool | float]) -> float:
    return float(sum(correct) * getattr(MODES[mode], f"{part}_points"))


def round_score(score: float) -> int:
    return int(Decimal(str(score)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def is_passed(score: float) -> bool:
    # 和結果頁顯示的總分用同一把尺：69.5 顯示成 70，就要算通過
    return round_score(score) >= EXAM_PASS_SCORE


def terminal_status(
    stage: str,
    now: datetime,
    ai_error_at: datetime | None,
    last_ok_at: datetime | None,
    *,
    abandoned: bool = False,
) -> str:
    """呼叫端已確認到期；只有情境關未恢復的 AI 故障才作廢。"""
    if abandoned:
        return "abandoned"
    if (
        stage == "scenario"
        and ai_error_at is not None
        and ai_error_at <= now
        and (last_ok_at is None or ai_error_at > last_ok_at)
    ):
        return "voided"
    return "expired"


def gate_met(swipe: int, quiz: int, scenario: int, recent: Sequence[bool]) -> bool:
    return (
        swipe >= RETAKE_SWIPE
        and quiz >= RETAKE_QUIZ
        and scenario >= RETAKE_SCENARIO
        and len(recent) >= RETAKE_RECENT
        and sum(recent[:RETAKE_RECENT]) >= RETAKE_CORRECT
    )


def score_answers(
    mode: str, items: dict[str, list[dict[str, Any]]], answers: dict[str, Any]
) -> tuple[dict[str, float], dict[str, int], list[str]]:
    """只讀鎖定快照與玩家答案；沒有作答的題目得零分。"""
    from app.core.fraud_types import FRAUD_TYPES

    by_type = dict.fromkeys(FRAUD_TYPES, 0)
    scores = dict.fromkeys(("pretest", "swipe", "verdict", "tactics", "scenario"), 0.0)
    missed: list[str] = []
    for stage, rows in items.items():
        stage_answers = answers.get(stage, {})
        if not isinstance(stage_answers, dict):
            continue
        for item_index, item in enumerate(rows):
            key = str(item.get("item_id", item.get("id", "")))
            answer = stage_answers.get(key)
            if stage == "pretest":
                ok = answer is not None and answer == item.get("correct_option")
                ft = str(item["fraud_type"])
                by_type[ft] += int(ok)
                scores["pretest"] += part_score(mode, "pretest", [ok])
            elif stage == "swipe":
                ok = isinstance(answer, bool) and answer == item.get("is_scam")
                scores["swipe"] += part_score(mode, "swipe", [ok])
            elif stage == "message":
                if item["kind"] == "tactics":
                    correct = set(item.get("correct_tags", []))
                    chosen = answer if isinstance(answer, list) else []
                    scores["tactics"] += part_score(
                        mode, "tactics", [tactics_fraction(correct, chosen)]
                    )
                    # 沒作答（到期時還沒做到）就不列，否則等於公布這題的正解
                    if isinstance(answer, list):
                        missed = sorted(correct - set(chosen))
                else:
                    ok = isinstance(answer, bool) and answer == item.get("is_scam")
                    scores["verdict"] += part_score(mode, "verdict", [ok])
            elif stage == "scenario":
                # scenario 的 key 是順序，不公開配對規則或裁決結果。
                judged = stage_answers.get(str(item_index))
                ok = isinstance(judged, dict) and judged.get("correct") is True
                scores["scenario"] += part_score(mode, "scenario", [ok])
    return scores, by_type, missed
