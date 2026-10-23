"""試測問卷的作答驗證與發錢條件。"""

from typing import Any

import pytest

from app.trial.payout import payout_reasons
from app.trial.survey import (
    ATTENTION_ID,
    QUESTIONS,
    SurveyError,
    attention_ok,
    export_columns,
    export_value,
    validate_answers,
)


def full_answers() -> dict[str, Any]:
    answers: dict[str, Any] = {}
    for q in QUESTIONS:
        if q.kind == "consent":
            answers[q.id] = True
        elif q.kind == "single":
            answers[q.id] = q.options[0]
        elif q.kind == "multi":
            answers[q.id] = [q.options[1], q.options[0]]
        elif q.kind == "scale":
            answers[q.id] = 3
    answers[ATTENTION_ID] = 4
    return answers


def test_question_ids_are_unique_and_scales_have_five_labels() -> None:
    ids = [q.id for q in QUESTIONS]
    assert len(ids) == len(set(ids))
    for q in QUESTIONS:
        if q.kind == "scale":
            assert len(q.labels) == 5
        if q.kind in ("single", "multi"):
            assert len(q.options) >= 2
        if q.other:
            assert q.options[-1] == "其他"
    # 同意聲明在最前面，注意力題放在中間
    assert QUESTIONS[0].kind == "consent"
    middle = ids.index(ATTENTION_ID)
    assert 0.3 < middle / len(ids) < 0.8


def test_valid_answers_are_cleaned() -> None:
    answers = full_answers()
    answers["unknown"] = "drop me"
    answers["improve"] = "  介面再大一點  "
    clean = validate_answers(answers)
    assert "unknown" not in clean
    assert clean["improve"] == "介面再大一點"
    # 複選照題目的選項順序存
    occasions = next(q for q in QUESTIONS if q.id == "occasions")
    assert clean["occasions"] == [occasions.options[0], occasions.options[1]]
    assert "wishlist" not in clean
    assert attention_ok(clean)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("consent", False),
        ("consent", "true"),
        ("age", "17 歲"),
        ("age", None),
        ("occasions", []),
        ("occasions", ["火星"]),
        ("satisfied", 0),
        ("satisfied", 6),
        ("satisfied", True),
        ("satisfied", "4"),
        ("improve", "字" * 501),
    ],
)
def test_invalid_answers_name_the_question(key: str, value: Any) -> None:
    answers = full_answers()
    answers[key] = value
    with pytest.raises(SurveyError) as error:
        validate_answers(answers)
    assert error.value.question_id == key


def test_other_needs_text() -> None:
    answers = full_answers()
    answers["favorite"] = "其他"
    with pytest.raises(SurveyError) as error:
        validate_answers(answers)
    assert error.value.question_id == "favorite"
    answers["favorite_other"] = "  排行榜 "
    clean = validate_answers(answers)
    assert clean["favorite_other"] == "排行榜"
    answers["occasions"] = ["其他"]
    with pytest.raises(SurveyError):
        validate_answers(answers)
    answers["occasions_other"] = "公司教育訓練"
    assert validate_answers(answers)["occasions_other"] == "公司教育訓練"


def test_attention_wrong_is_accepted_but_flagged() -> None:
    answers = full_answers()
    answers[ATTENTION_ID] = 5
    clean = validate_answers(answers)
    assert not attention_ok(clean)


def test_export_values() -> None:
    clean = validate_answers(full_answers())
    assert export_value(clean, "consent") == "true"
    assert export_value(clean, "satisfied") == 3
    assert "；" in str(export_value(clean, "occasions"))
    assert export_value(clean, "improve") == ""
    columns = export_columns()
    assert columns.index("favorite_other") == columns.index("favorite") + 1
    assert "role_other" not in columns


def payout_row(**overrides: str | int) -> dict[str, str | int]:
    row: dict[str, str | int] = {
        "pretest_done": "true",
        "pretest_seconds": 60,
        "exam_completed": "true",
        "exam_seconds": 180,
        "survey_done": "true",
        "survey_seconds": 60,
        "survey_attention_ok": "true",
    }
    row.update(overrides)
    return row


def test_payout_passes_exactly_at_thresholds() -> None:
    assert payout_reasons(payout_row()) == []


@pytest.mark.parametrize(
    ("overrides", "reasons"),
    [
        ({"pretest_done": "false", "pretest_seconds": ""}, ["前測沒做"]),
        ({"pretest_seconds": ""}, ["前測沒有計時"]),
        ({"pretest_seconds": 59}, ["前測太快"]),
        ({"exam_completed": "false", "exam_seconds": ""}, ["檢測沒有交卷"]),
        ({"exam_seconds": 179}, ["檢測太快"]),
        (
            {"survey_done": "false", "survey_seconds": "", "survey_attention_ok": ""},
            ["問卷沒填"],
        ),
        ({"survey_attention_ok": "false"}, ["問卷注意力題答錯"]),
        ({"survey_seconds": 30}, ["問卷太快"]),
        (
            {"pretest_seconds": 10, "exam_seconds": 10, "survey_seconds": 10},
            ["前測太快", "檢測太快", "問卷太快"],
        ),
    ],
)
def test_payout_reasons(overrides: dict[str, str | int], reasons: list[str]) -> None:
    assert payout_reasons(payout_row(**overrides)) == reasons
