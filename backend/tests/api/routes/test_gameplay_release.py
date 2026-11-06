"""使用真實 PostgreSQL 驗證獎勵閉環與失敗、重送、並行情境。"""

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.api.routes import quick
from app.core.config import settings
from app.core.db import engine
from app.models import QuizSession, User
from app.progression.collections import collection_summary
from app.progression.models import (
    CompetitionEntry,
    CompetitionSeason,
    PlayerCollectible,
    PlayerEquipment,
    PlayerGrowth,
    PlayerUnlock,
    ProgressionLedger,
    RewardReceipt,
    SeasonAward,
)
from app.progression.seasons import close_expired_seasons
from app.progression.service import (
    create_reward_context,
    get_or_create_growth,
    get_player_blueprints,
    get_utc_now,
    settle_reward,
)
from tests.api.routes.test_quick_quiz import _correct_answer, _deal, _submit_answer
from tests.api.routes.test_quick_swipe import _answer as swipe_answer
from tests.api.routes.test_quick_swipe import _deal as swipe_deal
from tests.api.routes.test_quick_swipe import _truth as swipe_truth
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email

API = settings.API_V1_STR


def player(client: TestClient, db: Session) -> tuple[dict[str, str], User]:
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    user = db.exec(select(User).where(User.email == email)).one()
    get_or_create_growth(db, user.id)
    db.commit()
    return headers, user


def fund(db: Session, user: User, cash: int = 100000, energy: int = 10000) -> None:
    from app.economy.service import adjust_cash

    adjust_cash(user, cash - user.cash, reason="test_fixture")
    growth = get_or_create_growth(db, user.id)
    growth.forge_energy = energy
    db.add(user)
    db.add(growth)
    db.commit()


def test_pet_growth_idempotency_and_frozen_multiplier(
    client: TestClient, db: Session
) -> None:
    headers, user = player(client, db)
    fund(db, user)
    summary = client.get(f"{API}/collections/me", headers=headers).json()
    pet = next(a for a in summary["assets"] if a["kind"] == "pet")
    request = {"key": str(uuid.uuid4()), "expected_level": 0}
    path = f"{API}/collections/pet/{pet['target_id']}/upgrade"
    first = client.post(path, headers=headers, json=request)
    assert first.status_code == 200
    repeat = client.post(path, headers=headers, json=request)
    assert repeat.status_code == 200
    assert (
        next(a for a in repeat.json()["assets"] if a["target_id"] == pet["target_id"])[
            "level"
        ]
        == 1
    )
    db.refresh(user)
    assert user.cash == 99500
    growth = db.get(PlayerGrowth, user.id)
    db.refresh(growth)
    assert growth.forge_energy == 9990
    assert growth.lifetime_cash == 0
    context = create_reward_context(db, user.id, "quiz", uuid.uuid4())
    db.commit()
    second = client.post(
        path, headers=headers, json={"key": str(uuid.uuid4()), "expected_level": 1}
    )
    assert second.status_code == 200
    from app.economy.service import adjust_cash

    db.refresh(user)
    adjust_cash(user, 100, reason="test_base_reward")
    receipt, growth = settle_reward(
        db, user, context, base_cash=100, base_xp=100, reason="test_frozen_pet"
    )
    db.commit()
    assert receipt.factors["cash"] == "1.01"
    assert receipt.final_rewards["cash_total"] == "101"
    assert growth.lifetime_cash == 101
    actual = client.get(f"{API}/progression/me", headers=headers).json()
    assert actual["factors"]["cash"] == "1.02"


