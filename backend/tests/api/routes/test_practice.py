"""練習重點的整合測試:四種玩法都寫進共用作答紀錄,紀錄會改變發牌與收件匣。

分析器在測試裡一律關閉(tests/conftest.py),練習重點走規則版;
每個測試結束後清掉作答紀錄與練習重點(tests/api/conftest.py)。
"""

import asyncio
from collections import Counter

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, col, select

from app.core.config import settings
from app.models import (
    PracticeAnswer,
    PracticeProfile,
    ScenarioSession,
    SwipeCard,
    User,
)
from app.practice.profile import PracticePlan
from app.practice.service import (
    recent_answers,
    record_answers,
    refresh_profile,
    save_profile,
)

API = settings.API_V1_STR


def _user(db: Session, email: str) -> User:
    user = db.exec(select(User).where(User.email == email)).one()
    return user


def _answers(db: Session, user: User, mode: str | None = None) -> list[PracticeAnswer]:
    db.expire_all()
    stmt = select(PracticeAnswer).where(PracticeAnswer.user_id == user.id)
    if mode:
        stmt = stmt.where(PracticeAnswer.mode == mode)
    return list(db.exec(stmt).all())


def _make_romance_the_weak_spot(db: Session, user: User) -> None:
    """假交友答錯 6 題,其他類各答對 4 題,再跑一次分析。"""
    rows = [("romance", False, ["trust_building"])] * 6
    rows += [
        (ft, True, [])
        for ft in ("investment", "shopping", "fake-sale", "atm")
        for _ in range(4)
    ]
    record_answers(db, user.id, "quiz", rows)
    db.commit()
    asyncio.run(refresh_profile(user.id))


