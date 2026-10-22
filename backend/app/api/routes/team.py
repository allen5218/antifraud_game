"""團隊題庫：全部題目與答案，以及每一題底下的討論。只給團隊成員與管理員。"""

import os
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlmodel import col, select

from app.api.deps import CurrentUser, SessionDep
from app.core.cases import list_published_for_team, list_verification_questions_for_team
from app.core.fraud_types import FRAUD_TYPES
from app.core.weakness import WEAKNESS_LABELS
from app.models import PretestQuestion, SwipeCard, TeamComment, User
from app.scenario.agent import (
    SKILLS_DIR,
    _frontmatter,
    _persona_path,
    read_persona_meta,
)
from app.schemas import (
    TeamBank,
    TeamCase,
    TeamCommentCreate,
    TeamCommentPublic,
    TeamFlag,
    TeamItemKind,
    TeamOption,
    TeamPersona,
    TeamPretest,
    TeamQuestion,
    TeamSkill,
    TeamSwipe,
)


def has_team_access(user: User) -> bool:
    return user.is_team or user.is_superuser


def require_team(current_user: CurrentUser) -> User:
    # 權限不足用 400：前端收到 401／403 會直接登出
    if not has_team_access(current_user):
        raise HTTPException(status_code=400, detail={"code": "team_required"})
    return current_user


TeamUser = Annotated[User, Depends(require_team)]
router = APIRouter(prefix="/team", tags=["team"], dependencies=[Depends(require_team)])


def _body_without_frontmatter(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    front = _frontmatter(text)
    if front:
        text = text.split(f"---\n{front}\n---", 1)[1]
    return text.strip()


def _personas() -> list[TeamPersona]:
    personas = []
    for fraud_type in FRAUD_TYPES:
        for pool in ("practice", "exam"):
            for role in ("scam", "legit"):
                meta = read_persona_meta(fraud_type, role, pool)
                personas.append(
                    TeamPersona(
                        key=f"{fraud_type}:{pool}:{role}",
                        pool=pool,
                        fraud_type=fraud_type,
                        role=role,
                        name=meta.name,
                        teaser=meta.teaser,
                        primary_tactics=meta.primary_tactics,
                        body=_body_without_frontmatter(
                            _persona_path(fraud_type, role, pool)
                        ),
                    )
                )
    return personas


def _skills() -> list[TeamSkill]:
    return [
        TeamSkill(
            fraud_type=fraud_type,
            body=_body_without_frontmatter(
                os.path.join(SKILLS_DIR, f"fraud-{fraud_type}", "SKILL.md")
            ),
        )
        for fraud_type in FRAUD_TYPES
    ]


def _options(
    raw: list[dict[str, Any]], correct_key: str | None = None
) -> list[TeamOption]:
    return [
        TeamOption(
            key=str(o["key"]),
            text=str(o["text"]),
            is_correct=bool(o.get("is_correct")) or o["key"] == correct_key,
        )
        for o in raw
    ]


@router.get("/bank", response_model=TeamBank)
def read_bank(session: SessionDep) -> TeamBank:
    cases = list_published_for_team(session)
    case_keys = {c.id: c.case_key for c in cases}
    pretest = session.exec(
        select(PretestQuestion).order_by(
            col(PretestQuestion.fraud_type), col(PretestQuestion.seed_key)
        )
    ).all()
    swipe = session.exec(
        select(SwipeCard).order_by(
            col(SwipeCard.pool), col(SwipeCard.fraud_type), col(SwipeCard.seed_key)
        )
    ).all()
    counts = session.exec(
        select(TeamComment.item_kind, TeamComment.item_key, func.count()).group_by(
            col(TeamComment.item_kind), col(TeamComment.item_key)
        )
    ).all()
    return TeamBank(
        pretest=[
            TeamPretest(
                key=q.seed_key or str(q.id),
                fraud_type=q.fraud_type,
                is_scam=q.is_scam,
                difficulty=q.difficulty,
                question=q.question_text,
                options=_options(q.options),
                explanation=q.explanation,
            )
            for q in pretest
        ],
        swipe=[
            TeamSwipe(
                key=c.seed_key or str(c.id),
                pool=c.pool,
                fraud_type=c.fraud_type,
                is_scam=c.is_scam,
                difficulty=c.difficulty,
                source_label=c.source_label,
                scenario=c.scenario,
                weakness_tags=c.weakness_tags,
                explanation=c.explanation,
            )
            for c in swipe
        ],
        cases=[
            TeamCase(
                key=c.case_key,
                pool=c.pool,
                fraud_type=c.fraud_type,
                is_scam=c.is_scam,
                difficulty=c.difficulty,
                title=c.title,
                narrative=c.narrative,
                red_flags=[
                    TeamFlag(tag=f.get("tag"), text=str(f.get("text", "")))
                    for f in c.red_flags
                ],
                provenance=c.provenance,
                mirror_key=c.mirror_key,
                pattern_key=c.pattern_key,
            )
            for c in cases
        ],
        questions=[
            TeamQuestion(
                key=q.question_key,
                case_key=case_keys.get(q.case_id, str(q.case_id)),
                question_kind=q.question_kind,
                difficulty=q.difficulty,
                question=q.question,
                options=_options(q.options, q.correct_key),
                explanation=q.explanation,
                weakness_tag=q.weakness_tag,
                provenance=q.provenance,
            )
            for q in list_verification_questions_for_team(session)
        ],
        personas=_personas(),
        skills=_skills(),
        tactic_labels=dict(WEAKNESS_LABELS),
        comment_counts={f"{kind}:{key}": n for kind, key, n in counts},
    )


def _author(user: User | None) -> str:
    if user is None:
        return "已刪除的帳號"
    # 不顯示 email：團隊題庫的留言可能被截圖分享
    return (
        user.full_name
        or user.nickname
        or ("管理員" if user.is_superuser else "團隊成員")
    )


def _public(comment: TeamComment, author: User | None, me: User) -> TeamCommentPublic:
    return TeamCommentPublic(
        id=str(comment.id),
        item_kind=comment.item_kind,
        item_key=comment.item_key,
        body=comment.body,
        author=_author(author),
        mine=comment.user_id == me.id,
        created_at=comment.created_at.isoformat(),
    )


@router.get("/comments", response_model=list[TeamCommentPublic])
def list_comments(
    item_kind: TeamItemKind, item_key: str, session: SessionDep, me: TeamUser
) -> list[TeamCommentPublic]:
    rows = session.exec(
        select(TeamComment, User)
        .join(User, col(User.id) == col(TeamComment.user_id), isouter=True)
        .where(TeamComment.item_kind == item_kind, TeamComment.item_key == item_key)
        .order_by(col(TeamComment.created_at), col(TeamComment.id))
    ).all()
    return [_public(comment, author, me) for comment, author in rows]


@router.post("/comments", response_model=TeamCommentPublic)
def create_comment(
    body: TeamCommentCreate, session: SessionDep, me: TeamUser
) -> TeamCommentPublic:
    comment = TeamComment(
        user_id=me.id,
        item_kind=body.item_kind,
        item_key=body.item_key,
        body=body.body,
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return _public(comment, me, me)


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: uuid.UUID, session: SessionDep, me: TeamUser) -> None:
    comment = session.get(TeamComment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail={"code": "comment_not_found"})
    # 只能刪自己的；管理員可以刪任何一則
    if comment.user_id != me.id and not me.is_superuser:
        raise HTTPException(status_code=400, detail={"code": "not_comment_owner"})
    session.delete(comment)
    session.commit()
