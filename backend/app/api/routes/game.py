import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.core.weakness import WEAKNESS_LABELS, WEAKNESS_SUGGESTIONS
from app.game.agent import GameDeps, create_game_agent
from app.game.manager import GameSessionManager
from app.models import (
    FraudType,
    GameAnswer,
    GameSession,
    GameStatus,
    PretestResult,
    UserScore,
)
from app.schemas import (
    AnswerRequest,
    AnswerResponse,
    AnswerResult,
    GameOverResult,
    GameStartRequest,
    MascotPopup,
    WeaknessDetail,
)

router = APIRouter(prefix="/game", tags=["game"])

manager = GameSessionManager()


@router.post("/start")
async def start_game(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    body: GameStartRequest,
) -> Any:
    """建立遊戲 session，呼叫 Agent 生成第一題。"""
    fraud_type = body.fraud_type
    pretest_weakness = "greed"

    if not fraud_type:
        statement = (
            select(PretestResult)
            .where(PretestResult.user_id == current_user.id)
            .order_by(PretestResult.created_at.desc())  # type: ignore
        )
        results = session.exec(statement).all()
        if results:
            type_stats: dict[str, dict[str, int]] = {}
            for r in results:
                if r.fraud_type not in type_stats:
                    type_stats[r.fraud_type] = {"correct": 0, "total": 0}
                type_stats[r.fraud_type]["total"] += 1
                if r.is_correct:
                    type_stats[r.fraud_type]["correct"] += 1
            if type_stats:
                fraud_type = min(
                    type_stats.keys(),
                    key=lambda ft: (
                        type_stats[ft]["correct"] / type_stats[ft]["total"]
                        if type_stats[ft]["total"] > 0
                        else 0
                    ),
                )

    if not fraud_type:
        fraud_type = FraudType.INVESTMENT.value

    game_session = GameSession(
        user_id=current_user.id,
        fraud_type=fraud_type,
        status=GameStatus.IN_PROGRESS,
    )
    session.add(game_session)
    session.commit()
    session.refresh(game_session)

    agent = create_game_agent()
    deps = GameDeps(session=game_session, pretest_weakness=pretest_weakness)
    result = await agent.run(
        f"開始一場關於「{fraud_type}」的反詐騙訓練遊戲，生成第一題。",
        deps=deps,
    )

    game_session.conversation_history = [
        {"role": "assistant", "content": result.output.model_dump()},
    ]
    session.add(game_session)
    session.commit()
    session.refresh(game_session)

    return {
        "session_id": str(game_session.id),
        "fraud_type": game_session.fraud_type,
        "first_question": result.output.model_dump(),
    }


