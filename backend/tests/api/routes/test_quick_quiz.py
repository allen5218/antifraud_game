import json
import logging
import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session, select

from app.api.routes import quick as quick_routes
from app.core import quiz as quiz_core
from app.core.cases import get_case, list_published_for_quiz
from app.core.config import settings
from app.core.quiz import case_tags
from app.models import QuizSession, User

EXPECTED_WEAKNESS_DETAILS = {
    "time_pressure": (
        "時間壓力",
        "遇到「限時」「緊急」等話術時，先深呼吸，給自己 24 小時冷靜期",
    ),
    "authority": ("權威服從", "不要因為對方自稱專家或官員就輕信，主動查證對方身份"),
    "greed": ("貪念誘惑", "記住「高報酬必伴隨高風險」，保證獲利幾乎都是詐騙"),
    "social_proof": ("社會認同", "不要因為「很多人都在做」就跟風，獨立思考很重要"),
    "trust_building": ("信任建立", "即使對方展示了真實資訊，也不代表整件事是真的"),
}


def _assert_weakness_details(
    details: list[dict[str, str]], expected_tags: set[str]
) -> None:
    assert {detail["tag"] for detail in details} == expected_tags
    for detail in details:
        assert (detail["label"], detail["suggestion"]) == EXPECTED_WEAKNESS_DETAILS[
            detail["tag"]
        ]


