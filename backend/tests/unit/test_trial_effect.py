"""成效分析的純計算：造作答紀錄，不碰資料庫。"""

import uuid
from datetime import datetime, timedelta, timezone

from app.trial.effect import (
    Answer,
    EffectInput,
    EntryPretest,
    ExamRecord,
    effect_analytics,
)

T0 = datetime(2026, 10, 26, 2, 0, tzinfo=timezone.utc)
TYPES = ("investment", "fake-sale", "shopping", "romance", "atm")


def pretest(correct_by_type: dict[str, int]) -> list[tuple[str, bool]]:
    return [(t, i < correct_by_type.get(t, 0)) for t in TYPES for i in range(4)]


def exam(
    user: uuid.UUID,
    *,
    at: datetime = T0,
    status: str = "completed",
    mode: str = "comprehensive",
    score: int = 72,
    passed: bool = True,
    correct: dict[str, int] | None = None,
    later: dict[str, list[bool]] | None = None,
    completed: bool = True,
) -> ExamRecord:
    return ExamRecord(
        user_id=user,
        created_at=at,
        completed_at=at + timedelta(minutes=10) if completed else None,
        status=status,
        counted=True,
        mode=mode,
        passed=passed,
        score=score,
        weakest="romance",
        pretest=pretest(correct or {}),
        later=later if later is not None else {},
    )


def answer(
    user: uuid.UUID,
    at: datetime,
    correct: bool,
    *,
    mode: str = "swipe",
    fraud_type: str = "romance",
    missed: list[str] | None = None,
) -> Answer:
    return Answer(
        user_id=user,
        mode=mode,
        fraud_type=fraud_type,
        correct=correct,
        missed_tags=missed or [],
        at=at,
    )


def test_empty_input() -> None:
    result = effect_analytics(EffectInput([], [], []))
    assert result.exam.change.n == 0
    assert result.exam.change.before_mean is None
    assert result.repeat.people == 0
    assert result.entry.total.n == 0
    assert result.practice.curve == []
    assert result.practice.baseline_people == 0
    assert result.volume.exam_people == 0
    assert result.volume.median_answers is None


def test_exam_stage_change() -> None:
    user = uuid.uuid4()
    data = EffectInput(
        [
            exam(
                user,
                correct={"romance": 1},
                later={
                    "swipe": [True, True],
                    "message": [False, True],
                    "scenario": [True],
                },
            )
        ],
        [],
        [],
    )
    result = effect_analytics(data).exam
    assert result.stages[0].key == "pretest_weakest"
    assert result.stages[0].accuracy == 25.0
    assert result.change.before_mean == 25.0
    assert result.change.after_mean == 80.0
    assert result.change.improved == 1


def test_exam_without_later_answers_skipped() -> None:
    user = uuid.uuid4()
    data = EffectInput(
        [exam(user, status="abandoned", completed=False, later={})], [], []
    )
    result = effect_analytics(data)
    assert result.exam.change.n == 0
    assert result.volume.exam_people == 1


def test_repeat_and_retake() -> None:
    user = uuid.uuid4()
    first = exam(user, score=60, passed=False, correct=dict.fromkeys(TYPES, 2))
    first.pretest = pretest({"investment": 4, "fake-sale": 4, "shopping": 4})
    second = exam(user, at=T0 + timedelta(days=1), score=75, passed=True)
    second.pretest = pretest(
        {"investment": 4, "fake-sale": 4, "shopping": 4, "romance": 3}
    )
    result = effect_analytics(EffectInput([first, second], [], [])).repeat
    assert result.people == 1
    assert result.score.diff_mean == 15.0
    assert result.pretest.diff_mean == 3.0
    assert result.failed_first == 1
    assert result.retook == 1
    assert result.retake_passed == 1


def test_entry_vs_exam() -> None:
    user = uuid.uuid4()
    entry = EntryPretest(user, T0 - timedelta(days=1), pretest(dict.fromkeys(TYPES, 2)))
    later = exam(user, correct=dict.fromkeys(TYPES, 3))
    result = effect_analytics(EffectInput([later], [entry], [])).entry
    assert result.total.n == 1
    assert result.total.before_mean == 50.0
    assert result.total.after_mean == 75.0
    assert result.by_type[0].before == 50.0
    assert result.by_type[0].after == 75.0
    assert result.practiced_between == 0


def test_practice_before_baseline_ignored() -> None:
    user = uuid.uuid4()
    first = exam(user, correct={"romance": 1})
    done = T0 + timedelta(minutes=10)
    answers = [
        answer(user, done - timedelta(minutes=1), True),
        answer(user, done + timedelta(minutes=1), True),
        answer(user, done + timedelta(minutes=2), False),
    ]
    result = effect_analytics(EffectInput([first], [], answers)).practice
    assert result.baseline_people == 1
    assert result.curve[0].items == 2
    assert result.curve[0].accuracy == 50.0


def test_practice_curve_and_modes() -> None:
    user = uuid.uuid4()
    first = exam(user)
    start = T0 + timedelta(hours=1)
    answers = [
        answer(
            user,
            start + timedelta(minutes=i),
            i >= 6,
            missed=None if i >= 6 else ["greed"],
        )
        for i in range(12)
    ]
    result = effect_analytics(EffectInput([first], [], answers)).practice
    assert [p.label for p in result.curve] == ["1–10", "11–20"]
    assert result.curve[0].missed_rate == 60.0
    swipe = next(m for m in result.modes if m.mode == "swipe")
    assert swipe.change.before_mean == 0.0
    assert swipe.change.after_mean == 100.0
    greed = next(t for t in result.tags if t.tag == "greed")
    assert (greed.first_half, greed.second_half) == (6, 0)


def test_specialized_only_ignored() -> None:
    user = uuid.uuid4()
    data = EffectInput(
        [exam(user, mode="specialized", later={"swipe": [True]})], [], []
    )
    result = effect_analytics(data)
    assert result.exam.change.n == 0
    assert result.volume.exam_people == 0


def test_volume() -> None:
    a, b = uuid.uuid4(), uuid.uuid4()
    day1 = T0 + timedelta(hours=1)
    day2 = T0 + timedelta(days=1, hours=1)
    answers = [
        answer(a, day1, True),
        answer(a, day1 + timedelta(minutes=1), True, mode="scenario"),
        answer(a, day2, False),
    ]
    result = effect_analytics(EffectInput([exam(a), exam(b)], [], answers)).volume
    assert result.exam_people == 2
    assert result.practiced_people == 1
    assert result.median_answers == 3
    assert result.median_days == 2
    assert result.scenario_rounds == 1
