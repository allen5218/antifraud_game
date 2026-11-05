"""問卷只問做過的事：依作答者的經驗決定題目與「最喜歡的功能」選項。"""

from app.trial.survey import (
    OTHER,
    QUESTIONS,
    SurveyContext,
    questions_for,
)

GAMIFY = "遊戲化（點數、房產、吉祥物、徽章）"
NOTHING = SurveyContext(
    exam_done=False,
    swipe=False,
    quiz=False,
    scenario=False,
    purchased=False,
    badge=False,
)


def ids(ctx: SurveyContext) -> set[str]:
    return {q.id for q in questions_for(ctx)}


def favorite(ctx: SurveyContext) -> tuple[str, ...]:
    return next(q for q in questions_for(ctx) if q.id == "favorite").options


def test_trial_exam_only() -> None:
    ctx = SurveyContext(
        exam_done=True,
        swipe=False,
        quiz=False,
        scenario=False,
        purchased=False,
        badge=False,
    )
    asked = ids(ctx)
    assert {"exam_difficulty", "points_reward", "ai_safe"} <= asked
    assert not {"focus_reason", "focus_match", "gamification", "badges"} & asked
    assert favorite(ctx) == ("滑卡", "訊息判讀", "情境對抗", "檢測", OTHER)


def test_general_swipe_only() -> None:
    ctx = SurveyContext(
        exam_done=False,
        swipe=True,
        quiz=False,
        scenario=False,
        purchased=False,
        badge=False,
    )
    asked = ids(ctx)
    assert {"focus_reason", "focus_match", "gamification"} <= asked
    assert not {"exam_difficulty", "points_reward", "ai_safe", "badges"} & asked
    assert favorite(ctx) == ("滑卡", GAMIFY, OTHER)


def test_purchase_without_practice() -> None:
    ctx = SurveyContext(
        exam_done=False,
        swipe=False,
        quiz=False,
        scenario=False,
        purchased=True,
        badge=False,
    )
    asked = ids(ctx)
    assert "gamification" in asked
    assert not {"focus_reason", "focus_match"} & asked


def test_badge_asked_only_with_badge() -> None:
    with_badge = SurveyContext(
        exam_done=True,
        swipe=False,
        quiz=False,
        scenario=False,
        purchased=False,
        badge=True,
    )
    assert "badges" in ids(with_badge)


def test_favorite_dropped_when_only_other() -> None:
    assert "favorite" not in ids(NOTHING)


def test_tam_items_always_asked() -> None:
    tam = {q.id for q in QUESTIONS if q.construct}
    contexts = [
        NOTHING,
        SurveyContext(True, False, False, False, False, False),
        SurveyContext(False, True, False, False, False, False),
        SurveyContext(True, True, True, True, True, True),
    ]
    for ctx in contexts:
        assert tam <= ids(ctx)


def test_everything_done_asks_everything() -> None:
    full = SurveyContext(True, True, True, True, True, True)
    assert ids(full) == {q.id for q in QUESTIONS}
    assert favorite(full) == next(q for q in QUESTIONS if q.id == "favorite").options


def test_context_json_round_trip() -> None:
    ctx = SurveyContext(True, False, True, False, True, False)
    assert SurveyContext.from_json(ctx.to_json()) == ctx
    assert SurveyContext.from_json({}) == NOTHING


def test_not_asked_counts() -> None:
    """分析頁把「沒被問到」和作答人數分開：條件題都是必填，沒答就是沒問到。"""
    from app.models import TrialSurvey
    from app.trial.analytics import survey_analytics

    with_badge = TrialSurvey(answers={"badges": 4, "favorite": "檢測"})
    without = TrialSurvey(answers={})
    result = survey_analytics([("T-0001", with_badge), ("T-0002", without)])
    badges = next(item for item in result.likert if item.id == "badges")
    assert (badges.n, badges.not_asked) == (1, 1)
    fav = next(item for item in result.choices if item.id == "favorite")
    assert (fav.n, fav.not_asked) == (1, 1)