def test_profile_without_any_record(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{API}/practice/profile", headers=superuser_token_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["source"] == "none"
    assert data["focus_type"] is None
    assert "前測" in data["note"]


def test_profile_follows_the_answer_log(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    _make_romance_the_weak_spot(db, _user(db, settings.FIRST_SUPERUSER))

    data = client.get(f"{API}/practice/profile", headers=superuser_token_headers).json()
    assert data["focus_type"] == "romance"
    assert data["focus_label"] == "假交友"
    assert data["source"] == "rule"
    assert "假交友" in data["note"]
    assert max(data["weights"], key=data["weights"].__getitem__) == "romance"


def test_weak_spot_changes_swipe_inbox_and_quiz(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    _make_romance_the_weak_spot(db, _user(db, settings.FIRST_SUPERUSER))

    # 滑卡:種子題庫每類 6 張,比例給 romance 最高(上限一半),抽出來的比例要明顯高於 1/5
    counts: Counter[str] = Counter()
    for _ in range(10):
        deck = client.get(
            f"{API}/quick/swipe/deck?size=10", headers=superuser_token_headers
        )
        counts.update(card["fraud_type"] for card in deck.json())
    assert counts["romance"] / sum(counts.values()) > 0.35, counts

    # 收件匣:romance 排第一
    inbox = client.get(f"{API}/scenario/inbox", headers=superuser_token_headers).json()
    assert inbox[0]["fraud_type"] == "romance"

    # 題組:查證題從 romance 抽
    deck = client.get(
        f"{API}/quick/quiz/deck?size=5", headers=superuser_token_headers
    ).json()
    verification = [i for i in deck["items"] if i["type"] == "verification"]
    assert [i["fraud_type"] for i in verification] == ["romance"]


def test_swipe_complete_records_every_card(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    user = _user(db, settings.EMAIL_TEST_USER)
    cards = db.exec(select(SwipeCard).where(col(SwipeCard.is_scam)).limit(3)).all()
    r = client.post(
        f"{API}/quick/swipe/complete",
        headers=normal_user_token_headers,
        json={
            "answers": [{"card_id": str(c.id), "guess_is_scam": False} for c in cards]
        },
    )
    assert r.status_code == 200

    logged = _answers(db, user, "swipe")
    assert len(logged) == 3
    assert all(not a.correct for a in logged)
    # 把詐騙判成正常 → 那張卡的話術算漏掉的
    by_type = {c.fraud_type for c in cards}
    assert {a.fraud_type for a in logged} == by_type
    assert all(a.missed_tags for a in logged)


def test_settlement_releases_db_connection_before_background_work(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """背景分析跑的時候,結算請求的 session 不能還借著一條連線(理由見 queue_refresh)。"""
    from app.core.db import engine
    from app.practice import service

    checked_out: list[int] = []

    async def fake_refresh(_user_id: object) -> None:
        checked_out.append(engine.pool.checkedout())

    monkeypatch.setattr(service, "refresh_profile", fake_refresh)
    cards = db.exec(select(SwipeCard).limit(2)).all()
    answers = [{"card_id": str(c.id), "guess_is_scam": True} for c in cards]
    db.commit()  # 測試自己的 session 先放掉連線(之後不再讀 ORM 屬性),才量得準
    before = engine.pool.checkedout()
    r = client.post(
        f"{API}/quick/swipe/complete",
        headers=normal_user_token_headers,
        json={"answers": answers},
    )
    assert r.status_code == 200
    assert checked_out == [before]


def test_quiz_complete_records_answered_items(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    user = _user(db, settings.FIRST_SUPERUSER)
    deck = client.get(
        f"{API}/quick/quiz/deck?size=3", headers=superuser_token_headers
    ).json()
    verdicts = [i for i in deck["items"] if i["type"] == "verdict"]
    assert verdicts
    for item in verdicts:
        r = client.post(
            f"{API}/quick/quiz/answer",
            headers=superuser_token_headers,
            json={
                "session_id": deck["session_id"],
                "item_id": item["item_id"],
                "guess_is_scam": True,
            },
        )
        assert r.status_code == 200
    r = client.post(
        f"{API}/quick/quiz/complete",
        headers=superuser_token_headers,
        json={"session_id": deck["session_id"]},
    )
    assert r.status_code == 200

    logged = _answers(db, user, "quiz")
    # 只記有作答的題目,類型取自題目本身
    assert len(logged) == len(verdicts)
    assert sorted(a.fraud_type for a in logged) == sorted(
        i["fraud_type"] for i in verdicts
    )


def test_scenario_judge_records_the_verdict(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    user = _user(db, settings.EMAIL_TEST_USER)
    sc = ScenarioSession(
        user_id=user.id,
        fraud_type="atm",
        persona_role="scam",
        display_name="客服",
        avatar="support",
        conversation_history=[
            {"role": "npc", "messages": ["您好"], "decision_point": None}
        ],
        tactics_seen=["authority", "time_pressure"],
        stake_loss=100,
        reward_win=50,
        reward_legit=30,
        penalty_misreport=10,
    )
    db.add(sc)
    db.commit()

    r = client.post(
        f"{API}/scenario/{sc.id}/judge",
        headers=normal_user_token_headers,
        json={"action": "comply"},
    )
    assert r.status_code == 200

    logged = _answers(db, user, "scenario")
    assert len(logged) == 1
    assert logged[0].fraud_type == "atm"
    assert logged[0].correct is False
    # 被騙了:對方用過的話術算漏掉的
    assert set(logged[0].missed_tags) == {"authority", "time_pressure"}


def test_refresh_needs_enough_answers(db: Session) -> None:
    user = _user(db, settings.FIRST_SUPERUSER)
    record_answers(db, user.id, "quiz", [("romance", False, [])] * 2)
    db.commit()
    asyncio.run(refresh_profile(user.id))
    db.expire_all()
    assert db.get(PracticeProfile, user.id) is None


def test_stale_analysis_does_not_overwrite_newer_answers(db: Session) -> None:
    """先開始的分析晚回來:讀完紀錄之後又有新作答,這份舊結果不能存。"""
    user = _user(db, settings.FIRST_SUPERUSER)
    record_answers(db, user.id, "quiz", [("romance", False, [])] * 6)
    db.commit()
    answers, total = recent_answers(db, user.id)
    assert len(answers) == 6 and total == 6

    record_answers(db, user.id, "swipe", [("atm", False, [])])
    db.commit()
    stale = PracticePlan({"romance": 1.0}, "romance", "舊的", "rule")
    assert save_profile(db, user.id, stale, len(answers), answers_total=total) is False
    db.commit()
    db.expire_all()
    assert db.get(PracticeProfile, user.id) is None

    answers, total = recent_answers(db, user.id)
    fresh = PracticePlan({"romance": 1.0}, "romance", "新的", "rule")
    assert save_profile(db, user.id, fresh, len(answers), answers_total=total) is True
    db.commit()
    db.expire_all()
    profile = db.get(PracticeProfile, user.id)
    assert profile is not None and profile.note == "新的"
