from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import text
from sqlmodel import Session, col, select

from app.daily.names import display_name
from app.economy.service import lock_user
from app.models import QuizSession, User
from app.progression.config import (
    CONFIG_VERSION,
    SEASON_DAYS,
    SEASON_FINALIZE_GRACE_MINUTES,
    SEASON_MIN_DAYS_FOR_AWARDS,
    SEASON_MIN_QUESTIONS_FOR_AWARDS,
    SEASON_SPEED_MIN_ACCURACY,
    SEASON_TIMEZONE,
)
from app.progression.math import calculate_power_points
from app.progression.models import (
    CompetitionEntry,
    CompetitionSeason,
    LeaderboardEntryPublic,
    PlayerUnlock,
    ProgressionLedger,
    RewardContext,
    SeasonAward,
    SeasonBoardPublic,
    SeasonFinalRow,
)
from app.progression.service import (
    add_player_blueprints,
    get_player_blueprints,
    get_utc_now,
)

logger = logging.getLogger(__name__)

TIER_BLUEPRINTS: dict[str, int] = {
    "tier_1": 10,
    "tier_2": 8,
    "tier_3": 6,
    "tier_4": 4,
    "tier_participation": 2,
}

TIER_PRIORITY: dict[str, int] = {
    "tier_1": 1,
    "tier_2": 2,
    "tier_3": 3,
    "tier_4": 4,
    "tier_participation": 5,
    "unqualified": 99,
}

TIER_TITLES: dict[str, str] = {
    "tier_1": "識詐冠軍",
    "tier_2": "識詐菁英",
    "tier_3": "識詐大師",
    "tier_4": "識詐專家",
    "tier_participation": "完賽榮譽",
}


def assign_award_tier(rank: int, is_qualified: bool) -> str:
    """依名次與參賽資格判定獎勵階級。"""
    if not is_qualified:
        return "unqualified"
    if rank == 1:
        return "tier_1"
    if rank in (2, 3):
        return "tier_2"
    if 4 <= rank <= 10:
        return "tier_3"
    if 11 <= rank <= 50:
        return "tier_4"
    return "tier_participation"


