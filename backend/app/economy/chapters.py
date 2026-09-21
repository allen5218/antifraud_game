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
        title="第 1 章：別離開平台",
        skill_type="fake-sale",
        description="拍賣與官方金流：學習辨識站外假客服、釣魚 QR Code 與堅持官方交易機制。",
    ),
    ChapterDef(
        chapter_id=2,
        title="第 2 章：便宜得太剛好",
        skill_type="shopping",
        description="購物、物流與價金：掌握超低價急售心理操縱，善用平台履約保證與七天鑑賞機制。",
    ),
    ChapterDef(
        chapter_id=3,
        title="第 3 章：電話那頭的銀行",
        skill_type="atm",
        description="分期、ATM 與自行回撥：建立「ATM 絕無解除分期功能」之鐵律，凡遇來電一律掛斷查證。",
    ),
    ChapterDef(
        chapter_id=4,
        title="第 4 章：穩賺群組",
        skill_type="investment",
        description="投資資格與資金去向：查證金管會證期局特許名冊，破除假對帳單、暗樁與保證獲利話術。",
    ),
    ChapterDef(
        chapter_id=5,
        title="第 5 章：感情碰到錢",
        skill_type="romance",
        description="交友界線與清關要求：識別海外急難、代墊清關稅費與殺豬盤誘導入金，堅守財務邊界。",
    ),
]


@dataclass(frozen=True)
class LadderRungDef:
    rung_id: int
    contact_id: str
    rung_title: str
    chapter_title: str
    description: str


LADDER_RUNGS: list[LadderRungDef] = [
    LadderRungDef(
        rung_id=1,
        contact_id="landlady",
        rung_title="鄰里幫手",
        chapter_title="別離開平台",
        description="房東阿姨管理著多處物業，近期常遇上有疑慮的通聯與租賃要求。從熟悉的生活事件開始，學習辨識非官方管道與假客服。",
    ),
    LadderRungDef(
        rung_id=2,
        contact_id="li_li",
        rung_title="網路同好",
        chapter_title="便宜得太剛好",
        description="梨梨熱愛手作次文化與二手周邊收購，但過於優惠的私訊急售往往伴隨風險。掌握價金查證與履約保障。",
    ),
    LadderRungDef(
        rung_id=3,
        contact_id="a_can",
        rung_title="社群現場",
        chapter_title="電話那頭的銀行",
        description="阿燦在社群平台嘗試各種企劃與帶貨，時常接到宣稱扣款錯誤或升級 VIP 的來電。記住 ATM 絕無解除分期功能。",
    ),
    LadderRungDef(
        rung_id=4,
        contact_id="hao_ge",
        rung_title="人脈考驗",
        chapter_title="穩賺群組",
        description="豪哥活躍於商務人脈社團，接觸各類私募基金與高額回報項目。查證特許名冊與真實金流，破除穩賺話術。",
    ),
    LadderRungDef(
        rung_id=5,
        contact_id="wei_jie",
        rung_title="高額委託",
        chapter_title="感情碰到錢",
        description="薇姐身家豐厚且直率豪爽，近期遇到海外特殊企劃與人脈委託。堅守財務邊界，查驗海外清關與個人境外匯款。",
    ),
]

LADDER_ORDER: list[str] = [r.contact_id for r in LADDER_RUNGS]


def get_unlocked_contact_ids(completed_chapters: int) -> list[str]:
    """取得依完成章節數解鎖的聯絡人 ID 列表。

    completed_chapters=0 -> ['landlady']
    completed_chapters=1 -> ['landlady', 'li_li']
    completed_chapters=2 -> ['landlady', 'li_li', 'a_can']
    completed_chapters=3 -> ['landlady', 'li_li', 'a_can', 'hao_ge']
    completed_chapters>=4 -> ['landlady', 'li_li', 'a_can', 'hao_ge', 'wei_jie']
    """
    count = min(len(LADDER_ORDER), max(1, completed_chapters + 1))
    return LADDER_ORDER[:count]


def is_contact_unlocked(contact_id: str, completed_chapters: int) -> bool:
    """判斷指定聯絡人對該玩家是否已解鎖。"""
    return contact_id in get_unlocked_contact_ids(completed_chapters)


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


def record_ladder_scenario_progress(
    session: Session, user: User, contact_id: str, has_evidence: bool
) -> bool:
    """以 contact_id 判定當前階的情境關卡完成（天梯主線）。

    若 contact_id == 當前階聯絡人且具有查證證據：
    標記當前階 scenario_completed = True。
    若該階 quiz_completed 亦已達成，推進章節（user.completed_chapters += 1）。
    最多推進一章。
    """
    if not has_evidence:
        return False

    current_chapter = user.completed_chapters + 1
    if current_chapter > len(LADDER_RUNGS):
        return False

    current_rung = LADDER_RUNGS[current_chapter - 1]
    if contact_id != current_rung.contact_id:
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
