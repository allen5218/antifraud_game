import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import FraudType, PretestQuestion, PretestResult
from app.schemas import (
    FraudTypeResult,
    PretestSubmitRequest,
    PretestSubmitResponse,
)

router = APIRouter(prefix="/pretest", tags=["pretest"])


@router.get("/questions")
def get_pretest_questions(session: SessionDep, current_user: CurrentUser) -> Any:  # noqa: ARG001
    """每種詐騙類型隨機抽 3 題，共 15 題。回傳時不包含 is_correct 欄位。"""
    questions: list[PretestQuestion] = []
    for fraud_type in FraudType:
        statement = (
            select(PretestQuestion)
            .where(PretestQuestion.fraud_type == fraud_type.value)
            .limit(3)
        )
        rows = session.exec(statement).all()
        questions.extend(rows)

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
) -> Any:
    """批次判定前測答案，計算各類正確率，找出最弱類型。"""
    # 收集所有題目
    question_ids = [a.question_id for a in body.answers]
    statement = select(PretestQuestion).where(
        PretestQuestion.id.in_([uuid.UUID(qid) for qid in question_ids])  # type: ignore
    )
    questions_map: dict[str, PretestQuestion] = {
        str(q.id): q for q in session.exec(statement).all()
    }

    # 判定對錯並儲存結果
    type_stats: dict[str, dict[str, int]] = {}
    for answer in body.answers:
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

        # 統計
        ft = question.fraud_type
        if ft not in type_stats:
            type_stats[ft] = {"correct": 0, "total": 0}
        type_stats[ft]["total"] += 1
        if is_correct:
            type_stats[ft]["correct"] += 1

    session.commit()

    # 計算各類結果
    results_by_type = {
        ft: FraudTypeResult(correct=stats["correct"], total=stats["total"])
        for ft, stats in type_stats.items()
    }

    # 找最弱類型（正確率最低）
    weakest_type = min(
        type_stats.keys(),
        key=lambda ft: (
            type_stats[ft]["correct"] / type_stats[ft]["total"]
            if type_stats[ft]["total"] > 0
            else 0
        ),
    )

    return PretestSubmitResponse(
        results_by_type=results_by_type,
        weakest_type=weakest_type,
        ready_for_game=True,
    )