def _deal(
    client: TestClient, headers: dict[str, str], size: int = 5
) -> tuple[str, list[dict[str, Any]]]:
    response = client.get(
        f"{settings.API_V1_STR}/quick/quiz/deck?size={size}", headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    return body["session_id"], body["items"]


def _quiz(db: Session, session_id: str) -> QuizSession:
    db.expire_all()
    quiz = db.get(QuizSession, uuid.UUID(session_id))
    assert quiz is not None
    return quiz


def _stored_item(db: Session, session_id: str, item_id: str) -> dict[str, Any]:
    item = next(
        (
            stored
            for stored in _quiz(db, session_id).items
            if stored["item_id"] == item_id
        ),
        None,
    )
    assert item is not None
    return item


def _correct_answer(
    db: Session, session_id: str, public_item: dict[str, Any]
) -> dict[str, Any]:
    stored = _stored_item(db, session_id, public_item["item_id"])
    answer: dict[str, Any] = {"item_id": public_item["item_id"]}
    if stored["type"] == "verdict":
        answer["guess_is_scam"] = stored["is_scam"]
    elif stored["type"] == "tactics":
        answer["selected_tags"] = stored["correct_tags"]
    else:
        answer["pairs"] = {pair["pair_id"]: pair["tag"] for pair in stored["pairs"]}
    return answer


def _submit_answer(
    client: TestClient,
    headers: dict[str, str],
    session_id: str,
    answer: dict[str, Any],
) -> Any:
    return client.post(
        f"{settings.API_V1_STR}/quick/quiz/answer",
        headers=headers,
        json={"session_id": session_id, **answer},
    )


def test_deck_returns_mixed_items_without_answers(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    session_id, items = _deal(client, normal_user_token_headers, size=5)

    assert session_id
    assert len(items) == 5
    assert len({item["item_id"] for item in items}) == len(items)
    assert [item["item_id"] for item in items] == [
        item["item_id"] for item in _quiz(db, session_id).items
    ]
    assert {item["type"] for item in items} <= {"verdict", "tactics", "match"}
    for item in items:
        assert "case_id" not in item
        assert "is_scam" not in item
        assert "red_flags" not in item
        assert "provenance" not in item
        if item["type"] == "tactics":
            assert len(item["options"]) == 5
        if item["type"] == "match":
            assert len(item["match_prompts"]) == 5
            assert len(item["match_targets"]) == 5


def test_deck_never_reuses_case_and_tactics_are_scam(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    fixture_cases = [
        case
        for case in list_published_for_quiz(db)
        if case.provenance == "pytest fixture"
    ]
    mirror_source = next(
        case for case in fixture_cases if case.title == "pytest investment scam-a"
    )
    mirror = next(
        case for case in fixture_cases if case.title == "pytest investment legit"
    )
    assert mirror.mirror_of == mirror_source.id

    session_id, _ = _deal(client, normal_user_token_headers, size=10)
    quiz = _quiz(db, session_id)

    assert len(quiz.items) == 10
    assert len(quiz.case_ids) == len(set(quiz.case_ids))
    selected_cases = [get_case(db, case_id) for case_id in quiz.case_ids]
    assert all(case is not None for case in selected_cases)
    selected_ids = set(quiz.case_ids)
    assert all(
        case.mirror_of not in selected_ids
        for case in selected_cases
        if case is not None and case.mirror_of is not None
    )
    for item in quiz.items:
        if item["type"] in {"verdict", "tactics"}:
            assert {"item_id", "type", "case_id"} <= set(item)
        else:
            assert set(item) == {"item_id", "type", "pairs"}
            assert all(
                set(pair) == {"pair_id", "case_id", "flag_index", "tag", "text"}
                for pair in item["pairs"]
            )
        if item["type"] != "tactics":
            continue
        case = get_case(db, item["case_id"])
        assert case is not None
        assert case.is_scam is True
        assert len(case_tags(case.red_flags)) >= 2


def test_deck_balances_verdicts_with_skewed_fixture(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    monkeypatch: Any,
) -> None:
    fixture_cases = [
        case
        for case in list_published_for_quiz(db)
        if case.provenance == "pytest fixture"
    ]
    assert sum(case.is_scam for case in fixture_cases) == 10
    assert sum(not case.is_scam for case in fixture_cases) == 5
    minimum_gaps: list[int] = []
    original_minimum_gap = quiz_core._minimum_possible_verdict_gap

    def record_minimum_gap(candidates: list[quiz_core.QuizMaterial]) -> int:
        minimum_gap = original_minimum_gap(candidates)
        minimum_gaps.append(minimum_gap)
        return minimum_gap

    monkeypatch.setattr(quiz_core, "_minimum_possible_verdict_gap", record_minimum_gap)
    monkeypatch.setattr(
        quick_routes, "list_published_for_quiz", lambda _session: fixture_cases.copy()
    )

    session_id, _ = _deal(client, normal_user_token_headers, size=10)
    verdict_cases = [
        get_case(db, item["case_id"])
        for item in _quiz(db, session_id).items
        if item["type"] == "verdict"
    ]
    verdict_scam = sum(case is not None and case.is_scam for case in verdict_cases)
    verdict_legit = sum(case is not None and not case.is_scam for case in verdict_cases)

    assert len(verdict_cases) >= 5
    assert minimum_gaps
    # 固定 <= 1 是錯的期望：match/tactics 會先消耗 scam，且 mirror、難度與
    # 唯一性仍須成立；完整候選有時只能達到差距 2。正確性質是最終選到
    # 同一組規則允許的最小差距，而不是假設原始 10/5 題庫仍全可供 verdict。
    assert abs(verdict_scam - verdict_legit) == minimum_gaps[-1]


def test_deck_uses_current_user_level_for_difficulty(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    monkeypatch: Any,
) -> None:
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None
    original_xp = user.xp
    source_cases = list_published_for_quiz(db)
    scam = next(case for case in source_cases if case.is_scam)
    legit = next(case for case in source_cases if not case.is_scam)
    tags = ["time_pressure", "authority", "greed", "social_proof", "trust_building"]
    low_cases = [
        (scam if index % 2 == 0 else legit).model_copy(
            update={
                "id": 90_000 + index,
                "difficulty": 1,
                "mirror_of": None,
                "red_flags": [],
            }
        )
        for index in range(6)
    ]
    hard_cases = [
        scam.model_copy(
            update={
                "id": 91_000 + index,
                "fraud_type": f"type-{index % 5}",
                "difficulty": 3,
                "mirror_of": None,
                "red_flags": [
                    {"tag": tags[index % 5], "text": f"高難度例句 {index}-1"},
                    {
                        "tag": tags[(index + 1) % 5],
                        "text": f"高難度例句 {index}-2",
                    },
                ],
            }
        )
        for index in range(12)
    ]
    monkeypatch.setattr(
        quick_routes,
        "list_published_for_quiz",
        lambda _session: [*low_cases, *hard_cases],
    )

    try:
        user.xp = 0
        db.add(user)
        db.commit()
        session_id, items = _deal(client, normal_user_token_headers, size=5)
    finally:
        user.xp = original_xp
        db.add(user)
        db.commit()

    verdict_items = [item for item in items if item["type"] == "verdict"]
    tactics_items = [item for item in items if item["type"] == "tactics"]
    match_items = [item for item in items if item["type"] == "match"]
    assert all(item["difficulty"] <= 1 for item in verdict_items)
    assert tactics_items and all(item["difficulty"] == 3 for item in tactics_items)
    assert len(match_items) == 1
    hard_ids = {case.id for case in hard_cases}
    stored_match = next(
        item for item in _quiz(db, session_id).items if item["type"] == "match"
    )
    assert all(pair["case_id"] in hard_ids for pair in stored_match["pairs"])


def test_deck_logs_session_and_count_when_mirror_exclusion_is_relaxed(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    monkeypatch: Any,
    caplog: pytest.LogCaptureFixture,
) -> None:
    cases = list_published_for_quiz(db)
    scam = next(case for case in cases if case.is_scam)
    legit = next(case for case in cases if not case.is_scam).model_copy(
        update={"mirror_of": scam.id}
    )
    monkeypatch.setattr(quick_routes, "shuffle", lambda _items: None)
    monkeypatch.setattr(
        quick_routes, "list_published_for_quiz", lambda _session: [scam, legit]
    )

    with caplog.at_level(logging.WARNING, logger=quick_routes.__name__):
        session_id, items = _deal(client, normal_user_token_headers, size=2)

    assert len(items) == 2
    assert session_id in caplog.text
    assert "放寬鏡像排除 1 張" in caplog.text


def test_answer_verdict_keeps_existing_reveal(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    session_id, items = _deal(client, normal_user_token_headers, size=1)
    verdict = items[0]
    answer = _correct_answer(db, session_id, verdict)

    response = client.post(
        f"{settings.API_V1_STR}/quick/quiz/answer",
        headers=normal_user_token_headers,
        json={"session_id": session_id, **answer},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "verdict"
    assert data["correct"] is True
    assert isinstance(data["is_scam"], bool)
    assert data["red_flags"]
    assert data["provenance"]
    assert data["tag_details"] == []


def test_answer_wrong_scam_verdict_reveals_weakness_suggestions(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    session_id, items = _deal(client, normal_user_token_headers, size=10)
    verdict = next(
        item
        for item in items
        if item["type"] == "verdict"
        and _stored_item(db, session_id, item["item_id"])["is_scam"]
    )
    stored = _stored_item(db, session_id, verdict["item_id"])

    response = _submit_answer(
        client,
        normal_user_token_headers,
        session_id,
        {"item_id": verdict["item_id"], "guess_is_scam": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "verdict"
    assert data["correct"] is False
    assert data["is_scam"] is True
    _assert_weakness_details(data["tag_details"], set(stored["correct_tags"]))


def test_answer_tactics_reveals_exact_missed_and_extra_tags(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_cases = [
        case
        for case in list_published_for_quiz(db)
        if case.provenance == "pytest fixture"
        and (not case.is_scam or "greed" not in case_tags(case.red_flags))
    ]
    assert sum(case.is_scam for case in fixture_cases) >= 2
    assert sum(not case.is_scam for case in fixture_cases) >= 2
    monkeypatch.setattr(
        quick_routes, "list_published_for_quiz", lambda _session: fixture_cases.copy()
    )

    session_id, items = _deal(client, normal_user_token_headers, size=3)
    tactics = next(item for item in items if item["type"] == "tactics")
    correct = _correct_answer(db, session_id, tactics)["selected_tags"]
    selected = correct[1:] + ["greed"]

    response = client.post(
        f"{settings.API_V1_STR}/quick/quiz/answer",
        headers=normal_user_token_headers,
        json={
            "session_id": session_id,
            "item_id": tactics["item_id"],
            "selected_tags": selected,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "tactics"
    assert data["correct"] is False
    assert set(data["correct_tags"]) == set(correct)
    assert set(data["missed_tags"]) == {correct[0]}
    assert set(data["extra_tags"]) == {"greed"} - set(correct)
    _assert_weakness_details(
        data["tag_details"],
        set(data["correct_tags"] + data["missed_tags"] + data["extra_tags"]),
    )


def test_answer_match_reveals_each_pair_result(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    session_id, items = _deal(client, normal_user_token_headers, size=5)
    match = next(item for item in items if item["type"] == "match")
    pairs = _correct_answer(db, session_id, match)["pairs"]
    wrong_pair_id = next(iter(pairs))
    pairs[wrong_pair_id] = next(
        tag for tag in pairs.values() if tag != pairs[wrong_pair_id]
    )

    response = client.post(
        f"{settings.API_V1_STR}/quick/quiz/answer",
        headers=normal_user_token_headers,
        json={
            "session_id": session_id,
            "item_id": match["item_id"],
            "pairs": pairs,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "match"
    assert data["correct"] is False
    assert len(data["results"]) == 5
    result = next(row for row in data["results"] if row["pair_id"] == wrong_pair_id)
    assert result["correct"] is False
    _assert_weakness_details(data["tag_details"], {result["correct_tag"]})


def test_answer_requires_session_owner(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    session_id, items = _deal(client, normal_user_token_headers, size=1)
    response = client.post(
        f"{settings.API_V1_STR}/quick/quiz/answer",
        headers=superuser_token_headers,
        json={
            "session_id": session_id,
            "item_id": items[0]["item_id"],
            "guess_is_scam": True,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "not_your_quiz_session"


def test_answer_is_saved_and_second_attempt_cannot_replace_it(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    session_id, items = _deal(client, normal_user_token_headers, size=1)
    first_answer = _correct_answer(db, session_id, items[0])
    second_answer = {**first_answer, "guess_is_scam": not first_answer["guess_is_scam"]}

    first = _submit_answer(client, normal_user_token_headers, session_id, first_answer)
    second = _submit_answer(
        client, normal_user_token_headers, session_id, second_answer
    )

    assert first.status_code == 200
    assert second.status_code == 400
    assert second.json()["detail"]["code"] == "quiz_item_already_answered"
    quiz = _quiz(db, session_id)
    assert quiz.answers == {
        first_answer["item_id"]: {"guess_is_scam": first_answer["guess_is_scam"]}
    }
    completed = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": session_id},
    )
    assert completed.status_code == 200
    assert completed.json()["correct_count"] == 1


def test_complete_rewards_all_three_types_equally(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    session_id, items = _deal(client, normal_user_token_headers, size=5)
    answers = [_correct_answer(db, session_id, item) for item in items]
    for answer in answers:
        assert (
            _submit_answer(
                client, normal_user_token_headers, session_id, answer
            ).status_code
            == 200
        )
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None
    cash_before, xp_before = user.cash, user.xp

    response = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": session_id},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(items)
    assert data["correct_count"] == len(items)
    assert data["cash_earned"] == int(
        40 * len(items) * (1 + 0.1 * (data["best_streak"] // 3))
    )
    assert data["xp_earned"] == 20 * len(items)
    db.refresh(user)
    assert user.cash == cash_before + data["cash_earned"]
    assert user.xp == xp_before + data["xp_earned"]


def test_complete_counts_unanswered_items_as_wrong(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    session_id, items = _deal(client, normal_user_token_headers, size=3)
    answer = _correct_answer(db, session_id, items[0])
    assert (
        _submit_answer(
            client, normal_user_token_headers, session_id, answer
        ).status_code
        == 200
    )

    response = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": session_id},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert response.json()["correct_count"] == 1


def test_answer_after_completion_is_rejected(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    session_id, items = _deal(client, normal_user_token_headers, size=1)
    completed = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": session_id},
    )
    answer = _correct_answer(db, session_id, items[0])
    response = _submit_answer(client, normal_user_token_headers, session_id, answer)

    assert completed.status_code == 200
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "quiz_already_completed"


def test_complete_tactics_counts_only_missed_tags(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    session_id, items = _deal(client, normal_user_token_headers, size=3)
    tactics = next(item for item in items if item["type"] == "tactics")
    correct = _correct_answer(db, session_id, tactics)["selected_tags"]
    missed = correct[0]
    assert (
        _submit_answer(
            client,
            normal_user_token_headers,
            session_id,
            {"item_id": tactics["item_id"], "selected_tags": correct[1:]},
        ).status_code
        == 200
    )

    response = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": session_id},
    )

    assert response.status_code == 200
    assert response.json()["correct_count"] == 0
    assert response.json()["weakness_summary"] == [{"tag": missed, "count": 1}]


def test_complete_match_counts_each_incorrect_pair_tag(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    session_id, items = _deal(client, normal_user_token_headers, size=5)
    match = next(item for item in items if item["type"] == "match")
    pairs = _correct_answer(db, session_id, match)["pairs"]
    wrong_pair_id = next(iter(pairs))
    correct_tag = pairs[wrong_pair_id]
    pairs[wrong_pair_id] = next(tag for tag in pairs.values() if tag != correct_tag)
    assert (
        _submit_answer(
            client,
            normal_user_token_headers,
            session_id,
            {"item_id": match["item_id"], "pairs": pairs},
        ).status_code
        == 200
    )

    response = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": session_id},
    )

    assert response.status_code == 200
    assert response.json()["correct_count"] == 0
    assert response.json()["weakness_summary"] == [{"tag": correct_tag, "count": 1}]


def test_complete_match_uses_answers_frozen_at_deal_time(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    session_id, items = _deal(client, normal_user_token_headers, size=5)
    match = next(item for item in items if item["type"] == "match")
    stored = _stored_item(db, session_id, match["item_id"])
    answer = _correct_answer(db, session_id, match)
    selected_pair: dict[str, Any] | None = None
    original = None
    swap_index = -1
    for pair in stored["pairs"]:
        candidate = get_case(db, pair["case_id"])
        if candidate is None:
            continue
        swap_index = next(
            (
                index
                for index, flag in enumerate(candidate.red_flags)
                if flag.get("tag") != pair["tag"]
            ),
            -1,
        )
        if swap_index >= 0:
            selected_pair = pair
            original = candidate
            break
    assert selected_pair is not None
    assert original is not None
    case_id = selected_pair["case_id"]
    reordered = original.red_flags.copy()
    flag_index = selected_pair["flag_index"]
    reordered[flag_index], reordered[swap_index] = (
        reordered[swap_index],
        reordered[flag_index],
    )
    assert (
        _submit_answer(
            client, normal_user_token_headers, session_id, answer
        ).status_code
        == 200
    )

    try:
        db.execute(
            text(
                "UPDATE game_cases SET red_flags = CAST(:flags AS jsonb) WHERE id = :id"
            ),
            {"flags": json.dumps(reordered), "id": case_id},
        )
        db.commit()
        response = client.post(
            f"{settings.API_V1_STR}/quick/quiz/complete",
            headers=normal_user_token_headers,
            json={"session_id": session_id},
        )
    finally:
        db.execute(
            text(
                "UPDATE game_cases SET red_flags = CAST(:flags AS jsonb) WHERE id = :id"
            ),
            {"flags": json.dumps(original.red_flags), "id": case_id},
        )
        db.commit()

    assert response.status_code == 200
    assert response.json()["total"] == 5
    assert response.json()["correct_count"] == 1


def test_complete_counts_unavailable_db_case_as_wrong(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    session_id, items = _deal(client, normal_user_token_headers, size=1)
    verdict = items[0]
    stored = _stored_item(db, session_id, verdict["item_id"])
    answer = _correct_answer(db, session_id, verdict)
    assert (
        _submit_answer(
            client, normal_user_token_headers, session_id, answer
        ).status_code
        == 200
    )

    try:
        db.execute(
            text("UPDATE game_cases SET status = 'draft' WHERE id = :id"),
            {"id": stored["case_id"]},
        )
        db.commit()
        response = client.post(
            f"{settings.API_V1_STR}/quick/quiz/complete",
            headers=normal_user_token_headers,
            json={"session_id": session_id},
        )
    finally:
        db.execute(
            text("UPDATE game_cases SET status = 'published' WHERE id = :id"),
            {"id": stored["case_id"]},
        )
        db.commit()

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["correct_count"] == 0


def test_complete_counts_unscorable_item_as_wrong_and_logs_warning(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    session_id, items = _deal(client, normal_user_token_headers, size=1)
    answer = _correct_answer(db, session_id, items[0])
    assert (
        _submit_answer(
            client, normal_user_token_headers, session_id, answer
        ).status_code
        == 200
    )
    quiz = _quiz(db, session_id)
    quiz.items = [{"item_id": items[0]["item_id"], "type": "invalid"}]
    db.add(quiz)
    db.commit()

    with caplog.at_level(logging.WARNING, logger=quick_routes.__name__):
        response = client.post(
            f"{settings.API_V1_STR}/quick/quiz/complete",
            headers=normal_user_token_headers,
            json={"session_id": session_id},
        )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["correct_count"] == 0
    assert "quiz 題目無法評分，按答錯計入" in caplog.text


def test_complete_replay_rejected(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    session_id, items = _deal(client, normal_user_token_headers, size=1)
    first = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": session_id},
    )
    second = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": session_id},
    )

    assert first.status_code == 200
    assert second.status_code == 400
    assert second.json()["detail"]["code"] == "quiz_already_completed"


def test_complete_not_your_session(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    session_id, _ = _deal(client, normal_user_token_headers, size=1)
    response = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=superuser_token_headers,
        json={"session_id": session_id},
    )

    assert response.status_code == 403


def test_complete_bad_session_rejected(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    not_found = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": str(uuid.uuid4())},
    )
    malformed = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": "not-a-uuid"},
    )

    assert not_found.status_code == 404
    assert malformed.status_code == 404


@pytest.mark.parametrize("malformed_items", [None, [None], {"item_id": "bad"}])
def test_malformed_items_do_not_make_quiz_endpoints_crash(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    malformed_items: object,
) -> None:
    session_id, items = _deal(client, normal_user_token_headers, size=1)
    db.execute(
        text(
            "UPDATE quiz_session SET items = CAST(:items AS jsonb) "
            "WHERE id = :session_id"
        ),
        {"items": json.dumps(malformed_items), "session_id": uuid.UUID(session_id)},
    )
    db.commit()

    answer = _submit_answer(
        client,
        normal_user_token_headers,
        session_id,
        {"item_id": items[0]["item_id"], "guess_is_scam": True},
    )
    complete = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": session_id},
    )

    assert answer.status_code == 404
    assert complete.status_code == 200
    assert complete.json()["total"] == 0


def test_null_case_ids_returns_404_instead_of_500(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    session_id, items = _deal(client, normal_user_token_headers, size=1)
    db.execute(
        text(
            "UPDATE quiz_session SET case_ids = CAST('null' AS jsonb) "
            "WHERE id = :session_id"
        ),
        {"session_id": uuid.UUID(session_id)},
    )
    db.commit()

    response = _submit_answer(
        client,
        normal_user_token_headers,
        session_id,
        {"item_id": items[0]["item_id"], "guess_is_scam": True},
    )

    assert response.status_code == 404


@pytest.mark.parametrize("malformed_answers", [None, [None], "invalid"])
def test_malformed_answers_are_skipped_during_completion(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    malformed_answers: object,
) -> None:
    session_id, _ = _deal(client, normal_user_token_headers, size=1)
    db.execute(
        text(
            "UPDATE quiz_session SET answers = CAST(:answers AS jsonb) "
            "WHERE id = :session_id"
        ),
        {"answers": json.dumps(malformed_answers), "session_id": uuid.UUID(session_id)},
    )
    db.commit()

    response = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": session_id},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["correct_count"] == 0


@pytest.mark.parametrize(
    "oversized_answer",
    [
        {"item_id": "x" * 65},
        {"item_id": "item", "selected_tags": ["authority"] * 6},
        {"item_id": "item", "selected_tags": ["x" * 33]},
        {
            "item_id": "item",
            "pairs": {f"pair-{index}": "authority" for index in range(6)},
        },
        {"item_id": "item", "pairs": {"x" * 65: "authority"}},
        {"item_id": "item", "pairs": {"pair": "x" * 65}},
    ],
)
def test_answer_rejects_oversized_nested_payload_with_422(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    oversized_answer: dict[str, Any],
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/quick/quiz/answer",
        headers=normal_user_token_headers,
        json={"session_id": str(uuid.uuid4()), **oversized_answer},
    )

    assert response.status_code == 422


def test_each_tactics_item_shuffles_its_own_options(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    monkeypatch: Any,
) -> None:
    tactics_shuffle_calls = 0

    def deterministic_shuffle(values: list[Any]) -> None:
        nonlocal tactics_shuffle_calls
        if values and values[0].__class__.__name__ == "QuizTacticsOption":
            tactics_shuffle_calls += 1
            if tactics_shuffle_calls % 2 == 0:
                values.reverse()

    monkeypatch.setattr(quick_routes, "shuffle", deterministic_shuffle)

    _, items = _deal(client, normal_user_token_headers, size=5)
    tactics_items = [item for item in items if item["type"] == "tactics"]
    option_orders = [
        [option["tag"] for option in item["options"]] for item in tactics_items
    ]

    assert tactics_shuffle_calls == len(tactics_items) == 2
    assert option_orders[0] != option_orders[1]


def test_deck_omits_match_when_material_is_insufficient(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    monkeypatch: Any,
) -> None:
    cases = list_published_for_quiz(db)
    insufficient = [
        case.model_copy(
            update={
                "red_flags": [
                    {"tag": "time_pressure", "text": "限時處理"},
                    {"tag": "authority", "text": "主管要求"},
                ]
            }
        )
        for case in cases
    ]
    monkeypatch.setattr(
        quick_routes, "list_published_for_quiz", lambda _session: insufficient
    )

    _, items = _deal(client, normal_user_token_headers, size=5)

    assert len(items) == 5
    assert [item["type"] for item in items].count("match") == 0
    assert [item["type"] for item in items].count("verdict") == 3
    assert [item["type"] for item in items].count("tactics") == 2
