import uuid
from random import shuffle
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import FraudType, PretestAttempt, PretestQuestion, PretestResult
from app.practice.service import queue_refresh, record_answers
from app.schemas import (
    FraudTypeResult,
    PretestSubmitRequest,
    PretestSubmitResponse,
)

router = APIRouter(prefix="/pretest", tags=["pretest"])


QUESTIONS_PER_TYPE = 4
"""每類抽幾題。三題太少:錯一題就差三成,量出來的「最弱類型」大半是運氣。"""


def _pick_for_type(rows: list[PretestQuestion]) -> list[PretestQuestion]:
    """詐騙情境與正常情境各抽一半。

    全部都是詐騙情境的話,「每題都選最保守的那個」就能拿高分,
    量到的是謹慎程度,不是辨識能力(LINE 模擬考 13 題有 12 題是陷阱,就是這個問題)。
    題庫某一邊不夠時,由另一邊或未標記的題目補滿。
    """
    half = QUESTIONS_PER_TYPE // 2
    scams = [q for q in rows if q.is_scam is True][:half]
    legits = [q for q in rows if q.is_scam is False][:half]
    picked = scams + legits
    picked_ids = {q.id for q in picked}
    rest = [q for q in rows if q.id not in picked_ids]
    return picked + rest[: QUESTIONS_PER_TYPE - len(picked)]


@router.get("/questions")
def get_pretest_questions(session: SessionDep, current_user: CurrentUser) -> Any:  # noqa: ARG001
    """每類抽 QUESTIONS_PER_TYPE 題(詐騙與正常情境各半),打散順序後回傳。

    回傳時不包含 is_correct 與 is_scam。
    """
    questions: list[PretestQuestion] = []
    for fraud_type in FraudType:
        rows = session.exec(
            select(PretestQuestion)
            .where(PretestQuestion.fraud_type == fraud_type.value)
            .order_by(func.random())
        ).all()
        questions.extend(_pick_for_type(list(rows)))
    # 不打散的話,同一類的題目會連在一起,做到一半就猜得到這一段在考什麼
    shuffle(questions)

    if not questions:
        raise HTTPException(status_code=404, detail="No pretest questions found")

    # 移除正確答案標記，只回傳 key + text
    result = []
    for q in questions:
        safe_options = [{"key": o["key"], "text": o["text"]} for o in q.options]
        result.append(
            {
                "id": str(q.id),
                "fraud_type": q.fraud_type,
                "question_text": q.question_text,
                "options": safe_options,
                "difficulty": q.difficulty,
            }
        )
    return {"questions": result}


@router.post("/submit", response_model=PretestSubmitResponse)
def submit_pretest(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    body: PretestSubmitRequest,
    background_tasks: BackgroundTasks,
) -> Any:
    """批次判定前測答案，計算各類正確率，找出最弱類型。"""
    # 同一題只算第一次作答,題數也不能超過一份前測。答案會寫進練習紀錄,
    # 不擋的話同一題送 80 次就能把某一類灌成練習重點。
    seen: set[str] = set()
    answers = []
    for answer in body.answers:
        if answer.question_id in seen:
            continue
        seen.add(answer.question_id)
        answers.append(answer)
    answers = answers[: QUESTIONS_PER_TYPE * len(FraudType)]
    question_ids = [a.question_id for a in answers]
    statement = select(PretestQuestion).where(
        PretestQuestion.id.in_([uuid.UUID(qid) for qid in question_ids])  # type: ignore
    )
    questions_map: dict[str, PretestQuestion] = {
        str(q.id): q for q in session.exec(statement).all()
    }

    # 判定對錯並儲存結果
    type_stats: dict[str, dict[str, int]] = {}
    practice: list[tuple[str, bool, list[str]]] = []
    for answer in answers:
        question = questions_map.get(answer.question_id)
        if not question:
            continue

        # 找正確答案
        correct_option = next(
            (o["key"] for o in question.options if o.get("is_correct")),
            None,
        )
        is_correct = answer.selected_option == correct_option

        # 儲存 PretestResult
        pretest_result = PretestResult(
            user_id=current_user.id,
            fraud_type=question.fraud_type,
            question_id=question.id,
            selected_option=answer.selected_option,
            is_correct=is_correct,
        )
        session.add(pretest_result)
        practice.append((question.fraud_type, is_correct, []))

        # 統計
        ft = question.fraud_type
        if ft not in type_stats:
            type_stats[ft] = {"correct": 0, "total": 0}
        type_stats[ft]["total"] += 1
        if is_correct:
            type_stats[ft]["correct"] += 1

    # 五類都要有作答。只交一類的話,那一類必定是「最弱」,玩家就能自己挑練習重點
    # (練習重點那一類的情境對抗每日上限比較高)。
    if len(type_stats) < len(FraudType):
        raise HTTPException(status_code=400, detail="前測要五類都作答")

    # 計算各類結果
    results_by_type = {
        ft: FraudTypeResult(correct=stats["correct"], total=stats["total"])
        for ft, stats in type_stats.items()
    }

    # 找最弱類型（正確率最低）
    # 同分時照固定的類型順序取,練習重點(settle_focus)遇到表現一樣的也照這個順序,
    # 結果頁說的最弱類型才會和首頁的練習重點一致。
    weakest_type = min(
        [ft.value for ft in FraudType if ft.value in type_stats],
        key=lambda ft: (
            type_stats[ft]["correct"] / type_stats[ft]["total"]
            if type_stats[ft]["total"] > 0
            else 0
        ),
    )

    # 記下結論。題組發牌與情境收件匣會讀最近一次(app/core/pretest.py)。
    user_id = current_user.id
    session.add(PretestAttempt(user_id=user_id, weakest_type=weakest_type))
    # 同時寫進所有玩法共用的作答紀錄,交卷後在背景重新分析練習重點
    record_answers(session, user_id, "pretest", practice)
    session.commit()
    queue_refresh(background_tasks, session, user_id)

    return PretestSubmitResponse(
        results_by_type=results_by_type,
        weakest_type=weakest_type,
        ready_for_game=True,
    )
