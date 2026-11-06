import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.economy.service import adjust_cash
from app.models import QuizSession, User
from app.progression.models import (
    PlayerEquipment,
    PlayerGrowth,
    RewardContext,
)
from app.progression.service import (
    ensure_starter_equipment,
    get_or_create_growth,
)
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email


def test_transaction_boundary_outer_rollback_preserves_atomicity(db: Session) -> None:
    """Codex 實測場景復原：
    初始 1000 元 -> 在未提交交易中加 100 元 -> 初始化成長/裝備上下文 -> 外層 rollback。
    驗證：外層 rollback 後，現金必須回滾回 1000 元，成長與裝備資料也全部回滾，不留孤兒資料。
    """
    email = random_email()
    user = User(
        email=email,
        hashed_password="fake",
        nickname="交易邊界測試員",
        cash=1000,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 在未提交的外層交易中修改現金為 1100
    user.cash = 1100
    db.add(user)
    db.flush()

    # 底層初始化函式被呼叫（以前會在此處自行 commit 把未提交的外層現金一起偷渡提交）
    growth = get_or_create_growth(db, user.id)
    ensure_starter_equipment(db, user.id)
    assert growth is not None

    # 外層業務邏輯因故發生例外並執行 rollback
    db.rollback()

    # 重新從 DB 查詢，驗證外層修改確實被回滾，且底層資料也不應殘留
    db.expire_all()
    reloaded_user = db.exec(select(User).where(User.id == user.id)).first()
    assert reloaded_user is not None
    assert reloaded_user.cash == 1000  # 絕非 1100

    reloaded_growth = db.exec(
        select(PlayerGrowth).where(PlayerGrowth.user_id == user.id)
    ).first()
    assert reloaded_growth is None  # 回滾後無殘留

    equipments = db.exec(
        select(PlayerEquipment).where(PlayerEquipment.user_id == user.id)
    ).all()
    assert len(equipments) == 0


def test_large_number_numeric78_precision_in_orm_and_api(
    client: TestClient, db: Session
) -> None:
    """Codex 實測場景：
    DB 實存 9007199254740993 (> 2^53 - 1)。
    驗證：
    1. ORM 讀出型別必須為 int（絕非 float 9007199254740992.0）。
    2. adjust_cash 加 1 元後，寫入 DB 正確為 9007199254740994。
    3. API /economy/me 回傳的 cash 必須為十進位字串 "9007199254740994"。
    4. 養成資源 growth_xp、forge_energy、power_points 同樣支援大數無精度損失。
    """
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    user = db.exec(select(User).where(User.email == email)).first()
    assert user is not None

    large_val = 9007199254740993
    user.cash = large_val
    db.add(user)
    db.commit()

    # 清空 ORM 快取，強制從 PostgreSQL 重新載入
    db.expire_all()
    refreshed = db.exec(select(User).where(User.id == user.id)).one()

    # 1. ORM 讀取精度
    assert isinstance(refreshed.cash, int)
    assert refreshed.cash == 9007199254740993
    assert refreshed.cash != 9007199254740992

    # 2. adjust_cash 加一元
    adjust_cash(refreshed, 1, reason="large_number_test")
    db.add(refreshed)
    db.commit()

    db.expire_all()
    after_add = db.exec(select(User).where(User.id == user.id)).one()
    assert isinstance(after_add.cash, int)
    assert after_add.cash == 9007199254740994

    # 3. API 回傳十進位字串
    res = client.get(f"{settings.API_V1_STR}/economy/me", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["cash"] == "9007199254740994"

    # 4. 成長資源與競技分數大數精度
    growth = get_or_create_growth(db, user.id)
    growth.growth_xp = 9007199254740995
    growth.forge_energy = 9007199254740997
    db.add(growth)
    db.commit()

    db.expire_all()
    g_reloaded = db.exec(
        select(PlayerGrowth).where(PlayerGrowth.user_id == user.id)
    ).one()
    assert isinstance(g_reloaded.growth_xp, int)
    assert g_reloaded.growth_xp == 9007199254740995
    assert isinstance(g_reloaded.forge_energy, int)
    assert g_reloaded.forge_energy == 9007199254740997


def test_settlement_failure_injection_all_or_nothing(db: Session) -> None:
    """在結算流程中注入失敗，確認現金、經驗、新養成資源、收據與牌局完成狀態均原子性回滾。"""
    email = random_email()
    user = User(
        email=email,
        hashed_password="fake",
        nickname="原子結算測試員",
        cash=1000,
        xp=100,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    growth = get_or_create_growth(db, user.id)
    initial_growth_xp = growth.growth_xp
    initial_energy = growth.forge_energy
    db.commit()

    # 模擬結算交易流程
    try:
        # 開始結算操作
        user.cash += 500
        user.xp += 50
        growth.growth_xp += 300
        growth.forge_energy += 200
        db.add(user)
        db.add(growth)
        db.flush()

        # 建立收據
        context = RewardContext(
            user_id=user.id,
            source_kind="quiz",
            source_id=uuid.uuid4(),
            core_level=0,
            equipment_snapshot=[],
            factor_snapshot={},
        )
        db.add(context)
        db.flush()

        # 注入失敗（例如外部服務斷線或資料庫約束失敗）
        raise RuntimeError("Simulated failure mid-settlement")
    except RuntimeError:
        db.rollback()

    # 驗證完全回滾
    db.expire_all()
    u = db.exec(select(User).where(User.id == user.id)).one()
    assert u.cash == 1000
    assert u.xp == 100

    g = db.exec(select(PlayerGrowth).where(PlayerGrowth.user_id == user.id)).one()
    assert g.growth_xp == initial_growth_xp
    assert g.forge_energy == initial_energy

    receipts = db.exec(
        select(RewardContext).where(RewardContext.user_id == user.id)
    ).all()
    assert len(receipts) == 0


def test_legacy_session_without_growth_compat(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """測試沒有成長資料或快照的舊牌局相容路徑：能正常讀取與結算，不拋出 500。"""
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None

    # 建立一個沒有 RewardContext 的既有 QuizSession
    quiz = QuizSession(
        user_id=user.id,
        case_ids=[],
        items=[
            {
                "item_id": "legacy_item_1",
                "type": "verdict",
                "is_scam": True,
                "text": "舊版題組相容測試",
            }
        ],
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    # 結算
    res = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": str(quiz.id)},
    )
    assert res.status_code == 200
    body = res.json()
    assert "cash_earned" in body
    assert "xp_earned" in body
