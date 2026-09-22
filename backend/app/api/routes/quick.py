import logging
import uuid
from datetime import datetime, timezone
from random import shuffle
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from sqlmodel import Session, col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.core.cases import (
    GameCaseRow,
    VerificationQuestionRow,
    get_case,
    list_published_for_quiz,
    list_published_verification_questions,
)
from app.core.quiz import (
    case_tags,
    max_difficulty_for_level,
    score_match,
    score_tactics,
    select_quiz_material,
    verification_quota,
)
from app.core.weakness import (
    WEAKNESS_LABELS,
    WEAKNESS_SUGGESTIONS,
    WEAKNESS_TAGS,
)
from app.economy.levels import level_of
from app.economy.service import add_xp, adjust_cash, lock_user
from app.models import QuizSession, SwipeCard
from app.schemas import (
    QuizAnswerItem,
    QuizAnswerRequest,
    QuizAnswerResponse,
    QuizCompleteRequest,
    QuizCompleteResponse,
    QuizDeckItem,
    QuizDeckResponse,
    QuizMatchAnswerResponse,
    QuizMatchPairResult,
    QuizMatchPrompt,
    QuizMatchPublic,
    QuizMatchTarget,
    QuizRedFlag,
    QuizTacticsAnswerResponse,
    QuizTacticsOption,
    QuizTacticsPublic,
    QuizVerdictAnswerResponse,
    QuizVerdictPublic,
    QuizVerificationAnswerResponse,
    QuizVerificationOption,
    QuizVerificationPublic,
    QuizWeaknessDetail,
    SwipeAnswerItem,
    SwipeAnswerRequest,
    SwipeAnswerResponse,
    SwipeCardPublic,
    SwipeCompleteRequest,
    SwipeCompleteResponse,
    WeaknessSummaryItem,
)

router = APIRouter(prefix="/quick", tags=["quick"])
logger = logging.getLogger(__name__)


