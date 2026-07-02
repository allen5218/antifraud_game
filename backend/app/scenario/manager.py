"""情境模擬純規則層:裁決矩陣、獎懲、回合上限、tactics 累積。不碰 DB。"""

from __future__ import annotations

from app.core.weakness import WEAKNESS_LABELS, WEAKNESS_SUGGESTIONS, WEAKNESS_TAGS
from app.scenario.config import LEGIT_SIGNALS, MAX_TURNS, ScenarioEconomyConfig
from app.schemas import FlagItem

ACTION_REPORT = "report"
ACTION_COMPLY = "comply"

OUTCOME_WIN_REPORT = "win_report"
OUTCOME_WIN_TRUST = "win_trust"
OUTCOME_LOSE_SCAMMED = "lose_scammed"
OUTCOME_LOSE_MISREPORT = "lose_misreport"

XP_BY_OUTCOME: dict[str, int] = {
    OUTCOME_WIN_REPORT: 15,
    OUTCOME_WIN_TRUST: 12,
    OUTCOME_LOSE_SCAMMED: 0,
    OUTCOME_LOSE_MISREPORT: 0,
}


def resolve_judgment(persona_role: str, action: str) -> str:
    """確定性裁決:真相 = persona_role,絕不由 LLM 判定。"""
    if action == ACTION_REPORT:
        return OUTCOME_WIN_REPORT if persona_role == "scam" else OUTCOME_LOSE_MISREPORT
    return OUTCOME_LOSE_SCAMMED if persona_role == "scam" else OUTCOME_WIN_TRUST


def outcome_deltas(outcome: str, econ: ScenarioEconomyConfig) -> tuple[int, int]:
    """回傳 (cash_delta, xp_delta)。"""
    cash = {
        OUTCOME_WIN_REPORT: econ.reward_win,
        OUTCOME_WIN_TRUST: econ.reward_legit,
        OUTCOME_LOSE_SCAMMED: -econ.stake_loss,
        OUTCOME_LOSE_MISREPORT: -econ.penalty_misreport,
    }[outcome]
    return cash, XP_BY_OUTCOME[outcome]


def can_send_message(player_turns: int) -> bool:
    return player_turns < MAX_TURNS


def accumulate_tactics(seen: list[str], new: list[str]) -> list[str]:
    """去重累積合法 weakness_tag;回傳新 list,不改動輸入。"""
    result = list(seen)
    for tag in new:
        if tag in WEAKNESS_TAGS and tag not in result:
            result.append(tag)
    return result


def build_flags(outcome: str, tactics_seen: list[str], fraud_type: str) -> list[FlagItem]:
    """揭曉卡的破綻/警訊(scam 結局)或正當訊號(legit 結局)。"""
    if outcome in (OUTCOME_WIN_REPORT, OUTCOME_LOSE_SCAMMED):
        return [
            FlagItem(
                tag=tag,
                label=WEAKNESS_LABELS.get(tag, tag),
                detail=WEAKNESS_SUGGESTIONS.get(tag, ""),
            )
            for tag in tactics_seen
        ]
    return [
        FlagItem(tag=None, label="正當訊號", detail=signal)
        for signal in LEGIT_SIGNALS.get(fraud_type, [])
    ]
