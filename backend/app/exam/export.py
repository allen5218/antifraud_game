"""管理員檢測匯出；唯讀快照，不結算、不發獎。"""

import uuid
from typing import Any

from sqlmodel import Session, col, select

from app.core.cases import get_case_keys
from app.exam.badges import badge_name
from app.exam.scoring import round_score, tactics_fraction
from app.models import ExamAttempt, ExamBadge, SwipeCard, User

CsvRow = dict[str, str | int]
EXAM_EXPORT_FIELDS = (
    "participant_code",
    "attempt_id",
    "mode",
    "fraud_type",
    "status",
    "counted",
    "started_at",
    "completed_at",
    "duration_seconds",
    "total_score",
    "passed",
    "stage",
    "item_index",
    "item_kind",
    "item_key",
    "is_scam",
    "answer",
    "correct",
)


def cohort_exam_summaries(
    session: Session, cohort_id: uuid.UUID
) -> dict[uuid.UUID, CsvRow]:
    summaries: dict[uuid.UUID, CsvRow] = {}
    attempts = session.exec(
        select(
            ExamAttempt.user_id,
            ExamAttempt.created_at,
            ExamAttempt.counted,
            ExamAttempt.passed,
        )
        .join(User, col(User.id) == col(ExamAttempt.user_id))
        .where(User.cohort_id == cohort_id)
        .order_by(col(ExamAttempt.created_at), col(ExamAttempt.id))
    ).all()
    for user_id, created_at, counted, passed in attempts:
        row = summaries.setdefault(user_id, empty_exam_summary())
        row["exam_attempt_count"] = int(row["exam_attempt_count"]) + int(counted)
        row["exam_pass_count"] = int(row["exam_pass_count"]) + int(counted and passed)
        row["last_exam_at"] = created_at.isoformat()
    badges = session.exec(
        select(ExamBadge)
        .join(User, col(User.id) == col(ExamBadge.user_id))
        .where(User.cohort_id == cohort_id)
        .order_by(col(ExamBadge.first_passed_at), col(ExamBadge.id))
    ).all()
    for badge in badges:
        row = summaries.setdefault(badge.user_id, empty_exam_summary())
        row["badges"] = "；".join(filter(None, [str(row["badges"]), badge_name(badge)]))
    return summaries


def empty_exam_summary() -> CsvRow:
    return {
        "exam_attempt_count": 0,
        "exam_pass_count": 0,
        "last_exam_at": "",
        "badges": "",
    }


def item_answer(
    stage: str, index: int, item: dict[str, Any], answers: dict[str, Any]
) -> tuple[str, str]:
    key = (
        str(index) if stage == "scenario" else str(item.get("item_id", item.get("id")))
    )
    if key not in answers:
        return "", ""
    answer = answers[key]
    if stage == "scenario":
        return str(answer["action"]), str(answer["correct"]).lower()
    if stage == "pretest":
        return str(answer), str(answer == item["correct_option"]).lower()
    if item.get("kind") == "tactics":
        correct = tactics_fraction(set(item["correct_tags"]), answer) == 1.0
        return "；".join(answer), str(correct).lower()
    return "scam" if answer else "legit", str(answer == item["is_scam"]).lower()


def build_exam_export_rows(session: Session, cohort_id: uuid.UUID) -> list[CsvRow]:
    attempts = session.exec(
        select(ExamAttempt, User.participant_code)
        .join(User, col(User.id) == col(ExamAttempt.user_id))
        .where(User.cohort_id == cohort_id)
        .order_by(
            col(User.created_at),
            col(User.id),
            col(ExamAttempt.created_at),
            col(ExamAttempt.id),
        )
    ).all()
    # 整批查回舊快照缺少的代號，避免每題各查一次；正解永遠取自快照。
    case_ids = {
        int(item["case_id"])
        for attempt, _ in attempts
        for stage in ("message", "scenario")
        for item in attempt.items.get(stage, [])
        if not item.get("case_key", item.get("case", {}).get("case_key"))
    }
    case_keys = get_case_keys(session, case_ids)
    swipe_ids = {
        uuid.UUID(item["id"])
        for attempt, _ in attempts
        for item in attempt.items.get("swipe", [])
        if not item.get("seed_key")
    }
    swipe_keys = (
        {
            str(card.id): card.seed_key or str(card.id)
            for card in session.exec(
                select(SwipeCard).where(col(SwipeCard.id).in_(swipe_ids))
            ).all()
        }
        if swipe_ids
        else {}
    )
    rows: list[CsvRow] = []
    for attempt, participant_code in attempts:
        common: CsvRow = {
            "participant_code": participant_code or "",
            "attempt_id": str(attempt.id),
            "mode": attempt.mode,
            "fraud_type": attempt.fraud_type or "",
            "status": attempt.status,
            "counted": str(attempt.counted).lower(),
            "started_at": attempt.created_at.isoformat(),
            "completed_at": attempt.completed_at.isoformat()
            if attempt.completed_at
            else "",
            "duration_seconds": str(
                (attempt.completed_at - attempt.created_at).total_seconds()
            )
            if attempt.completed_at
            else "",
            "total_score": round_score(attempt.total_score),
            "passed": str(attempt.passed).lower(),
        }
        for stage in ("pretest", "swipe", "message", "scenario"):
            for index, item in enumerate(attempt.items.get(stage, [])):
                if stage == "pretest":
                    item_key = str(item["id"])
                elif stage == "swipe":
                    item_key = item.get("seed_key") or swipe_keys.get(
                        str(item["id"]), str(item["id"])
                    )
                else:
                    item_key = (
                        item.get("case_key")
                        or item.get("case", {}).get("case_key")
                        or case_keys.get(int(item["case_id"]), str(item["case_id"]))
                    )
                truth = item.get(
                    "is_scam", True if item.get("kind") == "tactics" else None
                )
                answer, correct = item_answer(
                    stage, index, item, attempt.answers.get(stage, {})
                )
                rows.append(
                    {
                        **common,
                        "stage": stage,
                        "item_index": index + 1,
                        "item_kind": str(item.get("kind", stage)),
                        "item_key": str(item_key),
                        "is_scam": ""
                        if stage == "pretest" or truth is None
                        else str(truth).lower(),
                        "answer": answer,
                        "correct": correct,
                    }
                )
    return rows
