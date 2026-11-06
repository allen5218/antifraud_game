import json
import math
import uuid
from datetime import timedelta
from decimal import Decimal
from fractions import Fraction

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import engine
from app.economy.service import adjust_cash
from app.main import app
from app.models import User
from app.progression.config import CONFIG_VERSION
from app.progression.math import core_factor
from app.progression.models import (
    CompetitionEntry,
    CompetitionSeason,
    RewardContext,
    SeasonAward,
)
from app.progression.seasons import close_expired_seasons
from app.progression.service import (
    ensure_starter_equipment,
    get_or_create_growth,
    get_utc_now,
)
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email


def run_all_probes() -> dict:
    client = TestClient(app)
    results = {
        "runtime": "Docker / dedicated Supabase PostgreSQL",
        "probes": {},
    }

    with Session(engine) as session:
        # Probe 1: numeric_precision
        email1 = random_email()
        headers1 = authentication_token_from_email(
            client=client, email=email1, db=session
        )
        user1 = session.exec(select(User).where(User.email == email1)).one()
        user1.cash = 9007199254740993
        session.add(user1)
        session.commit()

        session.expire_all()
        refreshed_user1 = session.exec(select(User).where(User.id == user1.id)).one()
        orm_type = type(refreshed_user1.cash).__name__
        orm_val = str(refreshed_user1.cash)

        # Call API
        api_res = client.get(f"{settings.API_V1_STR}/economy/me", headers=headers1)
        api_cash = api_res.json().get("cash")

        # adjust_cash + 1
        adjust_cash(refreshed_user1, 1, reason="probe")
        session.add(refreshed_user1)
        session.commit()

        session.expire_all()
        after_user1 = session.exec(select(User).where(User.id == user1.id)).one()
        db_after_add_one = str(after_user1.cash)

        results["probes"]["numeric_precision"] = {
            "exact_database_value_before": "9007199254740993",
            "orm_type": orm_type,
            "orm_value": orm_val,
            "http_status": api_res.status_code,
            "api_cash": api_cash,
            "database_after_add_one": db_after_add_one,
            "expected_after_add_one": "9007199254740994",
        }

        # Probe 2: rollback_atomicity
        email2 = random_email()
        user2 = User(
            email=email2,
            hashed_password="fake",
            nickname="回滾原子探針員",
            cash=1000,
        )
        session.add(user2)
        session.commit()
        session.refresh(user2)

        # Uncommitted transaction
        user2.cash = 1100
        session.add(user2)
        session.flush()

        get_or_create_growth(session, user2.id)
        ensure_starter_equipment(session, user2.id)

        # Enclosing rollback
        session.rollback()

        session.expire_all()
        reloaded_user2 = session.exec(select(User).where(User.id == user2.id)).one()
        contexts = session.exec(
            select(RewardContext).where(RewardContext.user_id == user2.id)
        ).all()

        results["probes"]["rollback_atomicity"] = {
            "balance_before": "1000",
            "balance_after_enclosing_rollback": str(reloaded_user2.cash),
            "expected_balance_after_rollback": "1000",
            "reward_context_count": len(contexts),
            "base_cash_committed_despite_rollback": reloaded_user2.cash == 1100,
        }

        # Probe 3: season_frozen_and_ties
        now = get_utc_now()
        season = CompetitionSeason(
            name="Codex同分與快照驗證賽季",
            starts_at=now - timedelta(days=20),
            ends_at=now - timedelta(days=2),
            config_version=CONFIG_VERSION,
            award_version="award-v1",
            state="open",
        )
        session.add(season)
        session.commit()
        session.refresh(season)

        u_tie1 = User(email=random_email(), hashed_password="fake", nickname="同分A")
        u_tie2 = User(email=random_email(), hashed_password="fake", nickname="同分B")
        session.add(u_tie1)
        session.add(u_tie2)
        session.commit()
        session.refresh(u_tie1)
        session.refresh(u_tie2)

        entries_u1 = []
        for d in range(1, 6):
            e1 = CompetitionEntry(
                season_id=season.id,
                user_id=u_tie1.id,
                day=f"2026-10-0{d}",
                daily_source_id=uuid.uuid4(),
                correct=10,
                total=10,
                duration=60,  # 6.0 sec/question
                power_points=1200,
            )
            e2 = CompetitionEntry(
                season_id=season.id,
                user_id=u_tie2.id,
                day=f"2026-10-0{d}",
                daily_source_id=uuid.uuid4(),
                correct=10,
                total=10,
                duration=60,
                power_points=1200,
            )
            session.add(e1)
            session.add(e2)
            entries_u1.append(e1)
        session.commit()

        # Close season
        close_expired_seasons(session, now=now)
        session.refresh(season)

        a1 = session.exec(
            select(SeasonAward).where(
                SeasonAward.season_id == season.id, SeasonAward.user_id == u_tie1.id
            )
        ).first()
        a2 = session.exec(
            select(SeasonAward).where(
                SeasonAward.season_id == season.id, SeasonAward.user_id == u_tie2.id
            )
        ).first()

        # Query frozen speed board
        r_board1 = client.get(
            f"{settings.API_V1_STR}/seasons/{season.id}/boards/speed",
            headers=headers1,
        )
        speed_entries = r_board1.json().get("entries", [])
        u1_row = next(r for r in speed_entries if r["user_id"] == str(u_tie1.id))
        frozen_speed = u1_row["metrics"]["avg_seconds_per_question"]

        # Alter CompetitionEntry duration to 1248s (124.8 sec/question)
        for e in entries_u1:
            e.duration = 1248
            session.add(e)
        session.commit()

        # Query public speed board again
        r_board2 = client.get(
            f"{settings.API_V1_STR}/seasons/{season.id}/boards/speed",
            headers=headers1,
        )
        speed_entries2 = r_board2.json().get("entries", [])
        u1_row2 = next(r for r in speed_entries2 if r["user_id"] == str(u_tie1.id))
        speed_after_alter = u1_row2["metrics"]["avg_seconds_per_question"]

        awards_count_before = len(
            session.exec(
                select(SeasonAward).where(SeasonAward.season_id == season.id)
            ).all()
        )
        close_expired_seasons(session, now=now)
        awards_count_after = len(
            session.exec(
                select(SeasonAward).where(SeasonAward.season_id == season.id)
            ).all()
        )

        results["probes"]["season_frozen_and_ties"] = {
            "manual_close_state": season.state,
            "awards_for_two_equal_players": [
                a1.tier if a1 else None,
                a2.tier if a2 else None,
            ],
            "original_frozen_speed": {
                "days": 5,
                "total": 50,
                "accuracy": 1.0,
                "avg_seconds_per_question": frozen_speed,
            },
            "public_speed_after_entry_correction": {
                "avg_seconds_per_question": speed_after_alter,
                "accuracy": 1.0,
                "total": 50,
                "days": 5,
            },
            "repeat_close_awards_before": awards_count_before,
            "repeat_close_awards_after": awards_count_after,
        }

        # Probe 4: season_grace
        s_grace = CompetitionSeason(
            name="15分寬限驗證賽季",
            starts_at=now - timedelta(days=14),
            ends_at=now - timedelta(minutes=5),
            config_version=CONFIG_VERSION,
            award_version="award-v1",
            state="open",
        )
        session.add(s_grace)
        session.commit()
        session.refresh(s_grace)

        close_expired_seasons(session, now=now)
        session.refresh(s_grace)
        state_at_5m = s_grace.state

        close_expired_seasons(session, now=s_grace.ends_at + timedelta(minutes=16))
        session.refresh(s_grace)
        state_after_grace = s_grace.state

        results["probes"]["season_grace"] = {
            "minutes_since_end": 5,
            "required_grace_minutes": 15,
            "state_at_5m": state_at_5m,
            "state_after_grace": state_after_grace,
        }

        # Probe 5: math_precision
        exact_ratio = (Fraction(6, 5) ** 400) * 100
        exact_floor = exact_ratio.numerator // exact_ratio.denominator
        calculated_factor = core_factor(400)
        calculated_floor = math.floor(Decimal(100) * calculated_factor)

        results["probes"]["math_precision"] = {
            "core_level": 400,
            "base_cash": 100,
            "theoretical_floor": str(exact_floor),
            "calculated_floor": str(calculated_floor),
            "diff": calculated_floor - exact_floor,
        }

    return results


if __name__ == "__main__":
    res = run_all_probes()
    print(json.dumps(res, indent=2, ensure_ascii=False))  # noqa: T201  CLI 輸出
