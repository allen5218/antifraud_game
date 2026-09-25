"""快速測驗的純函式規則，不讀寫資料庫。"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from itertools import islice, permutations
from random import random
from typing import Any, NamedTuple

from app.core.cases import GameCaseRow
from app.core.weakness import WEAKNESS_TAGS

_MAX_FRAUD_TYPE_PERMUTATIONS = 200
_DIFFICULTY_LIMIT_BY_MAX_LEVEL = ((2, 1), (5, 2))

logger = logging.getLogger(__name__)


class DeckComposition(NamedTuple):
    verdict: int
    tactics: int
    match: int
    verification: int = 0


@dataclass(frozen=True)
class TacticsScore:
    correct: bool
    missed_tags: set[str]
    extra_tags: set[str]


@dataclass(frozen=True)
class MatchScore:
    correct: bool
    pair_correct: dict[str, bool]
    incorrect_tags: list[str]


@dataclass(frozen=True)
class MatchMaterial:
    case: GameCaseRow
    flag_index: int
    tag: str


@dataclass(frozen=True)
class QuizMaterial:
    verdict: list[GameCaseRow]
    tactics: list[GameCaseRow]
    match: list[MatchMaterial]
    mirror_relaxed_count: int = 0
    missing_match_tags: tuple[str, ...] = ()


def max_difficulty_for_level(level: int) -> int | None:
    """依玩家等級限制題目難度，避免新手第一副牌就遇到最難題而放棄。"""
    return next(
        (
            max_difficulty
            for max_level, max_difficulty in _DIFFICULTY_LIMIT_BY_MAX_LEVEL
            if level <= max_level
        ),
        None,
    )


def _is_mirror_compatible(
    case: GameCaseRow,
    cases_by_id: dict[int, GameCaseRow],
    selected_ids: set[int],
    *,
    enforce_mirror: bool,
) -> bool:
    if not enforce_mirror:
        return True
    return all(
        case.mirror_of != selected_id and cases_by_id[selected_id].mirror_of != case.id
        for selected_id in selected_ids
    )


FOCUS_SHARE = 0.6
"""做過前測的玩家,題組裡最弱類型佔的比例。

