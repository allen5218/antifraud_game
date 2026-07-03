import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import FraudType, ScenarioSession, ScenarioStatus, User
from app.schemas import ScenarioReply


def _test_user(db: Session) -> User:
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user
    return user


def _make_session(db: Session, user: User, *, role: str, **overrides) -> ScenarioSession:
    values = dict(
        user_id=user.id,
        fraud_type="investment",
        persona_role=role,
        display_name="Kevin",
        avatar="📈",
        conversation_history=[
            {"role": "npc", "messages": ["你好!"], "decision_point": None}
        ],
        stake_loss=100,
        reward_win=50,
        reward_legit=30,
        penalty_misreport=10,
    )
    values.update(overrides)
    sc = ScenarioSession(**values)
    db.add(sc)
    db.commit()
    db.refresh(sc)
    return sc


async def _fake_reply(session, player_text, case=None):  # noqa: ANN001, ARG001
    return ScenarioReply(
        messages=["嗨嗨,考慮得怎麼樣?"],
        decision_point="先轉 5000 到合作券商鎖額度",
        tactics_used=["time_pressure", "bogus_tag"],
    )


def test_inbox_bootstraps_five_types_without_leaking_role(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/scenario/inbox", headers=normal_user_token_headers
    )
    assert r.status_code == 200
    items = r.json()
    assert {i["fraud_type"] for i in items} == {ft.value for ft in FraudType}
    for item in items:
        assert item["preview"]
        assert "persona_role" not in item
    assert "persona_role" not in r.text
    assert "tactics" not in r.text


