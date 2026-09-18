"""情境模擬純規則層:裁決矩陣、獎懲、回合上限、tactics 累積。不碰 DB。"""

from __future__ import annotations

from app.core.weakness import WEAKNESS_LABELS, WEAKNESS_SUGGESTIONS, WEAKNESS_TAGS
from app.economy.chapters import apply_income_multiplier
from app.scenario.config import LEGIT_SIGNALS, MAX_TURNS, ScenarioEconomyConfig
from app.schemas import FlagItem

ACTION_REPORT = "report"
ACTION_COMPLY = "comply"
ACTION_SAFE_EXIT = "safe_exit"

OUTCOME_WIN_REPORT = "win_report"
OUTCOME_WIN_TRUST = "win_trust"
OUTCOME_SAFE_EXIT = "safe_exit"
OUTCOME_LOSE_SCAMMED = "lose_scammed"
OUTCOME_LOSE_MISREPORT = "lose_misreport"

XP_BY_OUTCOME: dict[str, int] = {
    OUTCOME_WIN_REPORT: 15,
    OUTCOME_WIN_TRUST: 12,
    OUTCOME_SAFE_EXIT: 10,
    OUTCOME_LOSE_SCAMMED: 0,
    OUTCOME_LOSE_MISREPORT: 0,
}


def resolve_judgment(persona_role: str, action: str) -> str:
    """確定性裁決:真相 = persona_role,絕不由 LLM 判定。"""
    if action == ACTION_SAFE_EXIT:
        return OUTCOME_SAFE_EXIT
    if action == ACTION_REPORT:
        return OUTCOME_WIN_REPORT if persona_role == "scam" else OUTCOME_LOSE_MISREPORT
    return OUTCOME_LOSE_SCAMMED if persona_role == "scam" else OUTCOME_WIN_TRUST


def outcome_deltas(
    outcome: str,
    econ: ScenarioEconomyConfig,
    has_evidence: bool = True,
    completed_chapters: int = 0,
) -> tuple[int, int]:
    """回傳 (cash_delta, xp_delta)。

    - 安全退出不提供可刷取的無條件現金，但給予謹慎求證 XP 獎勵。
    - 有效查證後勝出獲得完整獎勵（套用章節倍率）；盲猜不超過 100。
    """
    if outcome == OUTCOME_SAFE_EXIT:
        return 0, XP_BY_OUTCOME[OUTCOME_SAFE_EXIT]

    if outcome == OUTCOME_WIN_REPORT:
        base = econ.reward_win if has_evidence else min(100, econ.reward_win)
        cash = apply_income_multiplier(base, completed_chapters)
        return cash, XP_BY_OUTCOME[outcome]

    if outcome == OUTCOME_WIN_TRUST:
        cash = apply_income_multiplier(econ.reward_legit, completed_chapters)
        return cash, XP_BY_OUTCOME[outcome]

    if outcome == OUTCOME_LOSE_SCAMMED:
        return -econ.stake_loss, XP_BY_OUTCOME[outcome]

    if outcome == OUTCOME_LOSE_MISREPORT:
        return -econ.penalty_misreport, XP_BY_OUTCOME[outcome]

    return 0, 0


def can_send_message(player_turns: int) -> bool:
    return player_turns < MAX_TURNS


def accumulate_tactics(seen: list[str], new: list[str]) -> list[str]:
    """去重累積合法 weakness_tag;回傳新 list,不改動輸入。"""
    result = list(seen)
    for tag in new:
        if tag in WEAKNESS_TAGS and tag not in result:
            result.append(tag)
    return result


def build_flags(
    outcome: str, tactics_seen: list[str], fraud_type: str
) -> list[FlagItem]:
    """揭曉卡的破綻/警訊(scam 結局)、正當訊號(legit 結局)或安全退出處置文案。"""
    if outcome == OUTCOME_SAFE_EXIT:
        return [
            FlagItem(
                tag=None,
                label="安全退出處置",
                detail="主動暫停對話並保留查證空間，未輕信催促亦未草率指控，展現穩健成熟的自我保護意識。",
            )
        ]

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