def _reward(correct_count: int, best_streak: int) -> tuple[int, int]:
    cash = int(20 * correct_count * (1 + 0.1 * (best_streak // 3)))
    xp = 10 * correct_count
    return cash, xp


def _weakness_details(tags: set[str]) -> list[QuizWeaknessDetail]:
    return [
        QuizWeaknessDetail(
            tag=tag,
            label=WEAKNESS_LABELS[tag],
            suggestion=WEAKNESS_SUGGESTIONS[tag],
        )
        for tag in sorted(tags & WEAKNESS_TAGS)
    ]


def _weakness_summary(weakness: dict[str, int]) -> list[WeaknessSummaryItem]:
    return [
        WeaknessSummaryItem(tag=tag, label=WEAKNESS_LABELS[tag], count=count)
        for tag, count in sorted(
            weakness.items(), key=lambda item: item[1], reverse=True
        )
        if tag in WEAKNESS_TAGS
    ]


@router.get("/swipe/deck", response_model=list[SwipeCardPublic])
def swipe_deck(session: SessionDep, current_user: CurrentUser, size: int = 12) -> Any:
    _ = current_user
    size = max(1, min(size, 30))
    cards = session.exec(select(SwipeCard).order_by(func.random()).limit(size)).all()
    return [
        SwipeCardPublic(
            id=str(c.id),
            scenario=c.scenario,
            source_label=c.source_label,
            fraud_type=c.fraud_type,
            difficulty=c.difficulty,
        )
        for c in cards
    ]


@router.post("/swipe/answer", response_model=SwipeAnswerResponse)
def swipe_answer(
    payload: SwipeAnswerRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    _ = current_user
    card = session.get(SwipeCard, uuid.UUID(payload.card_id))
    if not card:
        raise HTTPException(404, "card not found")
    return SwipeAnswerResponse(
        correct=payload.guess_is_scam == card.is_scam,
        is_scam=card.is_scam,
        explanation=card.explanation,
        weakness_tags=card.weakness_tags,
        tag_details=_weakness_details(set(card.weakness_tags)),
    )


@router.post("/swipe/complete", response_model=SwipeCompleteResponse)
def swipe_complete(
    payload: SwipeCompleteRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    if not payload.answers:
        raise HTTPException(400, {"code": "empty_answers"})

    # Anti-cheat: dedupe card_ids (count each unique card once, first occurrence)
    # and cap the answer count to prevent reward inflation
    MAX_ANSWERS = 30
    seen: set[str] = set()
    deduped: list[SwipeAnswerItem] = []
    for a in payload.answers:
        if a.card_id in seen:
            continue
        seen.add(a.card_id)
        deduped.append(a)
        if len(deduped) >= MAX_ANSWERS:
            break

    ids = [uuid.UUID(a.card_id) for a in deduped]
    cards = {
        c.id: c
        for c in session.exec(select(SwipeCard).where(col(SwipeCard.id).in_(ids))).all()
    }

    correct_count = 0
    best_streak = 0
    streak = 0
    weakness: dict[str, int] = {}
    for a in deduped:
        card = cards.get(uuid.UUID(a.card_id))
        if card is None:
            continue
        if a.guess_is_scam == card.is_scam:
            correct_count += 1
            streak += 1
            best_streak = max(best_streak, streak)
        else:
            streak = 0
            for tag in card.weakness_tags:
                weakness[tag] = weakness.get(tag, 0) + 1

    cash, xp = _reward(correct_count, best_streak)
    current_user = lock_user(session, current_user)
    adjust_cash(current_user, cash, reason="swipe_reward")
    add_xp(current_user, xp, reason="swipe_reward")
    session.add(current_user)
    session.commit()

    summary = _weakness_summary(weakness)
    return SwipeCompleteResponse(
        correct_count=correct_count,
        total=len(deduped),
        best_streak=best_streak,
        cash_earned=cash,
        xp_earned=xp,
        weakness_summary=summary,
    )


# ── Quiz（混合題型）───────────────────────────────────────


def _quiz_reward(correct_count: int, best_streak: int) -> tuple[int, int]:
    cash = int(40 * correct_count * (1 + 0.1 * (best_streak // 3)))
    xp = 20 * correct_count
    return cash, xp


def _pick_verification_questions(
    session: SessionDep, *, max_difficulty: int | None, limit: int
) -> list[VerificationQuestionRow]:
    """逐題挑查證題,每一題都避開前面已挑走的母案例與其鏡像。

    不能一次 SQL 抽 N 題:`ORDER BY random() LIMIT n` 沒辦法讓同一次查詢裡的列
    互相排除,同一個母案例的兩個子題(next_action / evidence_scope)會一起被抽出來,
    鏡像對的兩面也會。鏡像對標題完全相同,同副出現等於把 verdict 題的答案寫在畫面上
    ——實測現有題庫抽三題有 1.95% 會碰到。

    limit 最多 3,所以多跑幾次查詢的成本可以忽略。
    """
    picked: list[VerificationQuestionRow] = []
    taken: set[int] = set()
    for _ in range(limit):
        rows = list_published_verification_questions(
            session,
            max_difficulty=max_difficulty,
            exclude_case_ids=taken,
            limit=1,
        )
        if not rows:
            break
        picked.append(rows[0])
        taken.add(rows[0].case_id)
    if len(picked) < limit:
        # 缺額會被 _compose_deck 補成 verdict,所以牌數看起來正常、玩家也不會察覺。
        # 子表沒灌好時整個題型會靜默消失,沒有這行就查不出來。
        logger.warning("quiz 查證題素材不足,配額 %d 只取到 %d", limit, len(picked))
    return picked


def _cases_excluding(
    cases: list[GameCaseRow], taken_case_ids: set[int]
) -> list[GameCaseRow]:
    """把已被查證題佔走的案例與其鏡像從選材池中移除。

    鏡像對是同一個情境的詐騙／正當兩面(標題完全相同),同時出現會直接洩漏
    verdict 題的答案。**兩個方向都要擋**:被佔走的案例自己指向的鏡像,
    以及反過來指向它的案例。
    """
    if not taken_case_ids:
        return cases
    blocked = set(taken_case_ids)
    blocked.update(
        case.mirror_of
        for case in cases
        if case.id in taken_case_ids and case.mirror_of is not None
    )
    return [
        case
        for case in cases
        if case.id not in blocked
        and (case.mirror_of is None or case.mirror_of not in blocked)
    ]


@router.get("/quiz/deck", response_model=QuizDeckResponse)
def quiz_deck(session: SessionDep, current_user: CurrentUser, size: int = 5) -> Any:
    size = max(1, min(size, 10))
    max_difficulty = max_difficulty_for_level(level_of(current_user.xp))
    cases = list_published_for_quiz(session)
    shuffle(cases)

    # 查證題先選。它與案例題型互相排斥(同一個情境不能在一副牌出現兩次),
    # 如果反過來先選案例題再挑查證題,兩邊的數量會互相牽動而收斂不了,
    # 牌堆就會時多時少。先定版查證題、再把它佔走的案例從選材池移除,
    # 剩下的缺額一律由 select_quiz_material 補滿,題數才穩定。
    verifications = _pick_verification_questions(
        session,
        max_difficulty=max_difficulty,
        limit=verification_quota(size),
    )
    taken_case_ids = {question.case_id for question in verifications}
    material = select_quiz_material(
        _cases_excluding(cases, taken_case_ids),
        size=size,
        max_difficulty=max_difficulty,
        verification_count=len(verifications),
    )

    stored_items: list[dict[str, Any]] = []
    public_items: list[QuizDeckItem] = []
    case_ids: list[int] = []

    for case in material.verdict:
        item_id = uuid.uuid4().hex
        stored_items.append(
            {
                "item_id": item_id,
                "type": "verdict",
                "case_id": case.id,
                "is_scam": case.is_scam,
                "correct_tags": sorted(case_tags(case.red_flags)),
            }
        )
        case_ids.append(case.id)
        public_items.append(
            QuizVerdictPublic(
                item_id=item_id,
                fraud_type=case.fraud_type,
                title=case.title,
                narrative=case.narrative,
                difficulty=case.difficulty,
            )
        )

    for case in material.tactics:
        item_id = uuid.uuid4().hex
        # 每題建立並打亂自己的 list，避免固定位置或跨題共用順序洩漏答案模式。
        tactics_options = [
            QuizTacticsOption(tag=tag, label=label)
            for tag, label in WEAKNESS_LABELS.items()
        ]
        shuffle(tactics_options)
        stored_items.append(
            {
                "item_id": item_id,
                "type": "tactics",
                "case_id": case.id,
                "correct_tags": sorted(case_tags(case.red_flags)),
            }
        )
        case_ids.append(case.id)
        public_items.append(
            QuizTacticsPublic(
                item_id=item_id,
                fraud_type=case.fraud_type,
                title=case.title,
                narrative=case.narrative,
                difficulty=case.difficulty,
                question="這則訊息用了哪些話術？（複選）",
                options=tactics_options,
            )
        )

    if material.match:
        item_id = uuid.uuid4().hex
        stored_pairs: list[dict[str, Any]] = []
        prompts: list[QuizMatchPrompt] = []
        for match_material in material.match:
            pair_id = uuid.uuid4().hex
            text = str(
                match_material.case.red_flags[match_material.flag_index].get("text", "")
            )
            stored_pairs.append(
                {
                    "pair_id": pair_id,
                    "case_id": match_material.case.id,
                    "flag_index": match_material.flag_index,
                    "tag": match_material.tag,
                    "text": text,
                    "provenance": match_material.case.provenance,
                }
            )
            case_ids.append(match_material.case.id)
            prompts.append(
                QuizMatchPrompt(
                    pair_id=pair_id,
                    text=text,
                )
            )
        targets = [
            QuizMatchTarget(tag=tag, label=WEAKNESS_LABELS[tag])
            for tag in WEAKNESS_TAGS
        ]
        shuffle(prompts)
        shuffle(targets)
        stored_items.append(
            {"item_id": item_id, "type": "match", "pairs": stored_pairs}
        )
        public_items.append(
            QuizMatchPublic(
                item_id=item_id,
                question="把話術和例句配對起來",
                match_prompts=prompts,
                match_targets=targets,
            )
        )

    for question in verifications:
        parent_case = get_case(session, question.case_id)
        if parent_case is None:
            logger.warning(
                "查證題 %s 的母案例 %d 讀不到，本題不進牌堆",
                question.question_key,
                question.case_id,
            )
            continue
        item_id = uuid.uuid4().hex
        stored_items.append(
            {
                "item_id": item_id,
                "type": "verification",
                "question_id": question.id,
                "case_id": question.case_id,
                "correct_key": question.correct_key,
                "explanation": question.explanation,
                "provenance": question.provenance,
                "weakness_tag": question.weakness_tag,
            }
        )
        case_ids.append(question.case_id)
        public_items.append(
            QuizVerificationPublic(
                item_id=item_id,
                fraud_type=parent_case.fraud_type,
                title=parent_case.title,
                narrative=parent_case.narrative,
                difficulty=question.difficulty,
                question=question.question,
                options=[
                    QuizVerificationOption(key=opt["key"], text=opt["text"])
                    for opt in question.options
                ],
            )
        )

    # 公開牌序與 session 權威牌序必須一致，避免客戶端重排答案操縱 streak。
    shuffle(public_items)
    stored_by_item_id = {str(item["item_id"]): item for item in stored_items}
    stored_items = [stored_by_item_id[item.item_id] for item in public_items]
    # 一次性結算 token 同時鎖定題目索引與全部底層 case id。
    quiz = QuizSession(user_id=current_user.id, case_ids=case_ids, items=stored_items)
    if material.mirror_relaxed_count:
        logger.warning(
            "quiz 牌組 %s 放寬鏡像排除 %d 張",
            quiz.id,
            material.mirror_relaxed_count,
        )
    session.add(quiz)
    session.commit()
    session.refresh(quiz)
    return QuizDeckResponse(session_id=str(quiz.id), items=public_items)


def _quiz_session_id(raw_session_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(raw_session_id)
    except ValueError:
        raise HTTPException(404, {"code": "quiz_session_not_found"}) from None


def _get_quiz_session(
    session: Session,
    *,
    raw_session_id: str,
    user_id: uuid.UUID,
    for_update: bool,
) -> QuizSession:
    session_id = _quiz_session_id(raw_session_id)
    statement = select(QuizSession).where(QuizSession.id == session_id)
    if for_update:
        statement = statement.with_for_update()
    quiz = session.exec(statement).first()
    if quiz is None:
        raise HTTPException(404, {"code": "quiz_session_not_found"})
    if quiz.user_id != user_id:
        raise HTTPException(403, {"code": "not_your_quiz_session"})
    return quiz


def _quiz_items(quiz: QuizSession) -> list[dict[str, Any]]:
    if not isinstance(quiz.items, list):
        return []
    return [item for item in quiz.items if isinstance(item, dict)]


def _quiz_case_ids(quiz: QuizSession) -> set[int]:
    if not isinstance(quiz.case_ids, list):
        return set()
    return {case_id for case_id in quiz.case_ids if isinstance(case_id, int)}


def _quiz_answers(quiz: QuizSession) -> dict[str, Any]:
    if not isinstance(quiz.answers, dict):
        return {}
    return {key: value for key, value in quiz.answers.items() if isinstance(key, str)}


def _find_quiz_item(quiz: QuizSession, item_id: str) -> dict[str, Any] | None:
    for item in _quiz_items(quiz):
        if item.get("item_id") == item_id:
            return item
    return None


def _item_case(session: Session, quiz: QuizSession, item: dict[str, Any]) -> Any | None:
    case_id = item.get("case_id")
    if not isinstance(case_id, int) or case_id not in _quiz_case_ids(quiz):
        return None
    return get_case(session, case_id)


def _correct_match_pairs(
    session: Session, quiz: QuizSession, item: dict[str, Any]
) -> tuple[dict[str, str], dict[str, str]] | None:
    stored_pairs = item.get("pairs")
    if not isinstance(stored_pairs, list) or len(stored_pairs) != len(WEAKNESS_TAGS):
        return None
    correct_pairs: dict[str, str] = {}
    provenance_by_pair: dict[str, str] = {}
    used_case_ids: set[int] = set()
    for stored_pair in stored_pairs:
        if not isinstance(stored_pair, dict):
            return None
        pair_id = stored_pair.get("pair_id")
        case_id = stored_pair.get("case_id")
        if (
            not isinstance(pair_id, str)
            or not isinstance(case_id, int)
            or pair_id in correct_pairs
            or case_id in used_case_ids
            or case_id not in _quiz_case_ids(quiz)
        ):
            return None
        flag_index = stored_pair.get("flag_index")
        if not isinstance(flag_index, int):
            return None
        # 優先採用發牌時定版的 tag。game_cases 由外部策展管線管理,
        # 策展人可在玩家開著牌的時候調動 red_flags 順序;若這裡回頭讀即時資料,
        # 同一個 flag_index 會指到別的話術,把答對判成答錯,
        # 還會把錯誤的弱點寫進 weakness_summary 給出反向的教學建議。
        frozen_tag = stored_pair.get("tag")
        frozen_provenance = stored_pair.get("provenance")
        case = None
        if not (
            isinstance(frozen_tag, str)
            and frozen_tag in WEAKNESS_TAGS
            and isinstance(frozen_provenance, str)
        ):
            case = get_case(session, case_id)
            if case is None:
                return None
        if isinstance(frozen_provenance, str):
            provenance_by_pair[pair_id] = frozen_provenance
        else:
            if case is None:
                return None
            provenance_by_pair[pair_id] = case.provenance
        if isinstance(frozen_tag, str) and frozen_tag in WEAKNESS_TAGS:
            correct_pairs[pair_id] = frozen_tag
            used_case_ids.add(case_id)
            continue
        # 定版機制上線前發出的舊 session 沒有 tag,才回頭查 DB
        if case is None:
            return None
        if not 0 <= flag_index < len(case.red_flags):
            return None
        tag = case.red_flags[flag_index].get("tag")
        if not isinstance(tag, str) or tag not in WEAKNESS_TAGS:
            return None
        correct_pairs[pair_id] = tag
        used_case_ids.add(case_id)
    if set(correct_pairs.values()) != WEAKNESS_TAGS:
        return None
    return correct_pairs, provenance_by_pair


@router.post("/quiz/answer", response_model=QuizAnswerResponse)
def quiz_answer(
    payload: QuizAnswerRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    quiz = _get_quiz_session(
        session,
        raw_session_id=payload.session_id,
        user_id=current_user.id,
        for_update=True,
    )
    if quiz.completed:
        raise HTTPException(400, {"code": "quiz_already_completed"})
    item = _find_quiz_item(quiz, payload.item_id)
    if item is None:
        raise HTTPException(404, {"code": "quiz_item_not_found"})
    answers = _quiz_answers(quiz)
    if payload.item_id in answers:
        raise HTTPException(400, {"code": "quiz_item_already_answered"})

    response = _quiz_answer_response(session, quiz, item, payload)
    raw_answer = payload.model_dump(
        exclude={"session_id", "item_id"}, exclude_none=True
    )
    # JSONB 就地 mutate 不會被 ORM 偵測；必須整個重新指派。
    quiz.answers = {**answers, payload.item_id: raw_answer}
    session.add(quiz)
    session.commit()
    return response


def _quiz_answer_response(
    session: Session,
    quiz: QuizSession,
    item: dict[str, Any],
    payload: QuizAnswerItem,
) -> QuizAnswerResponse:
    item_type = item.get("type")
    if item_type == "verdict":
        case = _item_case(session, quiz, item)
        if case is None:
            raise HTTPException(404, {"code": "quiz_case_not_found"})
        correct = payload.guess_is_scam == case.is_scam
        # 策展不變量：legit 案例的 red_flags[].tag 一律為 null。
        weakness_tags = (
            case_tags(case.red_flags) if not correct and case.is_scam else set()
        )
        return QuizVerdictAnswerResponse(
            correct=correct,
            is_scam=case.is_scam,
            red_flags=[
                QuizRedFlag(tag=flag.get("tag"), text=str(flag.get("text", "")))
                for flag in case.red_flags
            ],
            provenance=case.provenance,
            tag_details=_weakness_details(weakness_tags),
        )
    if item_type == "tactics":
        case = _item_case(session, quiz, item)
        if case is None:
            raise HTTPException(404, {"code": "quiz_case_not_found"})
        correct_tags = case_tags(case.red_flags)
        tactics_result = score_tactics(correct_tags, payload.selected_tags)
        relevant_tags = correct_tags | tactics_result.extra_tags
        return QuizTacticsAnswerResponse(
            correct=tactics_result.correct,
            correct_tags=sorted(correct_tags),
            missed_tags=sorted(tactics_result.missed_tags),
            extra_tags=sorted(tactics_result.extra_tags),
            provenance=case.provenance,
            tag_details=_weakness_details(relevant_tags),
        )
    if item_type == "verification":
        correct_key = str(item.get("correct_key", ""))
        correct = bool(payload.selected_key) and payload.selected_key == correct_key
        tag = item.get("weakness_tag")
        weakness_tags = {tag} if not correct and isinstance(tag, str) else set()
        return QuizVerificationAnswerResponse(
            correct=correct,
            correct_key=correct_key,
            explanation=str(item.get("explanation", "")),
            provenance=str(item.get("provenance", "")),
            tag_details=_weakness_details(weakness_tags),
        )
    if item_type == "match":
        match_pairs = _correct_match_pairs(session, quiz, item)
        if match_pairs is None:
            raise HTTPException(404, {"code": "quiz_case_not_found"})
        correct_pairs, provenance_by_pair = match_pairs
        match_result = score_match(correct_pairs, payload.pairs)
        return QuizMatchAnswerResponse(
            correct=match_result.correct,
            results=[
                QuizMatchPairResult(
                    pair_id=pair_id,
                    correct_tag=tag,
                    correct=match_result.pair_correct[pair_id],
                    provenance=provenance_by_pair[pair_id],
                )
                for pair_id, tag in correct_pairs.items()
            ],
            tag_details=_weakness_details(set(match_result.incorrect_tags)),
        )
    raise HTTPException(404, {"code": "quiz_item_not_found"})


def _score_quiz_item(
    session: Session,
    quiz: QuizSession,
    item: dict[str, Any],
    answer: QuizAnswerItem,
) -> tuple[bool, list[str]] | None:
    item_type = item.get("type")
    if item_type == "verdict":
        case = _item_case(session, quiz, item)
        if case is None:
            return None
        correct = answer.guess_is_scam == case.is_scam
        correct_tags = case_tags(case.red_flags)
        # 策展不變量：legit 案例的 red_flags[].tag 一律為 null。
        weaknesses = sorted(correct_tags) if not correct and case.is_scam else []
        return correct, weaknesses
    if item_type == "tactics":
        case = _item_case(session, quiz, item)
        if case is None:
            return None
        correct_tags = case_tags(case.red_flags)
        tactics_result = score_tactics(correct_tags, answer.selected_tags)
        return tactics_result.correct, sorted(tactics_result.missed_tags)
    if item_type == "verification":
        correct_key = str(item.get("correct_key", ""))
        correct = bool(answer.selected_key) and answer.selected_key == correct_key
        tag = item.get("weakness_tag")
        weaknesses = [tag] if not correct and isinstance(tag, str) else []
        return correct, weaknesses
    if item_type == "match":
        match_pairs = _correct_match_pairs(session, quiz, item)
        if match_pairs is None:
            return None
        correct_pairs, _ = match_pairs
        match_result = score_match(correct_pairs, answer.pairs)
        return match_result.correct, match_result.incorrect_tags
    return None


def _dealt_quiz_items(quiz: QuizSession) -> dict[str, dict[str, Any]]:
    dealt: dict[str, dict[str, Any]] = {}
    for item in _quiz_items(quiz):
        item_id = item.get("item_id")
        if isinstance(item_id, str) and item_id not in dealt:
            dealt[item_id] = item
    return dealt


def _stored_quiz_answer(item_id: str, raw_answer: Any) -> QuizAnswerItem | None:
    if not isinstance(raw_answer, dict):
        return None
    try:
        return QuizAnswerItem.model_validate({"item_id": item_id, **raw_answer})
    except ValidationError:
        return None


@router.post("/quiz/complete", response_model=QuizCompleteResponse)
def quiz_complete(
    payload: QuizCompleteRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    # 驗證一次性結算 token:必須存在、屬於本人、且尚未結算(防跨請求重放刷獎)。
    # 以 SELECT ... FOR UPDATE 鎖列,讓同 session_id 的並發結算(雙擊/重試)序列化——
    # 第二筆會阻塞到第一筆 commit(已標記 completed)後才讀到,避免 TOCTOU 雙重發獎。
    quiz = _get_quiz_session(
        session,
        raw_session_id=payload.session_id,
        user_id=current_user.id,
        for_update=True,
    )
    if quiz.completed:
        raise HTTPException(400, {"code": "quiz_already_completed"})

    # server-authoritative：只讀發牌時的不可變 items 與逐題首次寫入的 answers。
    dealt = _dealt_quiz_items(quiz)
    stored_answers = _quiz_answers(quiz)

    correct_count = 0
    total = len(dealt)
    best_streak = 0
    streak = 0
    weakness: dict[str, int] = {}
    for item_id, item in dealt.items():
        answer = _stored_quiz_answer(item_id, stored_answers.get(item_id))
        if answer is None:
            streak = 0
            continue
        scored = _score_quiz_item(session, quiz, item, answer)
        if scored is None:
            logger.warning(
                "quiz 題目無法評分，按答錯計入：session_id=%s item_id=%s type=%s",
                quiz.id,
                item_id,
                item.get("type"),
            )
            streak = 0
            continue
        correct, weakness_tags = scored
        if correct:
            correct_count += 1
            streak += 1
            best_streak = max(best_streak, streak)
        else:
            streak = 0
            for tag in weakness_tags:
                weakness[tag] = weakness.get(tag, 0) + 1

    cash, xp = _quiz_reward(correct_count, best_streak)
    # 全專案鎖順序約定：先鎖玩法 session（此處 quiz_session），再鎖 user。
    # 不可反向取得，避免兩種資源交叉等待造成死鎖。
    current_user = lock_user(session, current_user)
    adjust_cash(current_user, cash, reason="quiz_reward")
    add_xp(current_user, xp, reason="quiz_reward")
    # 標記已結算與加獎同一 commit 原子化——不會有「已發獎但可重放」的中間態
    quiz.completed = True
    quiz.completed_at = datetime.now(timezone.utc)
    session.add(current_user)
    session.add(quiz)
    session.commit()

    summary = _weakness_summary(weakness)
    return QuizCompleteResponse(
        correct_count=correct_count,
        total=total,
        best_streak=best_streak,
        cash_earned=cash,
        xp_earned=xp,
        weakness_summary=summary,
    )