def test_read_scenario_hides_truth(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    sc = _make_session(db, _test_user(db), role="scam")
    r = client.get(
        f"{settings.API_V1_STR}/scenario/{sc.id}", headers=normal_user_token_headers
    )
    assert r.status_code == 200
    data = r.json()
    assert data["max_turns"] == 10
    assert data["history"][0]["messages"] == ["你好!"]
    assert "persona_role" not in r.text
    assert "tactics_used" not in r.text


def test_message_appends_history_and_counts_turns(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str], monkeypatch
) -> None:
    monkeypatch.setattr("app.scenario.agent.generate_reply", _fake_reply)
    sc = _make_session(db, _test_user(db), role="scam")
    r = client.post(
        f"{settings.API_V1_STR}/scenario/{sc.id}/message",
        headers=normal_user_token_headers,
        json={"text": "為什麼要轉帳?"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["messages"] == ["嗨嗨,考慮得怎麼樣?"]
    assert data["decision_point"] == "先轉 5000 到合作券商鎖額度"
    assert data["turns_left"] == 9
    db.refresh(sc)
    assert sc.player_turns == 1
    assert sc.conversation_history[-2]["role"] == "player"
    assert sc.conversation_history[-1]["role"] == "npc"
    # 非法 tag 被過濾、合法 tag 被累積
    assert sc.tactics_seen == ["time_pressure"]


def test_message_turn_limit(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str], monkeypatch
) -> None:
    monkeypatch.setattr("app.scenario.agent.generate_reply", _fake_reply)
    sc = _make_session(db, _test_user(db), role="scam", player_turns=10)
    r = client.post(
        f"{settings.API_V1_STR}/scenario/{sc.id}/message",
        headers=normal_user_token_headers,
        json={"text": "hello"},
    )
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "turn_limit_reached"


def test_judge_report_scam_rewards(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    user = _test_user(db)
    # 共用測試使用者的 cash 可能被其他測試檔留在破產狀態(如 test_economy.py 最後一個
    # 測試刻意留 cash=-4400);此測試斷言 +50 後 triggers_forced_sell 為 False,
    # 需從已知的非負基準開始,避免跨檔案測試順序污染。
    user.cash = 0
    user.bankruptcy_pending = False
    db.add(user)
    db.commit()
    db.refresh(user)
    sc = _make_session(db, user, role="scam", tactics_seen=["greed"])
    cash_before, xp_before = user.cash, user.xp
    r = client.post(
        f"{settings.API_V1_STR}/scenario/{sc.id}/judge",
        headers=normal_user_token_headers,
        json={"action": "report"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["outcome"] == "win_report"
    assert data["true_role"] == "scam"
    assert data["cash_delta"] == 50
    assert data["xp_delta"] == 15
    assert data["flags"][0]["tag"] == "greed"
    assert data["triggers_forced_sell"] is False
    db.refresh(user)
    assert user.cash == cash_before + 50
    assert user.xp == xp_before + 15
    db.refresh(sc)
    assert sc.status == ScenarioStatus.COMPLETED
    assert sc.outcome == "win_report"


def test_judge_comply_scam_loses_and_can_trigger_forced_sell(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    user = _test_user(db)
    original_cash = user.cash
    sc = _make_session(db, user, role="scam", stake_loss=user.cash + 500)
    r = client.post(
        f"{settings.API_V1_STR}/scenario/{sc.id}/judge",
        headers=normal_user_token_headers,
        json={"action": "comply"},
    )
    data = r.json()
    assert data["outcome"] == "lose_scammed"
    assert data["new_cash"] == -500
    assert data["triggers_forced_sell"] is True
    db.refresh(user)
    assert user.bankruptcy_pending is True
    # 還原,避免影響其他測試
    user.cash = original_cash
    user.bankruptcy_pending = False
    db.add(user)
    db.commit()


def test_judge_misreport_legit_costs_penalty(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    user = _test_user(db)
    sc = _make_session(db, user, role="legit")
    cash_before, xp_before = user.cash, user.xp
    r = client.post(
        f"{settings.API_V1_STR}/scenario/{sc.id}/judge",
        headers=normal_user_token_headers,
        json={"action": "report"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["outcome"] == "lose_misreport"
    assert data["cash_delta"] == -10
    assert data["xp_delta"] == 0
    db.refresh(user)
    assert user.cash == cash_before - 10
    assert user.xp == xp_before


def test_judge_trust_legit_small_reward_with_signals(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    sc = _make_session(db, _test_user(db), role="legit")
    r = client.post(
        f"{settings.API_V1_STR}/scenario/{sc.id}/judge",
        headers=normal_user_token_headers,
        json={"action": "comply"},
    )
    data = r.json()
    assert data["outcome"] == "win_trust"
    assert data["cash_delta"] == 30
    assert all(f["tag"] is None for f in data["flags"])
    assert len(data["flags"]) >= 2


def test_judge_twice_rejected(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    sc = _make_session(db, _test_user(db), role="legit")
    first = client.post(
        f"{settings.API_V1_STR}/scenario/{sc.id}/judge",
        headers=normal_user_token_headers,
        json={"action": "report"},
    )
    assert first.status_code == 200
    second = client.post(
        f"{settings.API_V1_STR}/scenario/{sc.id}/judge",
        headers=normal_user_token_headers,
        json={"action": "report"},
    )
    assert second.status_code == 400


def test_new_scenario_daily_limit(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    user = _test_user(db)
    # 先把 romance 的 active 場清掉,再塞 3 場今天已完成
    for s in db.exec(
        select(ScenarioSession).where(
            ScenarioSession.user_id == user.id,
            ScenarioSession.fraud_type == "romance",
        )
    ).all():
        db.delete(s)
    db.commit()
    for _ in range(3):
        _make_session(
            db, user, role="scam", fraud_type="romance",
            status=ScenarioStatus.COMPLETED, outcome="win_report",
            completed_at=datetime.now(timezone.utc),
        )
    r = client.post(
        f"{settings.API_V1_STR}/scenario/new",
        headers=normal_user_token_headers,
        json={"fraud_type": "romance"},
    )
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "daily_limit_reached"


def test_not_your_scenario(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    sc = _make_session(db, _test_user(db), role="scam")
    r = client.get(
        f"{settings.API_V1_STR}/scenario/{sc.id}", headers=superuser_token_headers
    )
    assert r.status_code == 403


def test_scenario_not_found(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/scenario/{uuid.uuid4()}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404


def test_bootstrap_fills_case_id(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    # 共用 DB 可能殘留 case_id 欄位之前建立的舊場;先清空強迫 bootstrap
    user = _test_user(db)
    for s in db.exec(
        select(ScenarioSession).where(ScenarioSession.user_id == user.id)
    ).all():
        db.delete(s)
    db.commit()
    r = client.get(f"{settings.API_V1_STR}/scenario/inbox", headers=normal_user_token_headers)
    assert r.status_code == 200
    ids = [i["id"] for i in r.json()]
    sessions = [db.get(ScenarioSession, uuid.UUID(i)) for i in ids]
    # 40 筆 published 覆蓋全部 5 類 × 兩種 stance → bootstrap 場必有 case_id
    assert all(s is not None and s.case_id is not None for s in sessions)
    # case 的 stance 必須與 persona_role 一致
    from app.core.cases import get_case
    for s in sessions:
        assert s is not None and s.case_id is not None
        case = get_case(db, s.case_id)
        assert case is not None and case.is_scam == (s.persona_role == "scam")


def test_judge_returns_case_provenance(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    from app.core.cases import pick_case
    case = pick_case(db, fraud_type="investment", is_scam=True)
    assert case is not None
    sc = _make_session(db, _test_user(db), role="scam", case_id=case.id)
    r = client.post(
        f"{settings.API_V1_STR}/scenario/{sc.id}/judge",
        headers=normal_user_token_headers,
        json={"action": "report"},
    )
    assert r.status_code == 200
    assert r.json()["case_provenance"] == case.provenance


def test_judge_without_case_provenance_null(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    sc = _make_session(db, _test_user(db), role="legit")
    r = client.post(
        f"{settings.API_V1_STR}/scenario/{sc.id}/judge",
        headers=normal_user_token_headers,
        json={"action": "comply"},
    )
    assert r.json()["case_provenance"] is None