@router.post("/{session_id}/answer", response_model=AnswerResponse)
async def submit_answer(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    session_id: uuid.UUID,
    body: AnswerRequest,
) -> Any:
    """處理答題：判定對錯、更新狀態、檢查吉祥物/結束、生成下一題。"""
    game_session = session.get(GameSession, session_id)
    if not game_session:
        raise HTTPException(status_code=404, detail="Game session not found")
    if game_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your game session")
    if game_session.status == GameStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Game already completed")

    last_question = None
    for entry in reversed(game_session.conversation_history):
        if entry.get("role") == "assistant":
            last_question = entry["content"]
            break
    if not last_question:
        raise HTTPException(status_code=400, detail="No question to answer")

    correct_option = last_question["correct_option"]
    is_correct = body.selected_option == correct_option
    difficulty = last_question.get("difficulty", 1)

    base_score = manager.calculate_score(is_correct, difficulty)

    game_session.current_step += 1
    if is_correct:
        game_session.total_correct += 1
    else:
        game_session.total_wrong += 1

    answer_entry = {
        "role": "answer",
        "selected_option": body.selected_option,
        "is_correct": is_correct,
    }
    history = list(game_session.conversation_history)
    history.append(answer_entry)
    game_session.conversation_history = history

    streak_bonus = manager.calculate_streak_bonus(game_session)
    total_earned = base_score + streak_bonus
    game_session.score += total_earned

    game_session.max_steps = manager.adjust_max_steps(game_session)

    game_answer = GameAnswer(
        session_id=game_session.id,
        step=game_session.current_step,
        question_type=last_question.get("question_type", "scenario"),
        question_text=last_question.get("question", ""),
        options=last_question.get("options", []),
        selected_option=body.selected_option,
        correct_option=correct_option,
        is_correct=is_correct,
        ai_explanation=last_question.get("explanation", ""),
        weakness_tag=last_question.get("weakness_tag"),
    )
    session.add(game_answer)

    mascot_popup = None
    if is_correct and manager.check_mascot_trigger(game_session):
        mascot_popup = MascotPopup(
            show=True,
            message=manager.get_mascot_message(game_session.total_correct),
        )

    game_over = None
    next_question = None

    if manager.check_game_over(game_session):
        game_session.status = GameStatus.COMPLETED
        game_session.completed_at = datetime.now(timezone.utc)

        total_questions = game_session.total_correct + game_session.total_wrong
        correct_rate = (
            game_session.total_correct / total_questions if total_questions > 0 else 0
        )
        grade = manager.calculate_grade(correct_rate)

        if correct_rate >= 0.9:
            game_session.score += 50
        elif correct_rate >= 0.7:
            game_session.score += 20

        wrong_answers = session.exec(
            select(GameAnswer).where(
                GameAnswer.session_id == game_session.id,
                GameAnswer.is_correct == False,  # noqa: E712
                GameAnswer.weakness_tag.is_not(None),  # type: ignore
            )
        ).all()

        weakness_counts: dict[str, int] = {}
        for wa in wrong_answers:
            if wa.weakness_tag:
                weakness_counts[wa.weakness_tag] = (
                    weakness_counts.get(wa.weakness_tag, 0) + 1
                )

        weakness_analysis = [
            WeaknessDetail(
                tag=tag,
                count=count,
                label=WEAKNESS_LABELS.get(tag, tag),
                suggestion=WEAKNESS_SUGGESTIONS.get(tag, "持續練習，提升辨識能力"),
            )
            for tag, count in sorted(
                weakness_counts.items(), key=lambda x: x[1], reverse=True
            )
        ]

        correct_answers = session.exec(
            select(GameAnswer).where(
                GameAnswer.session_id == game_session.id,
                GameAnswer.is_correct == True,  # noqa: E712
                GameAnswer.weakness_tag.is_not(None),  # type: ignore
            )
        ).all()
        strength_tags = list(
            {ca.weakness_tag for ca in correct_answers if ca.weakness_tag}
            - set(weakness_counts.keys())
        )

        game_over = GameOverResult(
            total_score=game_session.score,
            correct_rate=round(correct_rate, 2),
            grade=grade,
            weakness_analysis=weakness_analysis,
            strength_tags=strength_tags,
        )

        user_score = session.exec(
            select(UserScore).where(UserScore.user_id == current_user.id)
        ).first()
        if user_score:
            user_score.total_score += game_session.score
            user_score.games_played += 1
            session.add(user_score)
        else:
            user_score = UserScore(
                user_id=current_user.id,
                total_score=game_session.score,
                games_played=1,
            )
            session.add(user_score)
    else:
        agent = create_game_agent()
        deps = GameDeps(
            session=game_session,
            pretest_weakness=last_question.get("weakness_tag", "greed") or "greed",
        )
        answer_context = (
            f"玩家選擇了 {body.selected_option}，"
            f"{'答對了' if is_correct else '答錯了'}。"
            f"正確答案是 {correct_option}。"
            f"請生成下一題。"
        )
        ai_result = await agent.run(answer_context, deps=deps)
        next_question = ai_result.output

        history = list(game_session.conversation_history)
        history.append({"role": "assistant", "content": next_question.model_dump()})
        game_session.conversation_history = history

    session.add(game_session)
    session.commit()

    return AnswerResponse(
        answer_result=AnswerResult(
            is_correct=is_correct,
            correct_option=correct_option,
            explanation=last_question.get("explanation", ""),
            score_earned=total_earned,
            total_score=game_session.score,
        ),
        mascot_popup=mascot_popup,
        next_question=next_question,
        game_over=game_over,
    )


@router.get("/{session_id}")
def get_game_session(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    session_id: uuid.UUID,
) -> Any:
    """取得遊戲狀態（斷線重連用）。"""
    game_session = session.get(GameSession, session_id)
    if not game_session:
        raise HTTPException(status_code=404, detail="Game session not found")
    if game_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your game session")

    last_question = None
    for entry in reversed(game_session.conversation_history):
        if entry.get("role") == "assistant":
            last_question = entry["content"]
            break

    return {
        "session": {
            "id": str(game_session.id),
            "fraud_type": game_session.fraud_type,
            "status": game_session.status,
            "current_step": game_session.current_step,
            "total_correct": game_session.total_correct,
            "total_wrong": game_session.total_wrong,
            "score": game_session.score,
            "max_steps": game_session.max_steps,
        },
        "last_question": last_question,
        "can_resume": game_session.status == GameStatus.IN_PROGRESS,
    }