def test_collection_visibility_ownership_and_no_private_account_fields(
    client: TestClient, db: Session
) -> None:
    headers, user = player(client, db)
    other_headers, _other = player(client, db)
    for key in ("visible-trophy", "hidden-trophy"):
        db.add(
            PlayerCollectible(user_id=user.id, item_key=key, kind="trophy", name=key)
        )
    db.add(PlayerUnlock(user_id=user.id, unlock_key="title_test", value="測試冠軍"))
    db.commit()
    assert (
        client.post(
            f"{API}/collections/display/showcase",
            headers=other_headers,
            json={"key": "visible-trophy"},
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"{API}/collections/display/showcase",
            headers=headers,
            json={"key": "visible-trophy"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"{API}/collections/display/title",
            headers=headers,
            json={"key": "title_test"},
        ).status_code
        == 200
    )
    public = client.get(f"{API}/players/{user.id}/showcase")
    assert public.status_code == 200
    assert public.json()["title"] == "測試冠軍"
    assert [c["item_key"] for c in public.json()["collectibles"]] == ["visible-trophy"]
    assert "hidden-trophy" not in public.text
    assert user.email not in public.text
    assert "hashed_password" not in public.text


def test_presets_are_storage_not_extra_active_loadouts(
    client: TestClient, db: Session
) -> None:
    headers, user = player(client, db)
    fund(db, user)
    catalog = client.get(f"{API}/equipment", headers=headers).json()
    starter = catalog["items"][0]["id"]
    unlocked = client.post(f"{API}/progression/unlocks/growth_lens", headers=headers)
    assert unlocked.status_code == 200
    growth_tool = unlocked.json()["item_id"]
    for position, item in enumerate((starter, growth_tool)):
        assert (
            client.put(
                f"{API}/collections/presets/{position}",
                headers=headers,
                json={"name": f"套裝 {position}", "item_ids": [item]},
            ).status_code
            == 200
        )
    assert client.get(f"{API}/equipment", headers=headers).json()["equipped_count"] == 0
    assert (
        client.post(f"{API}/collections/presets/1/apply", headers=headers).status_code
        == 200
    )
    equipment = client.get(f"{API}/equipment", headers=headers).json()
    assert [i["id"] for i in equipment["items"] if i["is_equipped"]] == [growth_tool]
    assert (
        client.post(f"{API}/collections/presets/0/apply", headers=headers).status_code
        == 200
    )
    equipment = client.get(f"{API}/equipment", headers=headers).json()
    assert [i["id"] for i in equipment["items"] if i["is_equipped"]] == [starter]
    assert (
        client.put(
            f"{API}/collections/presets/2",
            headers=headers,
            json={"name": "越界", "item_ids": []},
        ).status_code
        == 400
    )


def test_actual_quiz_failure_rolls_back_real_settlement(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers, user = player(client, db)
    session_id, items = _deal(client, headers)
    for item in items:
        assert (
            _submit_answer(
                client, headers, session_id, _correct_answer(db, session_id, item)
            ).status_code
            == 200
        )
    db.refresh(user)
    before = (user.cash, user.xp)
    uid = user.id
    db.commit()
    real_settle = quick.settle_reward

    def fail_after_settlement(*args: Any, **kwargs: Any) -> Any:
        real_settle(*args, **kwargs)
        raise RuntimeError("failure-after-real-settlement")

    with monkeypatch.context() as patch:
        patch.setattr(quick, "settle_reward", fail_after_settlement)
        with pytest.raises(RuntimeError, match="failure-after-real-settlement"):
            client.post(
                f"{API}/quick/quiz/complete",
                headers=headers,
                json={"session_id": session_id},
            )
    with Session(engine) as check:
        stored_user = check.get(User, uid)
        assert (stored_user.cash, stored_user.xp) == before
        assert check.get(QuizSession, uuid.UUID(session_id)).completed is False
        assert not check.exec(
            select(RewardReceipt).where(RewardReceipt.user_id == uid)
        ).all()
        assert not check.exec(
            select(ProgressionLedger).where(ProgressionLedger.user_id == uid)
        ).all()
        g = check.get(PlayerGrowth, uid)
        assert (g.growth_xp, g.forge_energy, g.lifetime_cash) == (0, 0, 0)
    success = client.post(
        f"{API}/quick/quiz/complete", headers=headers, json={"session_id": session_id}
    )
    assert success.status_code == 200
    db.refresh(user)
    assert user.cash - before[0] == int(success.json()["cash_earned"])


def test_twenty_concurrent_swipe_completions_pay_once(
    client: TestClient, db: Session
) -> None:
    headers, user = player(client, db)
    deck = swipe_deal(client, headers, size=1)
    card = deck["cards"][0]
    assert (
        swipe_answer(
            client,
            headers,
            deck["session_id"],
            card["id"],
            swipe_truth(db, card["id"]).is_scam,
        ).status_code
        == 200
    )
    uid = user.id
    db.commit()

    def finish(_index: int) -> Any:
        response = client.post(
            f"{API}/quick/swipe/complete",
            headers=headers,
            json={"session_id": deck["session_id"]},
        )
        assert response.status_code == 200
        return response.json()

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(finish, range(20)))
    assert all(result == results[0] for result in results)
    with Session(engine) as check:
        receipt = check.exec(
            select(RewardReceipt).where(RewardReceipt.user_id == uid)
        ).one()
        growth = check.get(PlayerGrowth, uid)
        assert growth.growth_xp == int(receipt.final_rewards["growth_xp"])
        assert growth.forge_energy == int(receipt.final_rewards["forge_energy"])
        assert check.get(User, uid).cash == 1000 + int(
            receipt.final_rewards["cash_total"]
        )


def test_legacy_client_cannot_spend_an_unsafe_balance(
    client: TestClient, db: Session
) -> None:
    headers, user = player(client, db)
    fund(db, user, cash=10**77 + 123456789)
    api = client.get(f"{API}/economy/me", headers=headers)
    assert api.status_code == 200
    assert api.json()["cash"] == str(10**77 + 123456789)
    legacy = client.get(
        f"{API}/economy/me", headers={**headers, "X-ScamGym-Client-Version": "1"}
    )
    assert legacy.status_code == 426
    assert legacy.json()["detail"]["code"] == "client_upgrade_required"


def test_season_concurrent_close_and_champion_tool_survive_new_period(
    client: TestClient, db: Session
) -> None:
    headers, user = player(client, db)
    now = get_utc_now()
    season = CompetitionSeason(
        name="並行關帳驗證",
        starts_at=now - timedelta(days=15),
        ends_at=now - timedelta(minutes=20),
        state="open",
    )
    db.add(season)
    db.commit()
    sid, uid = season.id, user.id
    for day in range(5):
        db.add(
            CompetitionEntry(
                season_id=sid,
                user_id=uid,
                day=f"2026-10-{day + 1:02d}",
                daily_source_id=uuid.uuid4(),
                correct=10,
                total=10,
                duration=60,
                power_points=1200,
            )
        )
    db.commit()

    def close(_index: int) -> list[uuid.UUID]:
        with Session(engine) as worker:
            return close_expired_seasons(worker, now=now)

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(close, range(4)))
    with Session(engine) as check:
        assert (
            check.exec(
                select(SeasonAward).where(
                    SeasonAward.season_id == sid, SeasonAward.user_id == uid
                )
            )
            .one()
            .tier
            == "tier_1"
        )
        assert get_player_blueprints(check, uid) == 10
        assert get_player_blueprints(check, uid, key="breakthrough_blueprints") == 2
        assert (
            len(
                check.exec(
                    select(PlayerCollectible).where(PlayerCollectible.user_id == uid)
                ).all()
            )
            == 4
        )
    for _ in range(2):
        response = client.post(
            f"{API}/seasons/{sid}/awards/tool",
            headers=headers,
            json={"family": "growth_lens"},
        )
        assert response.status_code == 200
    with Session(engine) as check:
        tools = check.exec(
            select(PlayerEquipment).where(
                PlayerEquipment.user_id == uid, PlayerEquipment.rank == 6
            )
        ).all()
        assert len(tools) == 1
        assert tools[0].rank_cap == 6
        saved = collection_summary(check, uid)
        assert len(saved.collectibles) == 4
    client.get(f"{API}/seasons/current", headers=headers).raise_for_status()
    after = client.get(f"{API}/collections/me", headers=headers).json()
    assert len(after["collectibles"]) == 4
    assert after["tool_choices"] == []
