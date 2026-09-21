from unittest.mock import Mock

import pytest
from pydantic import ValidationError
from sqlmodel import Session

from app.api.routes import quick as quick_routes
from app.models import QuizSession
from app.schemas import (
    QuizAnswerItem,
    QuizCompleteRequest,
    QuizMatchAnswerResponse,
    QuizTacticsAnswerResponse,
    QuizVerdictAnswerResponse,
    QuizWeaknessDetail,
    WeaknessSummaryItem,
)

EXPECTED_SUGGESTIONS = {
    "time_pressure": "遇到「限時」「緊急」等話術時，先深呼吸，給自己 24 小時冷靜期",
    "authority": "不要因為對方自稱專家或官員就輕信，主動查證對方身份",
}


class _Case:
    is_scam = True
    red_flags = [
        {"tag": "time_pressure", "text": "限時處理"},
        {"tag": "authority", "text": "假冒官員"},
    ]
    provenance = "pytest"


def _suggestions(details: list[QuizWeaknessDetail]) -> dict[str, str]:
    return {detail.tag: detail.suggestion for detail in details}


def test_each_quiz_reveal_type_returns_authoritative_suggestions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quiz = QuizSession(case_ids=[1])
    monkeypatch.setattr(quick_routes, "_item_case", lambda *_args: _Case())
    monkeypatch.setattr(
        quick_routes,
        "_correct_match_pairs",
        lambda *_args: {"pair-time": "time_pressure", "pair-authority": "authority"},
    )
    session = Mock(spec=Session)

    verdict = quick_routes._quiz_answer_response(
        session,
        quiz,
        {"type": "verdict", "case_id": 1},
        QuizAnswerItem(item_id="verdict", guess_is_scam=False),
    )
    tactics = quick_routes._quiz_answer_response(
        session,
        quiz,
        {"type": "tactics", "case_id": 1},
        QuizAnswerItem(item_id="tactics", selected_tags=["authority"]),
    )
    match = quick_routes._quiz_answer_response(
        session,
        quiz,
        {"type": "match"},
        QuizAnswerItem(
            item_id="match",
            pairs={"pair-time": "authority", "pair-authority": "authority"},
        ),
    )

    assert isinstance(verdict, QuizVerdictAnswerResponse)
    assert isinstance(tactics, QuizTacticsAnswerResponse)
    assert isinstance(match, QuizMatchAnswerResponse)
    assert _suggestions(verdict.tag_details) == EXPECTED_SUGGESTIONS
    assert _suggestions(tactics.tag_details) == EXPECTED_SUGGESTIONS
    assert _suggestions(match.tag_details) == {
        "time_pressure": EXPECTED_SUGGESTIONS["time_pressure"]
    }


def test_quiz_complete_request_contains_only_session_id() -> None:
    request = QuizCompleteRequest(session_id="session")

    assert request.model_dump() == {"session_id": "session"}


def test_weakness_summary_item_keeps_backend_provided_label() -> None:
    item = WeaknessSummaryItem.model_validate(
        {"tag": "authority", "label": "權威服從", "count": 1}
    )

    assert item.model_dump() == {
        "tag": "authority",
        "label": "權威服從",
        "count": 1,
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("item_id", "x" * 65),
        ("selected_tags", ["authority"] * 6),
        ("selected_tags", ["x" * 33]),
        ("pairs", {f"pair-{index}": "authority" for index in range(6)}),
        ("pairs", {"x" * 65: "authority"}),
        ("pairs", {"pair": "x" * 65}),
    ],
)
def test_quiz_answer_item_rejects_oversized_nested_payload(
    field: str, value: object
) -> None:
    payload = {"item_id": "item", field: value}

    with pytest.raises(ValidationError):
        QuizAnswerItem.model_validate(payload)


def test_quiz_complete_uses_real_case_narrative_length_for_calibration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """證明長題與短題把真實 case narrative 長度送進估算，而非 0。"""
    recorded_lengths: list[int] = []

    def mock_estimate(
        narrative_length: int = 0,
        response_time_ms: int | None = None,
        switch_count: int | None = None,
        interaction_obscured: bool | None = None,
    ) -> float:
        recorded_lengths.append(narrative_length)
        return 0.85

    from app.core import calibration
    monkeypatch.setattr(calibration, "estimate_behavioral_confidence", mock_estimate)

    class LongCase:
        is_scam = True
        narrative = "這是一道敘述相當詳盡的詐騙案例" * 5  # 15 * 5 = 75 chars
        red_flags = []

    class ShortCase:
        is_scam = False
        narrative = "短情境"  # 3 chars
        red_flags = []

    quiz = Mock()
    quiz.id = "mock-quiz-id"
    quiz.completed = False
    quiz.items = [
        {"item_id": "v-long", "type": "verdict", "case_id": 1},
        {"item_id": "v-short", "type": "verdict", "case_id": 2},
    ]
    quiz.answers = {
        "v-long": {"guess_is_scam": True, "response_time_ms": 3000, "option_switch_count": 0},
        "v-short": {"guess_is_scam": False, "response_time_ms": 1500, "option_switch_count": 0},
    }

    cases_by_id = {1: LongCase(), 2: ShortCase()}

    monkeypatch.setattr(quick_routes, "_get_quiz_session", lambda *a, **kw: quiz)
    monkeypatch.setattr(
        quick_routes,
        "_dealt_quiz_items",
        lambda q: {item["item_id"]: item for item in q.items},
    )
    monkeypatch.setattr(quick_routes, "_quiz_answers", lambda q: q.answers)
    monkeypatch.setattr(
        quick_routes,
        "_item_case",
        lambda s, q, item: cases_by_id.get(item.get("case_id")),
    )
    monkeypatch.setattr(quick_routes, "_score_quiz_item", lambda s, q, item, ans: (True, []))
    monkeypatch.setattr(quick_routes, "_get_user_insight_bonus", lambda *a: 0.0)
    monkeypatch.setattr(quick_routes, "lock_user", lambda s, u: u)
    monkeypatch.setattr(quick_routes, "adjust_cash", lambda *a, **kw: None)
    monkeypatch.setattr(quick_routes, "add_xp", lambda *a, **kw: None)
    monkeypatch.setattr(quick_routes, "record_quiz_progress", lambda *a: None)

    session = Mock(spec=Session)
    user = Mock()
    user.id = "user-id"
    user.completed_chapters = 0

    quick_routes.quiz_complete(
        payload=QuizCompleteRequest(session_id="mock-session"),
        session=session,
        current_user=user,
    )

    assert len(recorded_lengths) == 2
    assert recorded_lengths[0] == 75
    assert recorded_lengths[1] == 3
    assert all(l != 0 for l in recorded_lengths)