def get_current_season(session: Session) -> CompetitionSeason:
    """取得或自動初始化當前 14 天賽季。"""
    now = get_utc_now()
    season = session.exec(
        select(CompetitionSeason)
        .where(
            CompetitionSeason.starts_at <= now,
            CompetitionSeason.ends_at > now,
            CompetitionSeason.state == "open",
        )
        .order_by(col(CompetitionSeason.starts_at).desc())
    ).first()
    if season is not None:
        return season

    session.execute(text("SELECT pg_advisory_xact_lock(71682004)"))
    season = session.exec(
        select(CompetitionSeason)
        .where(
            CompetitionSeason.starts_at <= now,
            CompetitionSeason.ends_at > now,
            CompetitionSeason.state == "open",
        )
        .order_by(col(CompetitionSeason.starts_at).desc())
    ).first()
    if season is not None:
        return season

    # 依 Asia/Taipei 產生新賽季起訖
    tz = ZoneInfo(SEASON_TIMEZONE)
    anchor = datetime(2026, 11, 2, tzinfo=tz)
    elapsed_days = (now.astimezone(tz).date() - anchor.date()).days
    starts_at = (
        anchor + timedelta(days=elapsed_days // SEASON_DAYS * SEASON_DAYS)
    ).astimezone(timezone.utc)
    ends_at = starts_at + timedelta(days=SEASON_DAYS)

    new_season = CompetitionSeason(
        name=f"識詐競技第 {starts_at.astimezone(tz).strftime('%Y%m%d')} 期",
        starts_at=starts_at,
        ends_at=ends_at,
        config_version=CONFIG_VERSION,
        award_version="award-v1",
        state="open",
    )
    session.add(new_season)
    session.flush()
    return new_season


def record_daily_competition_entry(
    session: Session,
    user_id: uuid.UUID,
    quiz: QuizSession,
    context: RewardContext,
    *,
    correct: int,
    total: int,
    duration: int,
) -> CompetitionEntry | None:
    """在結算每日訓練時記錄至當期競技成績。

    防跨期規則：
    1. 跨過截止時間 (ends_at) 才完成的舊期題組，不補進已結束的競技榜，也不搬進新一期。
    2. 題目所屬的 daily_date 必須落在當前賽季的起訖日內。
    """
    if quiz.daily_date is None:
        return None

    now = get_utc_now()
    season = (
        session.get(CompetitionSeason, context.season_id)
        if context.season_id
        else get_current_season(session)
    )
    if season is None or season.state != "open":
        return None

    # 若作答完成時間已過該期截止時間，丟棄該次競技紀錄（玩家仍可得日常獎勵，但不可計入競技榜）
    if quiz.completed_at and quiz.completed_at >= season.ends_at:
        return None
    if (
        quiz.completed_at or now
    ) >= season.ends_at or now >= season.ends_at + timedelta(
        minutes=SEASON_FINALIZE_GRACE_MINUTES
    ):
        return None

    # 檢查題目日期是否符合當前賽季
    tz = ZoneInfo(SEASON_TIMEZONE)
    s_start_date = season.starts_at.astimezone(tz).date()
    s_end_date = season.ends_at.astimezone(tz).date()
    if not (s_start_date <= quiz.daily_date < s_end_date):
        return None

    day_str = quiz.daily_date.isoformat()

    existing = session.exec(
        select(CompetitionEntry).where(
            CompetitionEntry.season_id == season.id,
            CompetitionEntry.user_id == user_id,
            CompetitionEntry.day == day_str,
        )
    ).first()
    if existing is not None:
        return existing

    factors = context.factor_snapshot or {}
    comp_factor_str = factors.get("competition", "1.0")
    comp_factor = Decimal(comp_factor_str)

    power_points = calculate_power_points(
        correct=correct,
        total=total,
        core_level=context.core_level,
        competition_factor=comp_factor,
    )

    entry = CompetitionEntry(
        season_id=season.id,
        user_id=user_id,
        day=day_str,
        daily_source_id=quiz.id,
        correct=correct,
        total=total,
        duration=max(1, duration),
        power_points=power_points,
        context_id=context.id,
    )
    session.add(entry)
    session.flush()
    return entry


def calculate_board_entries(
    session: Session,
    season_id: uuid.UUID,
    board: str,
    current_user_id: uuid.UUID | None = None,
) -> list[LeaderboardEntryPublic]:
    """以精確比率排序，合格與暫列分開，實質同分共用名次。"""
    if board not in {"accuracy", "speed", "power"}:
        raise HTTPException(400, {"code": "unknown_board_type"})
    entries = session.exec(
        select(CompetitionEntry).where(CompetitionEntry.season_id == season_id)
    ).all()
    totals: dict[uuid.UUID, dict[str, int]] = {}
    for entry in entries:
        row = totals.setdefault(
            entry.user_id,
            {"days": 0, "correct": 0, "total": 0, "duration": 0, "power": 0},
        )
        row["days"] += 1
        row["correct"] += entry.correct
        row["total"] += entry.total
        row["duration"] += entry.duration
        row["power"] += entry.power_points
    users = (
        session.exec(select(User).where(col(User.id).in_(list(totals)))).all()
        if totals
        else []
    )
    names = {u.id: display_name(u.id, u.nickname) for u in users}
    rows: list[tuple[bool, tuple[Any, ...], str, uuid.UUID, dict[str, int]]] = []
    for uid, values in totals.items():
        total = values["total"]
        accuracy = Fraction(values["correct"], total) if total else Fraction(0)
        average = Fraction(values["duration"], total) if total else Fraction(999999)
        qualified = (
            values["days"] >= SEASON_MIN_DAYS_FOR_AWARDS
            and total >= SEASON_MIN_QUESTIONS_FOR_AWARDS
        )
        performance: tuple[Any, ...]
        if board == "speed":
            qualified = qualified and accuracy >= Fraction(
                str(SEASON_SPEED_MIN_ACCURACY)
            )
            performance = (average, -accuracy, -total, -values["days"])
        elif board == "accuracy":
            performance = (-accuracy, -total, average)
        else:
            performance = (-values["power"], -accuracy, -values["days"], -total)
        rows.append((not qualified, performance, str(uid), uid, values))
    rows.sort(key=lambda row: row[:3])
    output: list[LeaderboardEntryPublic] = []
    previous: tuple[Any, ...] | None = None
    rank = 0
    for index, (provisional, performance, _uid_text, uid, values) in enumerate(
        rows, start=1
    ):
        identity = (provisional, *performance)
        if identity != previous:
            rank = index
        previous = identity
        total = values["total"]
        displayed_accuracy = round(values["correct"] / total, 4) if total else 0.0
        metrics: dict[str, Any] = {
            "accuracy": displayed_accuracy,
            "correct": values["correct"],
            "total": total,
            "days": values["days"],
        }
        if board == "accuracy":
            metrics["accuracy_display"] = f"{displayed_accuracy * 100:.1f}%"
        elif board == "speed":
            metrics["avg_seconds_per_question"] = (
                round(values["duration"] / total, 2) if total else 0.0
            )
        else:
            metrics["power_points"] = str(values["power"])
        output.append(
            LeaderboardEntryPublic(
                rank=rank,
                user_id=uid,
                nickname=names.get(uid, "匿名玩家"),
                metrics=metrics,
                is_qualified=not provisional,
                is_me=uid == current_user_id,
            )
        )
    return output


def get_season_leaderboard(
    session: Session,
    season_id: uuid.UUID,
    board: str,
    current_user_id: uuid.UUID,
) -> SeasonBoardPublic:
    """查詢當期賽季排行榜（正確率榜、速度榜、養成競技榜）。"""
    season = session.get(CompetitionSeason, season_id)
    if season is None:
        raise HTTPException(404, {"code": "season_not_found"})

    if board not in {"accuracy", "speed", "power"}:
        raise HTTPException(400, {"code": "unknown_board_type"})
    if season.state in {"closing", "finalized"}:
        # finalized 賽季直接讀取凍結快照 SeasonFinalRow，確保公開榜永不因後續資料異動而變更
        final_rows = session.exec(
            select(SeasonFinalRow)
            .where(
                SeasonFinalRow.season_id == season_id,
                SeasonFinalRow.board == board,
            )
            .order_by(
                col(SeasonFinalRow.display_rank).asc(),
                col(SeasonFinalRow.user_id).asc(),
            )
        ).all()
        user_ids = [r.user_id for r in final_rows]
        users = (
            session.exec(select(User).where(col(User.id).in_(user_ids))).all()
            if user_ids
            else []
        )
        name_map = {u.id: display_name(u.id, u.nickname) for u in users}

        board_entries: list[LeaderboardEntryPublic] = []
        for r in final_rows:
            board_entries.append(
                LeaderboardEntryPublic(
                    rank=r.display_rank,
                    user_id=r.user_id,
                    nickname=name_map.get(r.user_id, "匿名玩家"),
                    metrics=r.metrics,
                    is_qualified=(r.award_tier != "unqualified"),
                    is_me=(r.user_id == current_user_id),
                )
            )
    else:
        board_entries = calculate_board_entries(
            session, season_id, board, current_user_id
        )

    my_entry = next((e for e in board_entries if e.user_id == current_user_id), None)

    return SeasonBoardPublic(
        season_id=season_id,
        board=board,
        entries=board_entries,
        my_entry=my_entry,
    )


def close_expired_seasons(
    session: Session,
    now: datetime | None = None,
) -> list[uuid.UUID]:
    """凍結與每位玩家發獎各自原子提交，可在中斷後續跑。"""
    current_time = now or get_utc_now()
    cutoff = current_time - timedelta(minutes=SEASON_FINALIZE_GRACE_MINUTES)
    ids = session.exec(
        select(CompetitionSeason.id).where(
            (CompetitionSeason.ends_at <= cutoff)
            | (CompetitionSeason.state == "closing"),
            CompetitionSeason.state != "finalized",
        )
    ).all()
    closed: list[uuid.UUID] = []
    for season_id in ids:
        season = session.exec(
            select(CompetitionSeason)
            .where(CompetitionSeason.id == season_id)
            .with_for_update(skip_locked=True)
            .execution_options(populate_existing=True)
        ).first()
        if season is None or season.state == "finalized":
            session.commit()
            continue
        if season.state == "open":
            for board in ("accuracy", "speed", "power"):
                for entry in calculate_board_entries(session, season_id, board):
                    session.add(
                        SeasonFinalRow(
                            season_id=season_id,
                            board=board,
                            user_id=entry.user_id,
                            metrics=entry.metrics,
                            award_tier=assign_award_tier(
                                entry.rank, entry.is_qualified
                            ),
                            display_rank=entry.rank,
                        )
                    )
            season.state = "closing"
            session.add(season)
        # 快照與 closing 狀態一起提交，之後續跑不再讀即時成績重新凍結。
        session.commit()
        final_rows = session.exec(
            select(SeasonFinalRow).where(SeasonFinalRow.season_id == season_id)
        ).all()
        best: dict[uuid.UUID, str] = {}
        for row in final_rows:
            if row.award_tier != "unqualified" and TIER_PRIORITY.get(
                row.award_tier, 99
            ) < TIER_PRIORITY.get(best.get(row.user_id, "unqualified"), 99):
                best[row.user_id] = row.award_tier
        for user_id, tier in best.items():
            user = session.get(User, user_id)
            if user is None:
                continue
            # 與其他經濟操作保持 User -> growth 鎖序；鎖後再檢查領獎紀錄。
            lock_user(session, user)
            award = session.exec(
                select(SeasonAward).where(
                    SeasonAward.season_id == season_id, SeasonAward.user_id == user_id
                )
            ).first()
            if award is not None:
                session.commit()
                continue
            count = TIER_BLUEPRINTS.get(tier, 0)
            add_player_blueprints(session, user_id, count)
            from app.progression.awards import grant_season_extras

            grant_season_extras(session, user_id, season_id, tier, final_rows)
            for row in final_rows:
                if row.user_id == user_id and row.award_tier == "tier_1":
                    key = f"title_{row.board}_{season_id}"
                    session.add(
                        PlayerUnlock(
                            user_id=user_id,
                            unlock_key=key,
                            value={
                                "accuracy": "本期正確率冠軍",
                                "speed": "本期速度冠軍",
                                "power": "本期養成競技冠軍",
                            }[row.board],
                        )
                    )
            session.add(
                SeasonAward(
                    season_id=season_id,
                    user_id=user_id,
                    tier=tier,
                    award_version=season.award_version,
                    state="granted",
                )
            )
            session.add(
                ProgressionLedger(
                    user_id=user_id,
                    event_key=f"season_award:{season_id}:{user_id}",
                    kind="season_award",
                    amounts={"blueprints": str(count)},
                    balance_after={
                        "blueprints": str(get_player_blueprints(session, user_id))
                    },
                )
            )
            session.commit()
        season = session.exec(
            select(CompetitionSeason)
            .where(CompetitionSeason.id == season_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).one()
        if season.state != "finalized":
            season.state = "finalized"
            session.add(season)
            session.commit()
            closed.append(season_id)
            logger.info("賽季 %s 關帳發獎完成", season_id)
        else:
            session.commit()
    return closed


def get_player_season_award(
    session: Session,
    season_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict[str, Any] | None:
    """查詢玩家在指定賽季的領獎結果。"""
    award = session.exec(
        select(SeasonAward).where(
            SeasonAward.season_id == season_id,
            SeasonAward.user_id == user_id,
        )
    ).first()
    if not award:
        return None

    final_rows = session.exec(
        select(SeasonFinalRow).where(
            SeasonFinalRow.season_id == season_id,
            SeasonFinalRow.user_id == user_id,
        )
    ).all()

    blueprints = TIER_BLUEPRINTS.get(award.tier, 0)
    title = TIER_TITLES.get(award.tier)

    return {
        "season_id": str(award.season_id),
        "tier": award.tier,
        "blueprints_awarded": blueprints,
        "title": title,
        "award_version": award.award_version,
        "state": award.state,
        "created_at": award.created_at.isoformat() if award.created_at else None,
        "final_rows": [
            {
                "board": r.board,
                "display_rank": r.display_rank,
                "award_tier": r.award_tier,
                "metrics": r.metrics,
            }
            for r in final_rows
        ],
    }
