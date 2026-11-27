"""日常卡片流（2026-11 改版）：一次一張卡、答錯的過幾天再出。

- `GET  /cards/summary`：首頁要的統計（今日目標、連續天數、學會幾招、各類進度），唯讀
- `POST /cards/rounds`：發一輪（年長者 3 張、其他 8 張），建立一次性牌局
- `POST /cards/rounds/{id}/answer`：作答，第一次的答案存成快照，同時更新間隔重複進度
- `POST /cards/rounds/{id}/complete`：結算發獎，重送原樣回傳

對錯只比對題庫裡寫好的答案（`app/cards/grading.py`），沒有 AI 呼叫。
"""

import uuid
from datetime import datetime, time, timedelta, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, col, select

from app.api.deps import CurrentUser, SessionDep
from app.cards.bank import GENERAL, Card, load_bank, practice_cards
from app.cards.deal import ELDER_ROUND_SIZE, ROUND_SIZE, Seen, deal_round
from app.cards.grading import (
    CardPublic,
    correct_answer,
    decode_answer,
    is_correct,
    public_card,
)
from app.cards.srs import is_learned, next_state
from app.core.age import is_elder
from app.core.fraud_types import FRAUD_TYPES
from app.core.weakness import WEAKNESS_LABELS
from app.daily.dates import TAIPEI, taipei_today
from app.economy.service import add_xp, adjust_cash, lock_user, touch_streak
from app.exam.lifecycle import require_no_active_exam
from app.models import CardProgress, CardRound, User
from app.practice.service import practice_weights, queue_refresh, record_answers
from app.progression.models import RewardContext
from app.progression.service import create_reward_context, settle_reward
from app.schemas import DecimalStr

router = APIRouter(prefix="/cards", tags=["cards"])

DAILY_GOAL = 20
ELDER_DAILY_GOAL = 6
CASH_PER_CORRECT = 30
XP_PER_CORRECT = 12


# ── 回應結構 ─────────────────────────────────────────────


class TopicProgress(BaseModel):
    fraud_type: str
    learned: int
    total: int


class CardSummary(BaseModel):
    elder_mode: bool
    daily_goal: int
    today_done: int
    streak_days: int
    # 「一招」是一句原料：同一句變出來的幾張卡，任一張到學會的盒子就算學會這一招
    learned: int
    total: int
    due_now: int
    topics: list[TopicProgress]


class RoundRequest(BaseModel):
    topic: str | None = None


class RoundResponse(BaseModel):
    round_id: uuid.UUID
    cards: list[CardPublic]
    daily_goal: int
    today_done: int


class AnswerRequest(BaseModel):
    card_key: str
    ids: list[str]


class WeaknessInfo(BaseModel):
    tag: str
    label: str


class AnswerResponse(BaseModel):
    correct: bool
    correct_ids: list[str]
    explanation: str
    weakness: WeaknessInfo | None = None


class RoundResult(BaseModel):
    correct_count: int
    total: int
    cash_earned: DecimalStr
    xp_earned: int
    today_done: int
    daily_goal: int


# ── 共用 ────────────────────────────────────────────────


def _goal(user: User) -> int:
    return ELDER_DAILY_GOAL if is_elder(user.birth_year) else DAILY_GOAL


def _today_start_utc() -> datetime:
    start = datetime.combine(taipei_today(), time.min, tzinfo=TAIPEI)
    return start.astimezone(timezone.utc)


def _today_done(session: Session, user_id: uuid.UUID) -> int:
    rows = session.exec(
        select(CardRound.answers).where(
            CardRound.user_id == user_id,
            col(CardRound.created_at) >= _today_start_utc(),
        )
    ).all()
    return sum(len(answers) for answers in rows)


def _streak(user: User) -> int:
    """昨天或今天有練才算還在連續；中斷了顯示 0（結算時才會重設欄位）。"""
    last = user.streak_last_day
    if last is None or last < taipei_today() - timedelta(days=1):
        return 0
    return user.streak_days


