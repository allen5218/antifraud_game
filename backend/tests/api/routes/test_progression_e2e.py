import uuid
from datetime import timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import QuizSession, User
from app.progression.config import CONFIG_VERSION, FAMILY_GROWTH_LENS, FAMILY_SAVE_VAULT
from app.progression.models import (
    CompetitionEntry,
    CompetitionSeason,
)
from app.progression.seasons import (
    close_expired_seasons,
    get_current_season,
    record_daily_competition_entry,
)
from app.progression.service import (
    create_reward_context,
    get_player_blueprints,
    get_utc_now,
    settle_reward,
)
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email


def test_full_multiplier_progression_lifecycle(client: TestClient, db: Session) -> None:
    """完整全流程驗證：
    新玩家取得工具 → 裝備 → 獎勵增加 → 強化／解鎖 → 入榜 → 關帳領獎 → 換期保留。
    """
    # 1. 建立獨立全新玩家
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    user = db.exec(select(User).where(User.email == email)).first()
    assert user is not None

    # 2. 查進度：新玩家自動初始化初始工具，且 active_slots = 0, max_active_slots = 2
    r_prog = client.get(f"{settings.API_V1_STR}/progression/me", headers=headers)
    assert r_prog.status_code == 200
    prog_data = r_prog.json()
    assert prog_data["core_level"] == 0
    assert prog_data["active_slots"] == 0
    assert prog_data["max_active_slots"] == 2
    assert prog_data["has_sixth_slot_license"] is False

    # 3. 查裝備目錄：擁有 1 件初始儲金保險箱 (save_vault, rank 1)
    r_eq = client.get(f"{settings.API_V1_STR}/equipment", headers=headers)
    assert r_eq.status_code == 200
    eq_data = r_eq.json()
    items = eq_data["items"]
    assert len(items) >= 1
    starter = items[0]
    assert starter["family"] == FAMILY_SAVE_VAULT
    assert starter["is_equipped"] is False

    # 4. 裝備到第 0 槽
    r_loadout = client.put(
        f"{settings.API_V1_STR}/equipment/loadout",
        headers=headers,
        json={"items": [{"slot_index": 0, "item_id": starter["id"]}]},
    )
    assert r_loadout.status_code == 200
    assert r_loadout.json()["equipped_count"] == 1

    # 再次檢查進度：active_slots 變為 1
    r_prog2 = client.get(f"{settings.API_V1_STR}/progression/me", headers=headers)
    assert r_prog2.json()["active_slots"] == 1

    # 5. 獎勵結算增加 (帶入倍率結算)
    context = create_reward_context(db, user.id, "quiz", uuid.uuid4())
    cash_before = user.cash
    receipt, growth = settle_reward(
        db,
        user,
        context,
        base_cash=200,
        base_xp=100,
        reason="quiz_test",
        best_streak=5,
    )
    db.commit()
    db.refresh(user)

    # 驗證收據與加成
    assert receipt.id is not None
    assert Decimal(receipt.factors["cash"]) > Decimal("1.0")
    assert user.cash > cash_before
    assert growth.growth_xp > 0

    # 6. 強化裝備與消耗能量解鎖新工具家族
    # 給予金錢與能量
    user.cash = 10000
    growth.forge_energy = 500
    db.add(user)
    db.add(growth)
    db.commit()

    # 升級裝備 (rank 1 -> 2)
    r_up = client.post(
        f"{settings.API_V1_STR}/equipment/{starter['id']}/upgrade",
        headers=headers,
    )
    assert r_up.status_code == 200
    assert r_up.json()["rank"] == 2

    # 解鎖新家族 growth_lens
    r_unlock = client.post(
        f"{settings.API_V1_STR}/progression/unlocks/growth_lens",
        headers=headers,
    )
    assert r_unlock.status_code == 200
    assert r_unlock.json()["unlocked"] == "growth_lens"

    # 7. 參與賽季每日競技並入榜
    season = get_current_season(db)
    daily_entry = record_daily_competition_entry(
        db,
        user.id,
        QuizSession(
            user_id=user.id,
            daily_date=season.starts_at.date() + timedelta(days=1),
            case_ids=[],
            items=[],
        ),
        context,
        correct=10,
        total=10,
        duration=25,
    )
    db.commit()
    assert daily_entry is not None

    # 8. 賽季關帳領獎
    # 建立過期賽季與成績以測試關帳發獎
    past_season = CompetitionSeason(
        name="即將結算賽季",
        starts_at=get_utc_now() - timedelta(days=15),
        ends_at=get_utc_now() - timedelta(minutes=20),
        config_version=CONFIG_VERSION,
        award_version="award-v1",
        state="open",
    )
    db.add(past_season)
    db.commit()
    db.refresh(past_season)

    # 補足 5 天競技成績以獲得資格
    for d in range(1, 6):
        db.add(
            CompetitionEntry(
                season_id=past_season.id,
                user_id=user.id,
                day=f"2026-10-1{d}",
                daily_source_id=uuid.uuid4(),
                correct=10,
                total=10,
                duration=20,
                power_points=1500,
            )
        )
    db.commit()

    bp_before = get_player_blueprints(db, user.id)
    closed = close_expired_seasons(db, now=get_utc_now())
    assert past_season.id in closed

    # 領取賽季獎勵
    r_award = client.get(
        f"{settings.API_V1_STR}/seasons/{past_season.id}/awards/me",
        headers=headers,
    )
    assert r_award.status_code == 200
    award_data = r_award.json()
    assert award_data["tier"] == "tier_1"
    assert award_data["blueprints_awarded"] == 10
    assert get_player_blueprints(db, user.id) == bp_before + 10

    # 9. 換期保留：新賽季中玩家的工具、等級、解鎖狀態均完整保留
    new_season = get_current_season(db)
    assert new_season.id != past_season.id

    r_prog_final = client.get(f"{settings.API_V1_STR}/progression/me", headers=headers)
    assert r_prog_final.status_code == 200
    final_data = r_prog_final.json()
    # 裝備維持 1 件生效
    assert final_data["active_slots"] == 1
    # 圖紙碎片完整保留
    assert final_data["blueprint_fragments"] == bp_before + 10

    # 檢查背包工具與解鎖工具依然保留
    r_eq_final = client.get(f"{settings.API_V1_STR}/equipment", headers=headers)
    assert r_eq_final.status_code == 200
    final_items = r_eq_final.json()["items"]
    # 初始升級過的工具 (rank 2) 仍在，且新解鎖的 growth_lens 也已在裝備庫中
    families = {i["family"]: i for i in final_items}
    assert FAMILY_SAVE_VAULT in families
    assert families[FAMILY_SAVE_VAULT]["rank"] == 2
    assert FAMILY_GROWTH_LENS in families
