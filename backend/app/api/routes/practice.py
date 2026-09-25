"""練習重點:玩家目前最需要加強哪一類、各類出題比例、為什麼。"""

from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.core.fraud_types import FRAUD_TYPE_LABELS
from app.core.pretest import latest_weakest_type
from app.practice.profile import clamp_weights
from app.practice.service import get_profile, practice_weights
from app.schemas import PracticeProfilePublic

router = APIRouter(prefix="/practice", tags=["practice"])


@router.get("/profile", response_model=PracticeProfilePublic)
def read_profile(session: SessionDep, current_user: CurrentUser) -> Any:
    profile = get_profile(session, current_user.id)
    if profile is not None:
        focus = profile.focus_type or None
        return PracticeProfilePublic(
            focus_type=focus,
            focus_label=FRAUD_TYPE_LABELS.get(focus) if focus else None,
            note=profile.note,
            weights=clamp_weights(profile.weights),
            source="gemini" if profile.source == "gemini" else "rule",
            answers_seen=profile.answers_seen,
        )

    # 還沒有練習重點(舊玩家只做過前測,或作答題數不到分析門檻)
    weakest = latest_weakest_type(session, current_user.id)
    if weakest is not None:
        return PracticeProfilePublic(
            focus_type=weakest,
            focus_label=FRAUD_TYPE_LABELS[weakest],
            note=f"前測顯示你在「{FRAUD_TYPE_LABELS[weakest]}」最容易失手，接下來會多練這一類。",
            weights=practice_weights(session, current_user.id) or {},
            source="pretest",
            answers_seen=0,
        )
    return PracticeProfilePublic(
        focus_type=None,
        focus_label=None,
        note="還沒有作答紀錄。先做前測，系統會找出你最需要加強的類型。",
        weights=clamp_weights({}),
        source="none",
        answers_seen=0,
    )
