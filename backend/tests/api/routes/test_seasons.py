import uuid
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import QuizSession, User
from app.progression.config import CONFIG_VERSION
from app.progression.models import (
    CompetitionEntry,
    CompetitionSeason,
    SeasonAward,
    SeasonFinalRow,
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
)


def test_season_current_and_boards(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    # 查當前賽季
    r = client.get(
        f"{settings.API_V1_STR}/seasons/current", headers=normal_user_token_headers
    )
    assert r.status_code == 200
    season_data = r.json()
    assert "id" in season_data
    assert season_data["state"] == "open"
    assert season_data["days_remaining"] >= 0

    season_id = season_data["id"]

    # 查三大榜單
    for board in ("accuracy", "speed", "power"):
        rb = client.get(
            f"{settings.API_V1_STR}/seasons/{season_id}/boards/{board}",
            headers=normal_user_token_headers,
        )
        assert rb.status_code == 200
        b_data = rb.json()
        assert b_data["board"] == board
        assert "entries" in b_data


def test_season_close_awards_and_idempotency(client: TestClient, db: Session) -> None:
    """測試 14 天賽季關帳、排行榜凍結、最佳 tier 發獎、防重複發放與中斷續跑。"""
    from tests.utils.user import authentication_token_from_email
    from tests.utils.utils import random_email

    email1 = random_email()
    headers1 = authentication_token_from_email(client=client, email=email1, db=db)
    user1 = db.exec(select(User).where(User.email == email1)).first()
    assert user1 is not None

    # 建立第二個測試玩家
    user2 = User(
        email=f"user2_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="fake",
        nickname="快手小王",
    )
    # 建立第三個未達資格的玩家
    user3 = User(
        email=f"user3_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="fake",
        nickname="新手小美",
    )
    db.add(user2)
    db.add(user3)
    db.commit()
    db.refresh(user2)
    db.refresh(user3)

    # 建立一個已過期的測試賽季
    now = get_utc_now()
    past_starts = now - timedelta(days=15)
    past_ends = now - timedelta(hours=1)
    season = CompetitionSeason(
        name="第 001 期已截止賽季",
        starts_at=past_starts,
        ends_at=past_ends,
        config_version=CONFIG_VERSION,
        award_version="award-v1",
        state="open",
    )
    db.add(season)
    db.commit()
    db.refresh(season)

    # User 1: 5 天滿資格，50 題全對，高積分 -> 正確率榜與競技榜第 1 名 (tier_1)
    for day_i in range(1, 6):
        db.add(
            CompetitionEntry(
                season_id=season.id,
                user_id=user1.id,
                day=f"2026-10-0{day_i}",
                daily_source_id=uuid.uuid4(),
                correct=10,
                total=10,
                duration=30,
                power_points=1200,
            )
        )

    # User 2: 5 天滿資格，50 題對 40 題 -> 第 2 名 (tier_2)
    for day_i in range(1, 6):
        db.add(
            CompetitionEntry(
                season_id=season.id,
                user_id=user2.id,
                day=f"2026-10-0{day_i}",
                daily_source_id=uuid.uuid4(),
                correct=8,
                total=10,
                duration=50,
                power_points=800,
            )
        )

    # User 3: 只有 2 天 20 題 -> 未符合 5 天/50 題資格 (unqualified)
    for day_i in range(1, 3):
        db.add(
            CompetitionEntry(
                season_id=season.id,
                user_id=user3.id,
                day=f"2026-10-0{day_i}",
                daily_source_id=uuid.uuid4(),
                correct=10,
                total=10,
                duration=20,
                power_points=1000,
            )
        )

    db.commit()

    u1_bp_before = get_player_blueprints(db, user1.id)
    u2_bp_before = get_player_blueprints(db, user2.id)
    u3_bp_before = get_player_blueprints(db, user3.id)

    # 執行關帳
    closed = close_expired_seasons(db, now=now)
    assert season.id in closed

    db.refresh(season)
    assert season.state == "finalized"

    # 驗證凍結榜行 SeasonFinalRow
    final_rows = db.exec(
        select(SeasonFinalRow).where(SeasonFinalRow.season_id == season.id)
    ).all()
    assert len(final_rows) >= 3

    # User 1 應獲得 tier_1 獎勵（10 片圖紙與冠軍稱號）
    u1_bp_after = get_player_blueprints(db, user1.id)
    assert u1_bp_after == u1_bp_before + 10

    # User 2 應獲得 tier_2 獎勵（8 片圖紙）
    u2_bp_after = get_player_blueprints(db, user2.id)
    assert u2_bp_after == u2_bp_before + 8

    # User 3 未符資格不應得圖紙
    u3_bp_after = get_player_blueprints(db, user3.id)
    assert u3_bp_after == u3_bp_before

    # 驗證 SeasonAward 記錄
    u1_award = db.exec(
        select(SeasonAward).where(
            SeasonAward.season_id == season.id,
            SeasonAward.user_id == user1.id,
        )
    ).first()
    assert u1_award is not None
    assert u1_award.tier == "tier_1"

    # 測試重跑關帳防重複發放（Idempotency）
    closed_again = close_expired_seasons(db, now=now)
    assert len(closed_again) == 0

    # 圖紙數量保持一致，不被重複加發
    assert get_player_blueprints(db, user1.id) == u1_bp_after
    assert get_player_blueprints(db, user2.id) == u2_bp_after

    # 測試 API 查詢個人領獎結果
    r_award = client.get(
        f"{settings.API_V1_STR}/seasons/{season.id}/awards/me",
        headers=headers1,
    )
    assert r_award.status_code == 200
    award_json = r_award.json()
    assert award_json["tier"] == "tier_1"
    assert award_json["blueprints_awarded"] == 10
    assert award_json["title"] == "識詐冠軍"
    assert len(award_json["final_rows"]) >= 1


def test_cross_period_daily_entry_dropped(db: Session) -> None:
    """測試跨期完成不能把分數搬到新一期或已截止賽季。"""
    from tests.utils.user import create_random_user

    user = create_random_user(db)
    assert user is not None

    season = get_current_season(db)
    context = create_reward_context(db, user.id, "quiz", uuid.uuid4())

    # 題目日期屬於上個月 (跨期題組)
    old_date = season.starts_at.date() - timedelta(days=2)
    quiz_stale = QuizSession(
        user_id=user.id,
        daily_date=old_date,
        case_ids=[],
        items=[],
    )
    db.add(quiz_stale)
    db.commit()

    entry = record_daily_competition_entry(
        db,
        user.id,
        quiz_stale,
        context,
        correct=10,
        total=10,
        duration=30,
    )
    # 跨期題組被拒絕計入競技榜
    assert entry is None


def test_finalized_season_reads_frozen_snapshot(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Codex 實測問題修正驗證：
    finalized 賽季查榜必須讀 SeasonFinalRow，不能再即時計算 CompetitionEntry。
    實測情境：凍結快照是每題 6 秒，成績表後續修正後，公開榜不能跳動變成 124.8 秒。
    """
    from tests.utils.utils import random_email

    email = random_email()
    user = User(
        email=email,
        hashed_password="fake",
        nickname="快手王",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    now = get_utc_now()
    past_starts = now - timedelta(days=20)
    past_ends = now - timedelta(days=2)
    season = CompetitionSeason(
        name="凍結榜快照驗證賽季",
        starts_at=past_starts,
        ends_at=past_ends,
        config_version=CONFIG_VERSION,
        award_version="award-v1",
        state="open",
    )
    db.add(season)
    db.commit()
    db.refresh(season)

    # 寫入 5 天完整紀錄：50 題，總共 300 秒 -> 每題 6.0 秒
    entries = []
    for day_i in range(1, 6):
        entry = CompetitionEntry(
            season_id=season.id,
            user_id=user.id,
            day=f"2026-10-1{day_i}",
            daily_source_id=uuid.uuid4(),
            correct=10,
            total=10,
            duration=60,  # 10 題 60 秒 = 6 秒/題
            power_points=1000,
        )
        db.add(entry)
        entries.append(entry)
    db.commit()

    # 關帳並凍結快照
    closed = close_expired_seasons(db, now=now)
    assert season.id in closed

    db.refresh(season)
    assert season.state == "finalized"

    # 查速度榜：應為 6.0 秒/題
    r_before = client.get(
        f"{settings.API_V1_STR}/seasons/{season.id}/boards/speed",
        headers=normal_user_token_headers,
    )
    assert r_before.status_code == 200
    rows_before = r_before.json()["entries"]
    user_row = next(r for r in rows_before if r["user_id"] == str(user.id))
    assert abs(user_row["metrics"]["avg_seconds_per_question"] - 6.0) < 0.001

    # 後續成績表被修改（模擬補發、修正或資料竄改，duration 改為 1248 秒 = 124.8 秒/題）
    for e in entries:
        e.duration = 1248
        db.add(e)
    db.commit()

    # 再次查詢已 finalized 賽季公開榜：必須讀取 SeasonFinalRow 凍結快照，仍為 6.0 秒，絕不能變成 124.8 秒！
    r_after = client.get(
        f"{settings.API_V1_STR}/seasons/{season.id}/boards/speed",
        headers=normal_user_token_headers,
    )
    assert r_after.status_code == 200
    rows_after = r_after.json()["entries"]
    user_row_after = next(r for r in rows_after if r["user_id"] == str(user.id))
    assert abs(user_row_after["metrics"]["avg_seconds_per_question"] - 6.0) < 0.001
    assert user_row_after["metrics"]["avg_seconds_per_question"] != 124.8


def test_tied_players_get_same_award_tier(db: Session) -> None:
    """Codex 實測問題修正驗證：
    兩名五天、五十題、正確率、時間、積分完全相同的玩家，
    必須取得相同名次與相同能力獎勵檔位（均為 tier_1，各得 10 片圖紙），
    不能因 UUID 排序導致一人 tier_1、一人 tier_2。
    """
    from tests.utils.utils import random_email

    u1 = User(
        email=random_email(),
        hashed_password="fake",
        nickname="同分玩家一號",
    )
    u2 = User(
        email=random_email(),
        hashed_password="fake",
        nickname="同分玩家二號",
    )
    db.add(u1)
    db.add(u2)
    db.commit()
    db.refresh(u1)
    db.refresh(u2)

    now = get_utc_now()
    season = CompetitionSeason(
        name="同分獎勵檔位驗證賽季",
        starts_at=now - timedelta(days=20),
        ends_at=now - timedelta(days=2),
        config_version=CONFIG_VERSION,
        award_version="award-v1",
        state="open",
    )
    db.add(season)
    db.commit()
    db.refresh(season)

    # 兩位玩家完全相同的戰績：5 天各 10 題全對，時間均 30 秒，積分均 1200
    for day_i in range(1, 6):
        for u in (u1, u2):
            db.add(
                CompetitionEntry(
                    season_id=season.id,
                    user_id=u.id,
                    day=f"2026-10-2{day_i}",
                    daily_source_id=uuid.uuid4(),
                    correct=10,
                    total=10,
                    duration=30,
                    power_points=1200,
                )
            )
    db.commit()

    u1_bp_before = get_player_blueprints(db, u1.id)
    u2_bp_before = get_player_blueprints(db, u2.id)

    # 關帳發獎
    close_expired_seasons(db, now=now)

    # 驗證兩位玩家獲得相同的 tier 與獎勵
    a1 = db.exec(
        select(SeasonAward).where(
            SeasonAward.season_id == season.id, SeasonAward.user_id == u1.id
        )
    ).first()
    a2 = db.exec(
        select(SeasonAward).where(
            SeasonAward.season_id == season.id, SeasonAward.user_id == u2.id
        )
    ).first()

    assert a1 is not None and a2 is not None
    # 兩者必須同屬 tier_1，圖紙數量均為 10 片
    assert a1.tier == a2.tier == "tier_1"
    assert get_player_blueprints(db, u1.id) == u1_bp_before + 10
    assert get_player_blueprints(db, u2.id) == u2_bp_before + 10


def test_season_grace_period_enforced(db: Session) -> None:
    """Codex 實測要求：
    落實十五分鐘關帳寬限。
    結束五分鐘的賽季不能 finalized，必須等待寬限期（15分鐘）屆滿後才能關帳。
    """
    now = get_utc_now()
    # 剛結束 5 分鐘的賽季
    ended_5m_ago = now - timedelta(minutes=5)
    season = CompetitionSeason(
        name="寬限期驗證賽季",
        starts_at=now - timedelta(days=14),
        ends_at=ended_5m_ago,
        config_version=CONFIG_VERSION,
        award_version="award-v1",
        state="open",
    )
    db.add(season)
    db.commit()
    db.refresh(season)

    # 結束 5 分鐘：在寬限期內，不可關帳
    closed_at_5m = close_expired_seasons(db, now=now)
    assert season.id not in closed_at_5m
    db.refresh(season)
    assert season.state == "open"

    # 結束 16 分鐘（超過 15 分鐘寬限期）：應正常關帳
    future_now = ended_5m_ago + timedelta(minutes=16)
    closed_at_16m = close_expired_seasons(db, now=future_now)
    assert season.id in closed_at_16m
    db.refresh(season)
    assert season.state == "finalized"
