"""問卷的科技接受模式構面與一般玩家版題目（不碰資料庫）。"""

from typing import Any

import pytest

from app.trial.analytics import tam_constructs
from app.trial.survey import (
    QUESTIONS,
    TAM_CONSTRUCTS,
    SurveyError,
    questions_for,
    validate_answers,
)


def full_answers(questions: tuple[Any, ...], score: int = 4) -> dict[str, Any]:
    answers: dict[str, Any] = {}
    for q in questions:
        if q.kind == "consent":
            answers[q.id] = True
        elif q.kind == "single":
            answers[q.id] = q.options[0]
        elif q.kind == "multi":
            answers[q.id] = [q.options[0]]
        elif q.kind == "scale":
            answers[q.id] = 4 if q.id == "attention" else score
    return answers


def test_every_construct_has_at_least_three_items() -> None:
    ids = {q.id for q in QUESTIONS}
    assert [key for key, _ in TAM_CONSTRUCTS] == ["peou", "pu", "attitude", "intention"]
    for key, _ in TAM_CONSTRUCTS:
        items = [q for q in QUESTIONS if q.construct == key]
        assert len(items) >= 3, key
        assert all(q.kind == "scale" and q.id in ids for q in items)
    # 沿用的舊題
    by_id = {q.id: q.construct for q in QUESTIONS}
    assert by_id["ui_clear"] == "peou"
    assert by_id["distinguish"] == "pu"
    assert by_id["satisfied"] == "attitude"
    assert by_id["recommend"] == "intention"
    assert by_id["attention"] is None


def test_without_exam_skips_difficulty() -> None:
    general = questions_for(exam_done=False)
    assert "exam_difficulty" not in {q.id for q in general}
    assert questions_for(exam_done=True) == QUESTIONS
    clean = validate_answers(full_answers(general), general)
    assert "exam_difficulty" not in clean
    # 試測版仍然要答檢測難度
    with pytest.raises(SurveyError):
        validate_answers(full_answers(general), QUESTIONS)


def test_tam_means_use_answered_items_and_alpha_needs_full_sets() -> None:
    complete = full_answers(QUESTIONS, score=5)
    # 舊問卷沒有新題：構面平均用有答的題，α 不算這份
    old = full_answers(QUESTIONS, score=3)
    for key in ("easy_learn", "useful_faster", "attitude_good", "intention_reuse"):
        old.pop(key)
    rows = {c.key: c for c in tam_constructs([complete, complete, old])}
    assert rows["peou"].n == 3
    assert rows["peou"].mean == pytest.approx((5 + 5 + 3) / 3, abs=0.01)
    assert rows["peou"].complete == 2
    # 兩份完全一樣的答案沒有變異，α 算不出來
    assert rows["peou"].alpha is None


def test_alpha_matches_hand_computation() -> None:
    peou = [q.id for q in QUESTIONS if q.construct == "peou"]
    surveys = []
    for scores in ([5, 5, 4, 5], [3, 3, 3, 2], [4, 4, 5, 4], [2, 1, 2, 2]):
        answers = full_answers(QUESTIONS)
        answers.update(dict(zip(peou, scores, strict=True)))
        surveys.append(answers)
    row = next(c for c in tam_constructs(surveys) if c.key == "peou")
    assert row.alpha is not None and row.alpha > 0.9
