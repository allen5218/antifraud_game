"""章節推進與收入倍率系統（T3 / AC4）。

五個章節覆蓋五種詐騙類型與查證技能：
- 第 1 章：假網路拍賣查證（fake-sale）
- 第 2 章：一般購物詐欺查證（shopping）
- 第 3 章：解除分期付款查證（atm）
- 第 4 章：假投資詐欺查證（investment）
- 第 5 章：假愛情交友查證（romance）

每章完成至少一輪訓練及該章的一次有證據的情境任務後晉級。
每個 session 最多推進一章。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlmodel import Session, select

from app.economy.service import adjust_cash
from app.models import User, UserChapterProgress

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class ChapterDef:
    chapter_id: int
    title: str
    skill_type: str
    description: str


CHAPTER_DEFINITIONS: list[ChapterDef] = [
    ChapterDef(
        chapter_id=1,
        title="第 1 章：拍賣平台與官方金流",
        skill_type="fake-sale",
        description="學習辨識站外假客服、釣魚 QR Code 與堅持官方交易機制。",
    ),
    ChapterDef(
        chapter_id=2,
        title="第 2 章：購物價金與物流查證",
        skill_type="shopping",
        description="掌握超低價急售心理操縱，善用平台履約保證與七天鑑賞機制。",
    ),
    ChapterDef(
        chapter_id=3,
        title="第 3 章：解除分期與 ATM 鐵律",
        skill_type="atm",
        description="建立「ATM 絕無解除分期功能」之鐵律，凡遇來電一律掛斷查證。",
    ),
    ChapterDef(
        chapter_id=4,
        title="第 4 章：投資資質與監管查核",
        skill_type="investment",
        description="查證金管會證期局特許名冊，破除假對帳單、暗樁與保證獲利話術。",
    ),
    ChapterDef(
        chapter_id=5,
        title="第 5 章：交友界線與清關查證",
        skill_type="romance",
        description="識別海外急難、代墊清關稅費與殺豬盤誘導入金，堅守財務邊界。",
    ),
]


def get_income_multiplier(completed_chapters: int) -> float:
    """收入倍率 = 1.15 ^ min(已完成章節數, 5)，最高約 2.011 倍。"""
    clamped = min(max(0, completed_chapters), 5)
    return 1.15**clamped


def apply_income_multiplier(base_cash: int, completed_chapters: int) -> int:
    """套用章節倍率並四捨五入取整。"""
    multiplier = get_income_multiplier(completed_chapters)
    return int(round(base_cash * multiplier))


def get_or_create_progress(
    session: Session, user_id: Any, chapter_id: int
) -> UserChapterProgress:
    prog = session.exec(
        select(UserChapterProgress).where(
            UserChapterProgress.user_id == user_id,
            UserChapterProgress.chapter_id == chapter_id,
        )
    ).first()
    if not prog:
        prog = UserChapterProgress(user_id=user_id, chapter_id=chapter_id)
        session.add(prog)
        session.flush()
    return prog


def record_quiz_progress(session: Session, user: User) -> bool:
    """記錄完成一輪快測訓練。若達成條件推進章節（最多推進一章）。"""
    current_chapter = user.completed_chapters + 1
    if current_chapter > 5:
        return False

    prog = get_or_create_progress(session, user.id, current_chapter)
    prog.quiz_completed = True
    session.add(prog)

    if prog.scenario_completed and not prog.is_completed:
        prog.is_completed = True
        prog.completed_at = datetime.now(timezone.utc)
        user.completed_chapters = current_chapter
        session.add(user)
        session.add(prog)
        return True
    return False


def record_scenario_progress(
    session: Session, user: User, fraud_type: str, has_evidence: bool
) -> bool:
    """記錄完成有查證證據的情境任務。若達成條件推進章節（最多推進一章）。"""
    if not has_evidence:
        return False

    current_chapter = user.completed_chapters + 1
    if current_chapter > 5:
        return False

    target_def = next(
        (c for c in CHAPTER_DEFINITIONS if c.chapter_id == current_chapter), None
    )
    if not target_def or target_def.skill_type != fraud_type:
        return False

    prog = get_or_create_progress(session, user.id, current_chapter)
    prog.scenario_completed = True
    session.add(prog)

    if prog.quiz_completed and not prog.is_completed:
        prog.is_completed = True
        prog.completed_at = datetime.now(timezone.utc)
        user.completed_chapters = current_chapter
        session.add(user)
        session.add(prog)
        return True
    return False


def claim_starter_grant(session: Session, user: User) -> int:
    """領取一次性入門章節補助 7,000 元（需完成第 1 章）。"""
    if user.starter_grant_claimed:
        raise ValueError("starter_grant_already_claimed")
    if user.completed_chapters < 1:
        raise ValueError("chapter_1_required")

    GRANT_AMOUNT = 7000
    adjust_cash(user, GRANT_AMOUNT, reason="starter_chapter_grant")
    user.starter_grant_claimed = True
    session.add(user)
    return GRANT_AMOUNT
