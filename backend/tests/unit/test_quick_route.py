from types import SimpleNamespace
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
        lambda *_args: (
            {"pair-time": "time_pressure", "pair-authority": "authority"},
            {"pair-time": "source-time", "pair-authority": "source-authority"},
        ),
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
    assert tactics.provenance == "pytest"
    assert _suggestions(verdict.tag_details) == EXPECTED_SUGGESTIONS
    assert _suggestions(tactics.tag_details) == EXPECTED_SUGGESTIONS
    assert _suggestions(match.tag_details) == {
        "time_pressure": EXPECTED_SUGGESTIONS["time_pressure"]
    }


def test_match_reveal_returns_each_source_case_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tags = [
        "time_pressure",
        "authority",
        "greed",
        "social_proof",
        "trust_building",
    ]
    cases = {
        case_id: SimpleNamespace(
            provenance=f"source-{case_id}",
            red_flags=[{"tag": tag, "text": f"example-{case_id}"}],
        )
        for case_id, tag in enumerate(tags, start=1)
    }
    monkeypatch.setattr(
        quick_routes, "get_case", lambda _session, case_id: cases.get(case_id)
    )
    quiz = QuizSession(case_ids=list(cases))
    item = {
        "type": "match",
        "pairs": [
            {
                "pair_id": f"pair-{case_id}",
                "case_id": case_id,
                "flag_index": 0,
                "tag": tag,
            }
            for case_id, tag in enumerate(tags, start=1)
        ],
    }

    response = quick_routes._quiz_answer_response(
        Mock(spec=Session),
        quiz,
        item,
        QuizAnswerItem(
            item_id="match",
            pairs={f"pair-{case_id}": tag for case_id, tag in enumerate(tags, start=1)},
        ),
    )

    assert isinstance(response, QuizMatchAnswerResponse)
    assert {pair.pair_id: pair.provenance for pair in response.results} == {
        f"pair-{case_id}": f"source-{case_id}" for case_id in cases
    }


def test_match_frozen_provenance_avoids_db_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tags = [
        "time_pressure",
        "authority",
        "greed",
        "social_proof",
        "trust_building",
    ]
    monkeypatch.setattr(
        quick_routes,
        "get_case",
        lambda *_args: pytest.fail("frozen match data should not query game_cases"),
    )
    quiz = QuizSession(case_ids=list(range(1, 6)))
    item = {
        "pairs": [
            {
                "pair_id": f"pair-{case_id}",
                "case_id": case_id,
                "flag_index": 0,
                "tag": tag,
                "provenance": f"source-{case_id}",
            }
            for case_id, tag in enumerate(tags, start=1)
        ]
    }

    result = quick_routes._correct_match_pairs(Mock(spec=Session), quiz, item)

    assert result == (
        {f"pair-{case_id}": tag for case_id, tag in enumerate(tags, start=1)},
        {f"pair-{case_id}": f"source-{case_id}" for case_id in range(1, 6)},
    )


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
