"""情境模擬純規則層:裁決矩陣、獎懲、回合上限、tactics 累積。不碰 DB。"""

from __future__ import annotations

from typing import Any

from app.core.weakness import WEAKNESS_LABELS, WEAKNESS_SUGGESTIONS, WEAKNESS_TAGS
from app.scenario.config import LEGIT_SIGNALS, MAX_TURNS, ScenarioEconomyConfig
from app.schemas import FlagItem

ACTION_REPORT = "report"
ACTION_COMPLY = "comply"
ACTION_SAFE_EXIT = "safe_exit"
ACTION_PAUSE = "pause"

OUTCOME_WIN_REPORT = "win_report"
OUTCOME_WIN_TRUST = "win_trust"
OUTCOME_SAFE_EXIT = "safe_exit"
OUTCOME_LOSE_SCAMMED = "lose_scammed"
OUTCOME_LOSE_MISREPORT = "lose_misreport"
OUTCOME_PAUSED = "paused"

XP_BY_OUTCOME: dict[str, int] = {
    OUTCOME_WIN_REPORT: 15,
    OUTCOME_WIN_TRUST: 12,
    OUTCOME_SAFE_EXIT: 10,
    OUTCOME_LOSE_SCAMMED: 0,
    OUTCOME_LOSE_MISREPORT: 0,
    OUTCOME_PAUSED: 0,
}


def resolve_judgment(
    persona_role: str,
    action: str,
    story_truth: str | None = None,
) -> str:
    """確定性裁決:真相來自 snapshot，絕不由 LLM 判定（C2 / C6）。"""
    if action == ACTION_PAUSE:
        return OUTCOME_PAUSED

    if action not in (ACTION_REPORT, ACTION_COMPLY, ACTION_SAFE_EXIT):
        raise ValueError(f"Unknown action: {action}")

    truth = story_truth or persona_role
    if action == ACTION_SAFE_EXIT:
        return OUTCOME_SAFE_EXIT

    if action == ACTION_REPORT:
        # 當真相為 scam 時舉報勝出；真相為 legit 或 pause_pending 時舉報為誤報
        return OUTCOME_WIN_REPORT if truth == "scam" else OUTCOME_LOSE_MISREPORT

    # action == ACTION_COMPLY
    # 當真相為 legit 時信任勝出；真相為 scam 或 pause_pending（未查核即配合）為受害
    return OUTCOME_WIN_TRUST if truth == "legit" else OUTCOME_LOSE_SCAMMED


def outcome_deltas(
    outcome: str,
    econ: ScenarioEconomyConfig,
    has_evidence: bool = True,
    completed_chapters: int = 0,
    shield_reduction: float = 0.0,
    negotiation_bonus: float = 0.0,
    is_new_referral: bool = False,
    tool_provided_new_info: bool = False,
    full_service_objective: bool = False,
    is_chapter_finale: bool = False,
    is_chat_life: bool = False,
    is_replay: bool = False,
    return_breakdown: bool = False,
) -> tuple[int, int] | tuple[int, int, dict[str, Any]]:
    """回傳 (cash_delta, xp_delta)；若 return_breakdown=True 則回傳 (cash, xp, breakdown)（C6 / A7）。

    計算規則：
    1. base * (1.15^chapter_level) 作為基準，chapter_level 上限為 5。
    2. chat 加成採加法：新轉介 +20%、有效新資訊 +10%、完整目標 +20%，上限 50%。
    3. 特殊首次跨角色章末事件以 2.5x 替代一般 chat 加成（不疊加 1.5）。
    4. 盲猜（無查證事證）勝出獎金上限 100，XP 上限 20。
    5. 安全退出不給予可刷取現金，但給予 10 XP 求證獎勵。
    6. 重放已完成案件 (is_replay=True) 獎金與 XP 為 0。
    """
    xp_base = XP_BY_OUTCOME.get(outcome, 0)
    xp_reward = int(xp_base * (1.0 + max(0.0, negotiation_bonus)))
    if not has_evidence and outcome != OUTCOME_SAFE_EXIT:
        xp_reward = min(20, xp_reward)

    chapter_level = min(completed_chapters, 5)
    chapter_mult = 1.15 ** chapter_level

    chat_bonuses: dict[str, float] = {}
    if is_new_referral:
        chat_bonuses["new_referral"] = 0.20
    if tool_provided_new_info:
        chat_bonuses["effective_tool_info"] = 0.10
    if full_service_objective:
        chat_bonuses["full_service_objective"] = 0.20

    total_chat_factor = min(0.50, sum(chat_bonuses.values()))

    base_cash = 0
    final_cash = 0

    if outcome == OUTCOME_PAUSED:
        base_cash = 0
        final_cash = 0
        xp_reward = 0
    elif outcome == OUTCOME_SAFE_EXIT:
        base_cash = 0
        final_cash = 0
        xp_reward = XP_BY_OUTCOME[OUTCOME_SAFE_EXIT]
        if full_service_objective or has_evidence:
            xp_reward = int(xp_reward * (1.0 + total_chat_factor))
    elif outcome == OUTCOME_WIN_REPORT:
        base_cash = econ.reward_win
        if is_chapter_finale:
            final_cash = round(base_cash * chapter_mult * 2.5)
        else:
            final_cash = round(base_cash * chapter_mult * (1.0 + total_chat_factor))
        if not has_evidence:
            final_cash = min(100, final_cash)
    elif outcome == OUTCOME_WIN_TRUST:
        base_cash = econ.reward_win if is_chat_life else econ.reward_legit
        if is_chapter_finale:
            final_cash = round(base_cash * chapter_mult * 2.5)
        else:
            final_cash = round(base_cash * chapter_mult * (1.0 + total_chat_factor))
        if not has_evidence:
            final_cash = min(100, final_cash)
    elif outcome == OUTCOME_LOSE_SCAMMED:
        base_cash = -econ.stake_loss
        loss = int(econ.stake_loss * (1.0 - min(0.75, max(0.0, shield_reduction))))
        final_cash = -loss
    elif outcome == OUTCOME_LOSE_MISREPORT:
        base_cash = -econ.penalty_misreport
        penalty = int(econ.penalty_misreport * (1.0 - min(0.75, max(0.0, shield_reduction))))
        final_cash = -penalty

    if is_replay:
        final_cash = 0
        xp_reward = 0

    if return_breakdown:
        chapter_subtotal = round(base_cash * chapter_mult)
        breakdown = {
            "base_cash": base_cash,
            "chapter_level": chapter_level,
            "chapter_multiplier": round(chapter_mult, 4),
            "chapter_subtotal": chapter_subtotal,
            "chat_bonuses": chat_bonuses,
            "total_chat_factor": round(total_chat_factor, 2),
            "is_chapter_finale": is_chapter_finale,
            "final_cash": final_cash,
            "final_xp": xp_reward,
            "is_replay": is_replay,
        }
        return final_cash, xp_reward, breakdown

    return final_cash, xp_reward




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
