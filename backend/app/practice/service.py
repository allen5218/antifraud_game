"""作答紀錄與練習重點的資料庫層。

寫入:各玩法結算時呼叫 `record_answers`(跟結算同一個交易),
      然後排一個背景工作 `refresh_profile`。
讀取:發牌、收件匣、首頁呼叫 `practice_focus` / `practice_weights`。

**發牌路徑上沒有 AI 呼叫。** 分析器只在背景工作裡跑,玩家等發牌時讀的是上一輪算好的結果。
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import Iterable, Sequence

from fastapi import BackgroundTasks
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, col, func, select
from starlette.concurrency import run_in_threadpool

from app.core.db import engine
from app.core.fraud_types import FRAUD_TYPE_LABELS, FRAUD_TYPES
from app.core.pretest import latest_weakest_type
from app.models import PracticeAnswer, PracticeProfile, get_datetime_utc
from app.practice import analyzer
from app.practice.profile import (
    MIN_ANSWERS,
    STATS_WINDOW,
    AnswerRow,
    PracticePlan,
    PracticeStats,
    apply_rules,
    clamp_weights,
    compute_stats,
    rule_plan,
    settle_focus,
)

logger = logging.getLogger(__name__)


def record_answers(
    session: Session,
    user_id: uuid.UUID,
    mode: str,
    answers: Iterable[tuple[str, bool, Sequence[str]]],
) -> int:
    """把一輪的作答加進紀錄。`answers` 是 (fraud_type, 答對與否, 漏掉的話術)。

    不 commit —— 跟呼叫端的結算放在同一個交易,結算失敗就不會留下半套紀錄。
    """
    count = 0
    for fraud_type, correct, missed in answers:
        session.add(
            PracticeAnswer(
                user_id=user_id,
                mode=mode,
                fraud_type=fraud_type,
                correct=correct,
                missed_tags=list(missed),
            )
        )
        count += 1
    return count


def recent_answers(session: Session, user_id: uuid.UUID) -> tuple[list[AnswerRow], int]:
    """最近的作答(新到舊),以及這位玩家目前的作答總筆數(存練習重點時用來判斷新舊)。

    總筆數先查、紀錄後查:兩次查詢之間剛好有新作答寫入的話,讀到的紀錄比總筆數新,
    存檔時會被當成過期而不存。那一輪自己也排了分析,不會漏。
    """
    total = _answer_count(session, user_id)
    rows = session.exec(
        select(PracticeAnswer)
        .where(PracticeAnswer.user_id == user_id)
        .order_by(col(PracticeAnswer.created_at).desc())
        .limit(STATS_WINDOW)
    ).all()
    answers = [AnswerRow(r.mode, r.fraud_type, r.correct, r.missed_tags) for r in rows]
    return answers, total


def _answer_count(session: Session, user_id: uuid.UUID) -> int:
    return session.exec(
        select(func.count())
        .select_from(PracticeAnswer)
        .where(col(PracticeAnswer.user_id) == user_id)
    ).one()


async def build_plan(answers: Sequence[AnswerRow]) -> PracticePlan | None:
    """從作答紀錄決定比例。題數不夠就不調整(回傳 None)。"""
    if len(answers) < MIN_ANSWERS:
        return None
    stats = compute_stats(answers)
    fallback = rule_plan(stats)
    if not analyzer.enabled():
        return fallback
    output = await analyzer.analyze(stats)
    if output is None:
        return fallback
    shares = apply_rules(output.weights.as_dict(), stats)
    if shares is None:
        logger.info("分析器的比例不合規則,改用規則版:%s", output.weights)
        return fallback

    weights = clamp_weights(shares)
    proposed = None if output.focus_type == "none" else output.focus_type
    focus = settle_focus(weights, proposed, stats)
    note = _pick_note(output.note, proposed, focus, fallback, stats)
    return PracticePlan(weights, focus, note, "gemini")


def _pick_note(
    written: str,
    proposed: str | None,
    focus: str | None,
    fallback: PracticePlan,
    stats: PracticeStats,
) -> str:
    """說明文字必須跟最後的練習重點對得上。

    1. 分析器提的重點被採用、文字也合格 → 用分析器寫的
    2. 最後的重點跟規則版相同 → 用規則版(有具體題數)
    3. 都不是 → 中性的說法
    """
    if focus == proposed:
        usable = analyzer.usable_note(written, stats, focus)
        if usable:
            return usable
    if focus == fallback.focus_type:
        return fallback.note
    if focus is None:
        return "目前各類答得差不多，接下來每一類平均練習。"
    return f"接下來會多練「{FRAUD_TYPE_LABELS[focus]}」。"


def save_profile(
    session: Session,
    user_id: uuid.UUID,
    plan: PracticePlan,
    seen: int,
    answers_total: int | None = None,
) -> bool:
    """一位玩家一列,重複呼叫就覆蓋。兩輪同時結束也不會撞主鍵。

    `answers_total` 是這次分析開始時這位玩家的作答總筆數。存的時候筆數變了,
    代表分析之後又有新作答,就不存、回傳 False:寫入新作答的那一輪也排了分析,
    會用更新的紀錄重算。兩輪接連結束時,先開始的分析(要等 Gemini)可能比
    後開始的晚回來,不擋的話舊的結果會蓋掉新的。
    比筆數不比時間:作答時間是在程式裡產生的,不等於寫進資料庫的先後。
    """
    if answers_total is not None and _answer_count(session, user_id) != answers_total:
        return False
    values = {
        "weights": plan.weights,
        "focus_type": plan.focus_type or "",
        "note": plan.note,
        "source": plan.source,
        "answers_seen": seen,
        "updated_at": get_datetime_utc(),
    }
    unchanged = (
        select(func.count())
        .select_from(PracticeAnswer)
        .where(col(PracticeAnswer.user_id) == user_id)
        .scalar_subquery()
        == answers_total
        if answers_total is not None
        else None
    )
    stmt = insert(PracticeProfile).values(user_id=user_id, **values)
    session.execute(
        stmt.on_conflict_do_update(
            index_elements=["user_id"],
            set_=values,
            # 上面檢查完到寫入之間,新作答剛好寫進來的情況
            where=unchanged,
        )
    )
    return True


REFRESH_COOLDOWN = 10.0
"""同一位玩家兩次 Gemini 分析至少隔 10 秒。正常玩一輪都超過這個時間;
連續重送結算的話,多出來的請求只會合併成一次補跑,不會一直呼叫付費的模型。"""

_running: set[uuid.UUID] = set()
_again: set[uuid.UUID] = set()
_last_start: dict[uuid.UUID, float] = {}


def queue_refresh(
    background_tasks: BackgroundTasks, session: Session, user_id: uuid.UUID
) -> None:
    """結算端點 commit 之後呼叫:排背景分析,並把這個請求的 session 收掉。

    背景工作在回應送出後才跑,而請求的 session(deps.get_db)要等背景工作跑完才關。
    commit 之後只要再讀任何 ORM 屬性(例如 current_user.id),就會開一個新交易、
    借走一條連線,在分析期間(等 Gemini、冷卻、補跑)一直閒置;幾十個人同時交卷,
    連線池就被佔滿。所以端點要在 commit 前把 user_id 與回應內容準備好,
    這裡再 close,確保沒有殘留的交易。
    """
    session.close()
    background_tasks.add_task(refresh_profile, user_id)


async def refresh_profile(user_id: uuid.UUID) -> None:
    """背景工作:重新分析這位玩家,更新練習重點。失敗只記 log,不影響玩家。

    async:FastAPI 的 BackgroundTasks 遇到 async 函式會在主事件迴圈上執行。
    分析器(Gemini)必須跑在同一個事件迴圈上,它底下的 HTTP 連線池綁定建立時的迴圈;
    原本用同步版在不同執行緒各開迴圈,重用連線時會出錯、默默退回規則版。
    讀寫資料庫是同步的,丟到執行緒池。

    同一位玩家同一時間只跑一次:分析中又有一輪結算,只記下「跑完再補一次」,
    所以最後一定有一次分析看得到最新的作答。有呼叫 Gemini 時,兩次開始之間
    至少隔 REFRESH_COOLDOWN 秒。每個 worker 各自計算;跨 worker 的新舊由
    save_profile 比對作答筆數把關。
    """
    if user_id in _running:
        _again.add(user_id)
        return
    _running.add(user_id)
    try:
        while True:
            _again.discard(user_id)
            if analyzer.enabled():
                since = time.monotonic() - _last_start.get(user_id, float("-inf"))
                if since < REFRESH_COOLDOWN:
                    await asyncio.sleep(REFRESH_COOLDOWN - since)
            _last_start[user_id] = time.monotonic()
            await _refresh_once(user_id)
            if user_id not in _again:
                return
    finally:
        _running.discard(user_id)


async def _refresh_once(user_id: uuid.UUID) -> None:
    try:
        answers, total = await run_in_threadpool(_load_answers, user_id)
        plan = await build_plan(answers)
        if plan is None:
            return
        await run_in_threadpool(_store_plan, user_id, plan, len(answers), total)
    except Exception:
        logger.exception("練習重點更新失敗 user_id=%s", user_id)


def _load_answers(user_id: uuid.UUID) -> tuple[list[AnswerRow], int]:
    # 讀完就關掉連線再呼叫 Gemini,不讓一條連線整段閒置在交易裡
    with Session(engine) as session:
        return recent_answers(session, user_id)


def _store_plan(user_id: uuid.UUID, plan: PracticePlan, seen: int, total: int) -> None:
    with Session(engine) as session:
        if save_profile(session, user_id, plan, seen, answers_total=total):
            session.commit()


def get_profile(session: Session, user_id: uuid.UUID) -> PracticeProfile | None:
    return session.get(PracticeProfile, user_id)


def practice_focus(session: Session, user_id: uuid.UUID) -> str | None:
    """題組要偏重哪一類。練習重點優先;還沒有的話退回最近一次前測的最弱類型。"""
    profile = get_profile(session, user_id)
    if profile is not None:
        return profile.focus_type or None
    return latest_weakest_type(session, user_id)


def practice_weights(session: Session, user_id: uuid.UUID) -> dict[str, float] | None:
    """滑卡與收件匣用的比例。沒有練習重點時,前測的最弱類型給最高比例。"""
    profile = get_profile(session, user_id)
    if profile is not None and profile.weights:
        return clamp_weights(profile.weights)
    weakest = latest_weakest_type(session, user_id)
    if weakest is None:
        return None
    return clamp_weights({ft: (0.4 if ft == weakest else 0.15) for ft in FRAUD_TYPES})