def _get_round(session: Session, round_id: uuid.UUID, user_id: uuid.UUID) -> CardRound:
    """鎖住這一局：同一局的並發作答與結算會排隊，不會重複發獎。"""
    card_round = session.exec(
        select(CardRound).where(CardRound.id == round_id).with_for_update()
    ).first()
    if card_round is None or card_round.user_id != user_id:
        raise HTTPException(404, {"code": "card_round_not_found"})
    return card_round


def _card(card_key: str) -> Card:
    card = load_bank().get(card_key)
    if card is None:
        raise HTTPException(404, {"code": "card_not_found"})
    return card


# ── 端點 ────────────────────────────────────────────────


@router.get("/summary", response_model=CardSummary)
def card_summary(session: SessionDep, current_user: CurrentUser) -> Any:
    elder = is_elder(current_user.birth_year)
    cards = practice_cards(elder=elder)
    progress = {
        p.card_key: p
        for p in session.exec(
            select(CardProgress).where(CardProgress.user_id == current_user.id)
        ).all()
    }
    now = datetime.now(timezone.utc)
    sources: dict[str, str] = {}
    learned_sources: set[str] = set()
    due = 0
    for card in cards:
        sources[card.source_key] = card.fraud_type
        p = progress.get(card.card_key)
        if p is None:
            continue
        if is_learned(p.box):
            learned_sources.add(card.source_key)
        if p.due_at <= now:
            due += 1
    topics = [
        TopicProgress(
            fraud_type=ft,
            learned=sum(1 for s in learned_sources if sources[s] == ft),
            total=sum(1 for f in sources.values() if f == ft),
        )
        for ft in [*FRAUD_TYPES, GENERAL]
        if any(f == ft for f in sources.values())
    ]
    return CardSummary(
        elder_mode=elder,
        daily_goal=_goal(current_user),
        today_done=_today_done(session, current_user.id),
        streak_days=_streak(current_user),
        learned=len(learned_sources),
        total=len(sources),
        due_now=due,
        topics=topics,
    )