不給 100%:配對題需要五個不同類型的素材,整副同一類就湊不出來;
玩家一直看到同一類,也很快就膩了。
"""


def focus_quota(slots: int) -> int:
    """`slots` 個位置裡要留給最弱類型幾個。"""
    return math.ceil(slots * FOCUS_SHARE) if slots > 0 else 0


def case_slots(size: int, verification_count: int) -> DeckComposition:
    """一副牌的題型配置(查證題取實際抽到的數量)。"""
    return _compose_deck(size, verification_count)


def prioritize_fraud_type(
    cases: list[GameCaseRow],
    fraud_type: str,
    *,
    verdict_slots: int,
    tactics_slots: int,
    match_slots: int = 0,
    max_difficulty: int | None = None,
) -> list[GameCaseRow]:
    """把指定類型的幾張案例排到最前面,其餘維持原本(已打亂)的順序。

    `select_quiz_material` 依候選順序挑題,排在前面的先被選到,所以不必改動它
    那一整套約束(鏡像、詐騙與正常平衡、配對題需要不同類型、難度上限)。

    排在前面的有兩段,**順序對應選材的順序**:
    1. 給 verdict 的:詐騙與正常**輪流**。verdict 會輪流補較少的一邊,前排如果
       全是同一邊,另一邊就會從後面(別的類型)補。
    2. 給 tactics 的:只放**有兩個以上話術標籤的詐騙案例**,tactics 只收這種。
    兩段都不能有鏡像對 —— 鏡像對不能同副出現,會被選材規則跳過,
    實際偏重的比例就不準。

    **難度上限只管 verdict**(見 `_select_quiz_material`):新手的 verdict 只收難度 1,
    這一類剩下的案例如果都太難,verdict 那段就排不滿 —— 用不到的名額轉給 tactics,
    tactics 不看難度。不轉的話,低等級玩家的偏重會悄悄掉到只剩查證題。

    **配對題會拿走一張**:它需要五個不同類型,選材順序在 tactics 之前,
    這一類的名額會用掉排在最前面、符合標籤的那張詐騙案例 —— 常常正是留給 tactics 的。
    所以有配對題時,tactics 段多留一張備用。實測(新手、假交友):
    不留備用只有 13%,等於沒偏重。
    """
    quota = focus_quota(verdict_slots + tactics_slots)

    pool = [case for case in cases if case.fraud_type == fraud_type]
    easy = [
        case
        for case in pool
        if max_difficulty is None or case.difficulty <= max_difficulty
    ]
    scams = [case for case in easy if case.is_scam]
    legits = [case for case in easy if not case.is_scam]
    tactics_ready = [
        case for case in pool if case.is_scam and len(case_tags(case.red_flags)) >= 2
    ]

    chosen: list[GameCaseRow] = []
    chosen_ids: set[int] = set()

    def first_free(candidates: list[GameCaseRow]) -> GameCaseRow | None:
        """第一張還沒被選、也不和已選的任何一張互為鏡像的案例。"""
        return next(
            (
                case
                for case in candidates
                if case.id not in chosen_ids
                and case.mirror_of not in chosen_ids
                and not any(other.mirror_of == case.id for other in chosen)
            ),
            None,
        )

    def add(case: GameCaseRow) -> None:
        chosen.append(case)
        chosen_ids.add(case.id)

    # verdict 段:每一步都找「需要的那一邊」裡第一張不衝突的,找不到才拿另一邊。
    # 不能先交錯排好再逐張檢查 —— 題庫裡每則正常訊息幾乎都是某則詐騙的鏡像,
    # 固定交錯的話正常題會全部因為鏡像被跳過,前排只剩詐騙。
    want_scam = True
    for _ in range(min(quota, verdict_slots)):
        primary, fallback = (scams, legits) if want_scam else (legits, scams)
        case = first_free(primary) or first_free(fallback)
        if case is None:
            break
        add(case)
        want_scam = not case.is_scam

    for _ in range(min(quota - len(chosen), tactics_slots) + match_slots):
        case = first_free(tactics_ready)
        if case is None:
            break
        add(case)

    return chosen + [case for case in cases if case.id not in chosen_ids]


def verification_quota(size: int) -> int:
    """每三題配一題查證題；不足三題的小牌不出查證題。"""
    return max(1, min(size, 10)) // 3


def _compose_deck(size: int, verification_count: int = 0) -> DeckComposition:
    """依總題數分配題型；match 是五對配對重型題，每副牌最多一題。

    `verification_count` 由路由傳入「實際取到幾題」而非理論配額——查證題素材
    來自另一張子表，可能不足。取不到就讓 verdict／tactics 補回去，
    牌堆題數不會因此縮水。
    """
    clamped = max(1, min(size, 10))
    match_count = 1 if clamped >= 5 else 0
    remaining = clamped - match_count - verification_count
    verdict_count = (remaining + 1) // 2
    tactics_count = remaining // 2
    return DeckComposition(
        verdict_count, tactics_count, match_count, verification_count
    )


def case_tags(red_flags: list[dict[str, Any]]) -> set[str]:
    """取出案例中合法且去重的弱點標籤。"""
    return {
        tag
        for flag in red_flags
        if isinstance((tag := flag.get("tag")), str) and tag in WEAKNESS_TAGS
    }


def score_tactics(
    correct_tags: set[str], selected_tags: list[str] | None
) -> TacticsScore:
    """話術題僅在玩家選項集合與正解完全相等時得分。"""
    selected = set(selected_tags or [])
    missed = correct_tags - selected
    extra = selected - correct_tags
    return TacticsScore(not missed and not extra, missed, extra)


def score_match(
    correct_pairs: dict[str, str], submitted_pairs: dict[str, str] | None
) -> MatchScore:
    """配對題必須每一個 pair 都配對正確才得分。"""
    submitted = submitted_pairs or {}
    pair_correct = {
        pair_id: submitted.get(pair_id) == tag for pair_id, tag in correct_pairs.items()
    }
    incorrect_tags = [
        correct_pairs[pair_id]
        for pair_id, is_correct in pair_correct.items()
        if not is_correct
    ]
    return MatchScore(all(pair_correct.values()), pair_correct, incorrect_tags)


def _match_candidates(
    cases: list[GameCaseRow], excluded_ids: set[int]
) -> dict[str, list[MatchMaterial]]:
    candidates: dict[str, list[MatchMaterial]] = {tag: [] for tag in WEAKNESS_TAGS}
    seen_case_tags: set[tuple[int, str]] = set()
    for case in cases:
        if case.id in excluded_ids or not case.is_scam:
            continue
        for flag_index, flag in enumerate(case.red_flags):
            tag = flag.get("tag")
            if (
                not isinstance(tag, str)
                or tag not in WEAKNESS_TAGS
                or (case.id, tag) in seen_case_tags
            ):
                continue
            key = (case.id, tag)
            seen_case_tags.add(key)
            candidates[tag].append(MatchMaterial(case, flag_index, tag))
    return candidates


def _select_match_material(
    cases: list[GameCaseRow],
    excluded_ids: set[int],
    *,
    enforce_mirror: bool = True,
) -> list[MatchMaterial]:
    candidates = _match_candidates(cases, excluded_ids)
    cases_by_id = {case.id: case for case in cases}
    tags = sorted(WEAKNESS_TAGS, key=lambda tag: len(candidates[tag]))
    if any(not candidates[tag] for tag in tags):
        return []

    # 先嘗試五種不同 fraud_type；成功時 case 必然也各不相同。
    fraud_types = list(
        dict.fromkeys(
            candidate.case.fraud_type for tag in tags for candidate in candidates[tag]
        )
    )

    def assign_distinct_types(
        index: int,
        assigned_types: tuple[str, ...],
        selection: list[MatchMaterial],
        selected_ids: set[int],
    ) -> bool:
        if index == len(tags):
            return True
        tag = tags[index]
        fraud_type = assigned_types[index]
        for candidate in candidates[tag]:
            if (
                candidate.case.fraud_type != fraud_type
                or candidate.case.id in selected_ids
                or not _is_mirror_compatible(
                    candidate.case,
                    cases_by_id,
                    selected_ids,
                    enforce_mirror=enforce_mirror,
                )
            ):
                continue
            selection.append(candidate)
            selected_ids.add(candidate.case.id)
            if assign_distinct_types(
                index + 1, assigned_types, selection, selected_ids
            ):
                return True
            selection.pop()
            selected_ids.remove(candidate.case.id)
        return False

    if len(fraud_types) >= len(tags):
        # 外部策展資料的 fraud_type 沒有 CHECK 約束；限制排列搜尋，避免髒 slug
        # 讓同步發牌端點耗盡 CPU。超過上限時交由下方 MRV 回溯處理。
        assigned_type_options = islice(
            permutations(fraud_types, len(tags)), _MAX_FRAUD_TYPE_PERMUTATIONS
        )
        for assigned_types in assigned_type_options:
            distinct_type_selection: list[MatchMaterial] = []
            selected_ids = set(excluded_ids)
            if assign_distinct_types(
                0, assigned_types, distinct_type_selection, selected_ids
            ):
                return distinct_type_selection

    # fraud_type 無法全數去重時放寬，但仍以回溯保證五個 case 不重複。
    fallback_selection: list[MatchMaterial] = []
    used_case_ids = set(excluded_ids)
    used_fraud_types: set[str] = set()

    def assign(index: int) -> bool:
        if index == len(tags):
            return True
        tag = tags[index]
        ordered = sorted(
            candidates[tag],
            key=lambda candidate: candidate.case.fraud_type in used_fraud_types,
        )
        for candidate in ordered:
            if candidate.case.id in used_case_ids or not _is_mirror_compatible(
                candidate.case,
                cases_by_id,
                used_case_ids,
                enforce_mirror=enforce_mirror,
            ):
                continue
            fallback_selection.append(candidate)
            used_case_ids.add(candidate.case.id)
            added_fraud_type = candidate.case.fraud_type not in used_fraud_types
            used_fraud_types.add(candidate.case.fraud_type)
            if assign(index + 1):
                return True
            fallback_selection.pop()
            used_case_ids.remove(candidate.case.id)
            if added_fraud_type:
                used_fraud_types.remove(candidate.case.fraud_type)
        return False

    return fallback_selection if assign(0) else []


def _extend_balanced_verdict(
    verdict: list[GameCaseRow],
    cases: list[GameCaseRow],
    *,
    count: int,
    excluded_ids: set[int],
    enforce_mirror: bool = True,
    max_difficulty: int | None = None,
    prefer_scam_on_tie: bool,
) -> None:
    """優先補較少的一側，讓 verdict 的 scam/legit 數量盡量接近。"""
    scam_count = sum(case.is_scam for case in verdict)
    legit_count = len(verdict) - scam_count
    cases_by_id = {case.id: case for case in cases}
    available = [
        case
        for case in cases
        if case.id not in excluded_ids
        and (max_difficulty is None or case.difficulty <= max_difficulty)
    ]

    for _ in range(count):
        if scam_count == legit_count:
            prefer_scam = prefer_scam_on_tie
        else:
            prefer_scam = scam_count < legit_count
        selected = next(
            (
                case
                for case in available
                if case.is_scam is prefer_scam
                and _is_mirror_compatible(
                    case,
                    cases_by_id,
                    excluded_ids,
                    enforce_mirror=enforce_mirror,
                )
            ),
            None,
        )
        if selected is None:
            selected = next(
                (
                    case
                    for case in available
                    if case.is_scam is not prefer_scam
                    and _is_mirror_compatible(
                        case,
                        cases_by_id,
                        excluded_ids,
                        enforce_mirror=enforce_mirror,
                    )
                ),
                None,
            )
        if selected is None:
            return
        verdict.append(selected)
        excluded_ids.add(selected.id)
        available.remove(selected)
        if selected.is_scam:
            scam_count += 1
        else:
            legit_count += 1


def _extend_verdict_with_difficulty_limit(
    verdict: list[GameCaseRow],
    cases: list[GameCaseRow],
    *,
    count: int,
    excluded_ids: set[int],
    enforce_mirror: bool,
    max_difficulty: int | None,
    prefer_scam_on_tie: bool,
) -> None:
    """verdict 先依等級限難度，不足再放寬以優先發滿題數。"""
    original_count = len(verdict)
    _extend_balanced_verdict(
        verdict,
        cases,
        count=count,
        excluded_ids=excluded_ids,
        enforce_mirror=enforce_mirror,
        max_difficulty=max_difficulty,
        prefer_scam_on_tie=prefer_scam_on_tie,
    )
    missing = count - (len(verdict) - original_count)
    if missing:
        _extend_balanced_verdict(
            verdict,
            cases,
            count=missing,
            excluded_ids=excluded_ids,
            enforce_mirror=enforce_mirror,
            prefer_scam_on_tie=prefer_scam_on_tie,
        )


def _question_count(material: QuizMaterial) -> int:
    return len(material.verdict) + len(material.tactics) + bool(material.match)


def _case_question_total(composition: DeckComposition) -> int:
    """配額中「取自 game_cases 的題數」；查證題來自子表，不由此處選材。"""
    return composition.verdict + composition.tactics + composition.match


def _material_cases(material: QuizMaterial) -> list[GameCaseRow]:
    return [
        *material.verdict,
        *material.tactics,
        *(pair.case for pair in material.match),
    ]


def _mirror_relaxed_count(material: QuizMaterial) -> int:
    selected_ids: set[int] = set()
    cases = _material_cases(material)
    cases_by_id = {case.id: case for case in cases}
    relaxed_count = 0
    for case in cases:
        if not _is_mirror_compatible(
            case, cases_by_id, selected_ids, enforce_mirror=True
        ):
            relaxed_count += 1
        selected_ids.add(case.id)
    return relaxed_count


def _select_quiz_material(
    cases: list[GameCaseRow],
    *,
    size: int,
    enforce_mirror: bool,
    max_difficulty: int | None,
    prefer_scam_on_tie: bool,
    verification_count: int = 0,
) -> QuizMaterial:
    """先保留平衡 verdict，再選 tactics/match，並以 verdict 補足缺額。"""
    composition = _compose_deck(size, verification_count)
    used_case_ids: set[int] = set()

    verdict: list[GameCaseRow] = []
    # difficulty 描述「判斷是否為詐騙」的難度，只對 verdict 有意義；
    # tactics 與 match 測的是話術辨識／配對，若沿用此指標會測不準並餓死題庫。
    _extend_verdict_with_difficulty_limit(
        verdict,
        cases,
        count=composition.verdict,
        excluded_ids=used_case_ids,
        enforce_mirror=enforce_mirror,
        max_difficulty=max_difficulty,
        prefer_scam_on_tie=prefer_scam_on_tie,
    )

    cases_by_id = {case.id: case for case in cases}
    match: list[MatchMaterial] = []
    missing_match_tags: tuple[str, ...] = ()
    if composition.match:
        # match 必須先保留每個 tag 的稀缺素材；例如 social_proof 全庫僅少數案例，
        # 若先讓 tactics 取用，會讓本來可出的 match 隨機消失。
        candidates_by_tag = _match_candidates(cases, used_case_ids)
        missing_match_tags = tuple(
            tag for tag in sorted(WEAKNESS_TAGS) if not candidates_by_tag[tag]
        )
        selected_match = _select_match_material(
            cases, used_case_ids, enforce_mirror=enforce_mirror
        )
        selected_match_ids = {pair.case.id for pair in selected_match}
        target_size = composition.verdict + composition.tactics + composition.match
        backfill_needed = target_size - len(verdict) - bool(selected_match)
        ids_after_match = used_case_ids | selected_match_ids
        remaining_after_match = sum(
            case.id not in ids_after_match
            and _is_mirror_compatible(
                case,
                cases_by_id,
                ids_after_match,
                enforce_mirror=enforce_mirror,
            )
            for case in cases
        )
        if selected_match and remaining_after_match >= backfill_needed:
            match = selected_match
            used_case_ids.update(selected_match_ids)
            missing_match_tags = ()

    tactics: list[GameCaseRow] = []
    for case in cases:
        if (
            len(tactics) >= composition.tactics
            or case.id in used_case_ids
            or not case.is_scam
            or len(case_tags(case.red_flags)) < 2
            or not _is_mirror_compatible(
                case,
                cases_by_id,
                used_case_ids,
                enforce_mirror=enforce_mirror,
            )
        ):
            continue
        tactics.append(case)
        used_case_ids.add(case.id)

    target_size = composition.verdict + composition.tactics + composition.match
    current_size = len(verdict) + len(tactics) + bool(match)
    _extend_verdict_with_difficulty_limit(
        verdict,
        cases,
        count=target_size - current_size,
        excluded_ids=used_case_ids,
        enforce_mirror=enforce_mirror,
        max_difficulty=max_difficulty,
        prefer_scam_on_tie=prefer_scam_on_tie,
    )
    return QuizMaterial(
        verdict=verdict,
        tactics=tactics,
        match=match,
        missing_match_tags=missing_match_tags,
    )


def _log_material_shortages(
    material: QuizMaterial, *, size: int, verification_count: int = 0
) -> None:
    composition = _compose_deck(size, verification_count)
    missing_tactics = composition.tactics - len(material.tactics)
    if missing_tactics:
        logger.warning("quiz tactics 素材不足，缺少 %d 題", missing_tactics)
    if composition.match and not material.match:
        if material.missing_match_tags:
            logger.warning(
                "quiz match 素材不足，缺少 tag: %s",
                ", ".join(material.missing_match_tags),
            )
        else:
            logger.warning("quiz match 素材不足，缺少 1 題")


def _verdict_balance_gap(material: QuizMaterial) -> int:
    scam_count = sum(case.is_scam for case in material.verdict)
    return abs(scam_count - (len(material.verdict) - scam_count))


def _minimum_possible_verdict_gap(candidates: list[QuizMaterial]) -> int:
    """枚舉完成選材的候選，回傳素材與規則允許的最小 verdict 差距。

    候選已各自完整跑過難度、唯一性、mirror、tactics 與 match 規則；必要時
    兩種平手方向都會納入比較，若只有一個候選則它已達題數奇偶的理論下限。
    因此剩餘偏差只可能來自可行素材不足，不能再由先選哪一側的順序造成。
    """
    return min(_verdict_balance_gap(candidate) for candidate in candidates)


def _choose_balanced_candidate(candidates: list[QuizMaterial]) -> QuizMaterial:
    minimum_gap = _minimum_possible_verdict_gap(candidates)
    best = [
        candidate
        for candidate in candidates
        if _verdict_balance_gap(candidate) == minimum_gap
    ]
    if len(best) == 1:
        return best[0]
    # 候選順序已由本副牌唯一一次硬幣決定；同樣最佳時保留第一方向。
    return best[0]


def _selection_candidates(
    cases: list[GameCaseRow],
    *,
    size: int,
    enforce_mirror: bool,
    max_difficulty: int | None,
    prefer_scam_on_tie: bool,
    verification_count: int = 0,
) -> list[QuizMaterial]:
    primary = _select_quiz_material(
        cases,
        size=size,
        enforce_mirror=enforce_mirror,
        max_difficulty=max_difficulty,
        prefer_scam_on_tie=prefer_scam_on_tie,
        verification_count=verification_count,
    )
    target_size = _case_question_total(_compose_deck(size, verification_count))
    theoretical_minimum = len(primary.verdict) % 2
    if (
        _question_count(primary) == target_size
        and _verdict_balance_gap(primary) == theoretical_minimum
    ):
        return [primary]
    return [
        primary,
        _select_quiz_material(
            cases,
            size=size,
            enforce_mirror=enforce_mirror,
            max_difficulty=max_difficulty,
            prefer_scam_on_tie=not prefer_scam_on_tie,
            verification_count=verification_count,
        ),
    ]


def select_quiz_material(
    cases: list[GameCaseRow],
    *,
    size: int,
    max_difficulty: int | None = None,
    verification_count: int = 0,
) -> QuizMaterial:
    """依難度與鏡像規則分層選材；題數不足時依序放寬難度、鏡像。

    `verification_count` 是路由「實際取到的查證題數」，會從本函式要選的
    案例題數中扣掉——查證題素材來自 game_case_questions 子表，不經此處。
    """
    # 每副牌只擲一次硬幣；第二方向只在第一方向仍可能改善時才計算。
    prefer_scam_on_tie = random() < 0.5
    strict_candidates = _selection_candidates(
        cases,
        size=size,
        enforce_mirror=True,
        max_difficulty=max_difficulty,
        prefer_scam_on_tie=prefer_scam_on_tie,
        verification_count=verification_count,
    )
    target_size = _case_question_total(_compose_deck(size, verification_count))
    full_strict_candidates = [
        candidate
        for candidate in strict_candidates
        if _question_count(candidate) == target_size
    ]
    if full_strict_candidates:
        result = _choose_balanced_candidate(full_strict_candidates)
        _log_material_shortages(
            result, size=size, verification_count=verification_count
        )
        return result

    relaxed_candidates = _selection_candidates(
        cases,
        size=size,
        enforce_mirror=False,
        max_difficulty=max_difficulty,
        prefer_scam_on_tie=prefer_scam_on_tie,
        verification_count=verification_count,
    )
    fullest_count = max(_question_count(candidate) for candidate in relaxed_candidates)
    fullest_candidates = [
        candidate
        for candidate in relaxed_candidates
        if _question_count(candidate) == fullest_count
    ]
    relaxed = _choose_balanced_candidate(fullest_candidates)
    result = QuizMaterial(
        verdict=relaxed.verdict,
        tactics=relaxed.tactics,
        match=relaxed.match,
        mirror_relaxed_count=_mirror_relaxed_count(relaxed),
        missing_match_tags=relaxed.missing_match_tags,
    )
    _log_material_shortages(result, size=size, verification_count=verification_count)
    return result