@router.post("/rounds", response_model=RoundResponse)
def start_round(
    body: RoundRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    require_no_active_exam(session, current_user.id)
    elder = is_elder(current_user.birth_year)
    if body.topic is not None and body.topic not in {*FRAUD_TYPES, GENERAL}:
        raise HTTPException(400, {"code": "unknown_topic"})
    seen = {
        p.card_key: Seen(box=p.box, due_at=p.due_at)
        for p in session.exec(
            select(CardProgress).where(CardProgress.user_id == current_user.id)
        ).all()
    }
    cards = deal_round(
        practice_cards(elder=elder),
        seen,
        datetime.now(timezone.utc),
        size=ELDER_ROUND_SIZE if elder else ROUND_SIZE,
        weights=practice_weights(session, current_user.id),
        topic=body.topic,
    )
    if not cards:
        raise HTTPException(400, {"code": "no_cards"})
    card_round = CardRound(
        user_id=current_user.id,
        topic=body.topic,
        card_keys=[c.card_key for c in cards],
    )
    session.add(card_round)
    create_reward_context(session, current_user.id, "card", card_round.id)
    session.commit()
    rid = str(card_round.id)
    return RoundResponse(
        round_id=card_round.id,
        cards=[public_card(rid, c) for c in cards],
        daily_goal=_goal(current_user),
        today_done=_today_done(session, current_user.id),
    )


def _answer_response(snap: dict[str, Any]) -> AnswerResponse:
    tag = snap.get("weakness_tag")
    return AnswerResponse(
        correct=snap["correct"],
        correct_ids=snap["correct_ids"],
        explanation=snap["explanation"],
        weakness=WeaknessInfo(tag=tag, label=WEAKNESS_LABELS[tag])
        if tag in WEAKNESS_LABELS
        else None,
    )


@router.post("/rounds/{round_id}/answer", response_model=AnswerResponse)
def answer_card(
    round_id: uuid.UUID,
    body: AnswerRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    # 檢測中暫停訓練：先取檢測鎖，再鎖牌局
    require_no_active_exam(session, current_user.id)
    card_round = _get_round(session, round_id, current_user.id)
    if card_round.completed:
        raise HTTPException(400, {"code": "card_round_completed"})
    if body.card_key not in card_round.card_keys:
        raise HTTPException(404, {"code": "card_not_in_round"})
    snap = card_round.answers.get(body.card_key)
    if snap is not None:
        # 重送同樣的答案（上一次的回應可能遺失）回傳當時的結果；換答案就拒絕
        if snap["ids"] != body.ids:
            raise HTTPException(400, {"code": "card_already_answered"})
        return _answer_response(snap)

    card = _card(body.card_key)
    rid = str(card_round.id)
    indexes = decode_answer(rid, card, body.ids)
    if indexes is None:
        raise HTTPException(400, {"code": "bad_answer"})
    correct = is_correct(card, indexes)
    snap = {
        "ids": body.ids,
        "correct": correct,
        "correct_ids": correct_answer(rid, card),
        "fraud_type": card.fraud_type,
        "weakness_tag": card.weakness_tag,
        "explanation": card.explanation,
    }
    card_round.answers = {**card_round.answers, body.card_key: snap}

    now = datetime.now(timezone.utc)
    progress = session.get(CardProgress, (current_user.id, card.card_key))
    if progress is None:
        progress = CardProgress(
            user_id=current_user.id,
            card_key=card.card_key,
            fraud_type=card.fraud_type,
            source_key=card.source_key,
            due_at=now,
        )
    progress.box, progress.due_at = next_state(progress.box, correct, now)
    progress.seen_count += 1
    progress.correct_count += int(correct)
    progress.last_answered_at = now
    session.add(progress)
    session.add(card_round)
    session.commit()
    return _answer_response(snap)


@router.post("/rounds/{round_id}/complete", response_model=RoundResult)
def complete_round(
    round_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> Any:
    card_round = _get_round(session, round_id, current_user.id)
    if card_round.completed:
        if card_round.result is None:
            raise HTTPException(400, {"code": "card_round_completed"})
        return RoundResult.model_validate(card_round.result)
    answered = [
        card_round.answers[k] for k in card_round.card_keys if k in card_round.answers
    ]
    if not answered:
        raise HTTPException(400, {"code": "empty_answers"})

    correct_count = sum(1 for a in answered if a["correct"])
    cash = CASH_PER_CORRECT * correct_count
    xp = XP_PER_CORRECT * correct_count
    user = lock_user(session, current_user)
    adjust_cash(user, cash, reason="card_reward")
    add_xp(user, xp, reason="card_reward")
    touch_streak(user, taipei_today())

    context = session.exec(
        select(RewardContext).where(
            RewardContext.source_kind == "card",
            RewardContext.source_id == card_round.id,
        )
    ).first() or create_reward_context(session, user.id, "card", card_round.id)
    receipt, _ = settle_reward(
        session, user, context, base_cash=cash, base_xp=xp, reason="card_reward"
    )
    cash_total = cash + int(receipt.final_rewards["cash_bonus"])

    # 練習重點只看五種詐騙；共通類（165、查證習慣）不算
    record_answers(
        session,
        user.id,
        "card",
        [
            (
                a["fraud_type"],
                bool(a["correct"]),
                [a["weakness_tag"]] if not a["correct"] and a["weakness_tag"] else [],
            )
            for a in answered
            if a["fraud_type"] in FRAUD_TYPES
        ],
    )
    result = RoundResult(
        correct_count=correct_count,
        total=len(answered),
        cash_earned=cash_total,
        xp_earned=xp,
        today_done=_today_done(session, user.id),
        daily_goal=_goal(user),
    )
    card_round.completed = True
    card_round.completed_at = datetime.now(timezone.utc)
    card_round.result = result.model_dump(mode="json")
    session.add(user)
    session.add(card_round)
    user_id = user.id
    session.commit()

    queue_refresh(background_tasks, session, user_id)
    return result
