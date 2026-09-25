"""練習重點:從作答紀錄算出每類詐騙的出題比例。純函式,不碰資料庫。

流程(見 app/practice/service.py):
    作答紀錄 → compute_stats → 分析器(Gemini)或 rule_plan → clamp_weights → PracticeProfile

**不論比例是誰決定的,最後一律經過 `clamp_weights` 與 `settle_focus`**:
分析器回傳怪東西(少一類、負數、全部塞給同一類)也不會讓發牌壞掉。
分析器的比例還要先過 `apply_rules`(表現一樣的比例一樣、比較弱的不能比較低),
不合就整份改用規則版。
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from random import random
from typing import TypeVar

from app.core.fraud_types import FRAUD_TYPE_LABELS, FRAUD_TYPES
from app.core.weakness import WEAKNESS_LABELS

MODE_LABELS: dict[str, str] = {
    "pretest": "前測",
    "swipe": "滑卡",
    "quiz": "題組",
    "scenario": "情境對抗",
}

STATS_WINDOW = 80
"""只看最近 80 題。舊的弱點練起來之後會自然淡出,不會被幾週前的紀錄綁住。"""

RECENT = 30
"""最近 30 題加倍計算:剛剛一直錯的類型,比很久以前錯的更該多練。"""

MIN_ANSWERS = 5
"""少於 5 題不調整,樣本太少,錯一題就會被當成弱點。"""

MIN_WEIGHT = 0.08
"""每類至少 8%。弱項以外的也要練到,否則其他類型會越練越生疏。"""

MAX_WEIGHT = 0.5
"""單一類最多一半。配對題需要五類各一張;整副同一類玩家也很快就膩了。"""

UNIFORM_SPREAD = 0.05
"""最高與最低比例相差不到 5 個百分點時,視為沒有明顯弱項,不指定練習重點。"""


@dataclass(frozen=True)
class TypeStats:
    attempts: int = 0
    wrong: int = 0
    recent_attempts: int = 0
    recent_wrong: int = 0


@dataclass(frozen=True)
class AnswerRow:
    """作答紀錄的最小描述,與 ORM 解耦,方便測試。"""

    mode: str
    fraud_type: str
    correct: bool
    missed_tags: Sequence[str] = ()


@dataclass(frozen=True)
class PracticeStats:
    by_type: dict[str, TypeStats]
    by_mode: dict[str, tuple[int, int]] = field(default_factory=dict)
    """{mode: (題數, 答錯)}"""
    missed_tags: dict[str, int] = field(default_factory=dict)
    total: int = 0


@dataclass(frozen=True)
class PracticePlan:
    weights: dict[str, float]
    focus_type: str | None
    note: str
    source: str


def compute_stats(answers: Sequence[AnswerRow]) -> PracticeStats:
    """`answers` 由新到舊排列(最新的在前)。"""
    counts = {ft: [0, 0, 0, 0] for ft in FRAUD_TYPES}
    by_mode: dict[str, list[int]] = {}
    missed: dict[str, int] = {}
    for index, row in enumerate(answers[:STATS_WINDOW]):
        if row.fraud_type not in counts:
            continue
        bucket = counts[row.fraud_type]
        bucket[0] += 1
        bucket[1] += 0 if row.correct else 1
        if index < RECENT:
            bucket[2] += 1
            bucket[3] += 0 if row.correct else 1
        mode = by_mode.setdefault(row.mode, [0, 0])
        mode[0] += 1
        mode[1] += 0 if row.correct else 1
        for tag in row.missed_tags:
            missed[tag] = missed.get(tag, 0) + 1
    return PracticeStats(
        by_type={ft: TypeStats(*values) for ft, values in counts.items()},
        by_mode={mode: (n, wrong) for mode, (n, wrong) in by_mode.items()},
        missed_tags=missed,
        total=sum(values[0] for values in counts.values()),
    )


def clamp_weights(weights: Mapping[str, float]) -> dict[str, float]:
    """補齊五類、去掉負數,再把每類夾在 [MIN_WEIGHT, MAX_WEIGHT] 之間,合計為 1。

    做法:找一個倍數 t,讓 Σ clip(t × 原比例, 下限, 上限) = 1(二分搜尋)。
    這樣原本的大小順序會保留,而且一定湊得到 1。

    不能「先正規化、再把超出範圍的固定住」:只給一類的時候,那一類觸頂(0.5)、
    其他四類觸底(0.08),全部都被固定,合計只有 0.82,沒有任何一類能吸收剩下的量。
    每類加一個極小值,是讓原本是 0 的類型也能往上長。
    """
    raw = [max(0.0, float(weights.get(ft, 0.0) or 0.0)) for ft in FRAUD_TYPES]
    peak = max(raw)
    if peak <= 0:
        return {ft: round(1 / len(FRAUD_TYPES), 4) for ft in FRAUD_TYPES}
    raw = [value / peak + 1e-9 for value in raw]

    def total(scale: float) -> float:
        return sum(min(MAX_WEIGHT, max(MIN_WEIGHT, scale * value)) for value in raw)

    low, high = 0.0, 1.0
    while total(high) < 1:
        high *= 2
    for _ in range(100):
        mid = (low + high) / 2
        if total(mid) < 1:
            low = mid
        else:
            high = mid
    clipped = [min(MAX_WEIGHT, max(MIN_WEIGHT, high * value)) for value in raw]
    return {ft: round(value, 4) for ft, value in zip(FRAUD_TYPES, clipped, strict=True)}


def worse_than(a: TypeStats, b: TypeStats) -> bool:
    """a 的表現明顯比 b 差:錯的不比 b 少、對的不比 b 多,而且兩者不完全一樣。

    全部題目與最近 30 題分開比,所以「一樣錯 2 題,a 是最近錯的」也算 a 比較差。
    只比得出「明顯比較差」;像「錯 3 題共 10 題」對「錯 1 題共 1 題」這種
    題數和錯誤率互相拉扯的情況,兩邊都不算比較差,交給分析器判斷。
    """
    a_right = (a.attempts - a.wrong, a.recent_attempts - a.recent_wrong)
    b_right = (b.attempts - b.wrong, b.recent_attempts - b.recent_wrong)
    return (
        a != b
        and a.wrong >= b.wrong
        and a.recent_wrong >= b.recent_wrong
        and a_right[0] <= b_right[0]
        and a_right[1] <= b_right[1]
    )


def apply_rules(
    weights: Mapping[str, float], stats: PracticeStats
) -> dict[str, float] | None:
    """分析器給的比例要先過兩條規則,回傳合計為 1 的比例;不合就回傳 None(改用規則版)。

    1. 表現完全一樣的類型,比例要一樣。不一樣就取平均:前測只錯假交友時,
       其他四類都是全對,分析器卻給 20/10/20/10,這種差別沒有根據。
    2. 表現明顯比較差的類型(見 worse_than),比例不能比較低。
       不合代表分析器看錯了統計,整份不採用。

    規則版自己一定符合這兩條(錯越多、對越少,分數越高),見測試。
    """
    raw = {ft: max(0.0, float(weights.get(ft, 0.0) or 0.0)) for ft in FRAUD_TYPES}
    total = sum(raw.values())
    if total <= 0:
        return None
    share = {ft: value / total for ft, value in raw.items()}

    # 先檢查規則 2 再取平均:平均會把「全對的那類給最高」這種錯誤攤掉,看不出來。
    for a in FRAUD_TYPES:
        for b in FRAUD_TYPES:
            if (
                worse_than(stats.by_type[a], stats.by_type[b])
                and share[a] < share[b] - 1e-6
            ):
                return None

    groups: dict[TypeStats, list[str]] = {}
    for ft in FRAUD_TYPES:
        groups.setdefault(stats.by_type[ft], []).append(ft)
    for members in groups.values():
        mean = sum(share[ft] for ft in members) / len(members)
        for ft in members:
            share[ft] = mean
    return share


def settle_focus(
    weights: Mapping[str, float],
    proposed: str | None = None,
    stats: PracticeStats | None = None,
) -> str | None:
    """決定練習重點。

    比例幾乎平均時不指定 —— 否則題組會把一個根本不弱的類型偏重到六成。
    分析器提議的類型只有在它確實是比例最高(或並列最高)時才採用,
    不然就以比例為準,兩者不能互相矛盾。
    並列最高時,表現明顯比另一個並列者好的類型不能當重點(有 stats 才檢查)。
    """
    top = max(weights.values())
    if top - min(weights.values()) < UNIFORM_SPREAD:
        return None
    leaders = [ft for ft in FRAUD_TYPES if weights.get(ft, 0.0) >= top - 1e-9]
    if stats is not None:
        leaders = [
            ft
            for ft in leaders
            if not any(
                worse_than(stats.by_type[other], stats.by_type[ft]) for other in leaders
            )
        ]
        # 表現完全一樣的類型不分先後,照固定順序取同組的第一個(與前測結果頁的
        # 最弱類型一致),不讓分析器在兩個同分的類型之間隨意挑一個。
        if proposed in leaders:
            same = stats.by_type[proposed]
            proposed = next(ft for ft in leaders if stats.by_type[ft] == same)
    if proposed in leaders:
        return proposed
    return leaders[0]


def rule_plan(stats: PracticeStats) -> PracticePlan:
    """不靠 AI 的比例:錯誤率越高比例越高,最近的錯誤加倍計算。

    錯誤率用 (錯 + 1) / (題數 + 3) 估,題數少的類型不會因為錯一題就衝到最高。
    """
    raw: dict[str, float] = {}
    for ft, s in stats.by_type.items():
        attempts = s.attempts + s.recent_attempts
        wrong = s.wrong + s.recent_wrong
        raw[ft] = ((wrong + 1) / (attempts + 3)) ** 1.5
    weights = clamp_weights(raw)
    focus = settle_focus(weights, stats=stats)
    return PracticePlan(weights, focus, rule_note(stats, focus), "rule")


def rule_note(stats: PracticeStats, focus: str | None) -> str:
    if focus is None:
        return "目前各類答得差不多，接下來每一類平均練習。"
    s = stats.by_type[focus]
    label = FRAUD_TYPE_LABELS[focus]
    # 規則版會把沒練過或練得少的類型排高(不知道弱不弱,先多練),這時不能說「答錯 0 題」
    if s.attempts == 0:
        return f"「{label}」還沒練過，接下來會多排這一類。"
    if s.wrong == 0:
        return f"「{label}」練得比較少，接下來會多排這一類。"
    return f"最近在「{label}」答錯 {s.wrong} 題（共 {s.attempts} 題），接下來會多練這一類。"


def stats_for_prompt(stats: PracticeStats) -> str:
    """給分析器看的統計表。用中文類型名,讓它寫給玩家的說明直接可用。"""
    lines = ["類型 | 題數 | 答錯 | 最近30題中的題數 | 最近30題中答錯"]
    for ft in FRAUD_TYPES:
        s = stats.by_type[ft]
        lines.append(
            f"{FRAUD_TYPE_LABELS[ft]}({ft}) | {s.attempts} | {s.wrong} | "
            f"{s.recent_attempts} | {s.recent_wrong}"
        )
    # 玩法與話術也給中文名:給英文代號,分析器寫說明時常會照抄,
    # 那句說明就會被 usable_note 擋掉、退回規則版。
    if stats.by_mode:
        modes = "、".join(
            f"{MODE_LABELS.get(mode, mode)} {n} 題錯 {wrong} 題"
            for mode, (n, wrong) in stats.by_mode.items()
        )
        lines.append(f"各玩法:{modes}")
    if stats.missed_tags:
        tags = "、".join(
            f"{WEAKNESS_LABELS.get(tag, tag)} {n} 次"
            for tag, n in stats.missed_tags.items()
        )
        lines.append(f"答錯時漏掉的話術:{tags}")
    return "\n".join(lines)


T = TypeVar("T")


def weighted_order(
    items: Sequence[T], type_of: Callable[[T], str], weights: Mapping[str, float]
) -> list[T]:
    """依類型比例排出一個隨機順序,前 k 個就是「照比例抽 k 張」。

    每張卡的權重 = 類型比例 ÷ 該類型的張數,所以抽出來的**類型分布**跟比例一致,
    不會因為某一類卡片比較多就被抽得比較多。排序鍵用 random() ** (1 / 權重)
    (Efraimidis–Spirakis 加權抽樣),一次排好,不必逐張重抽。
    """
    counts: dict[str, int] = {}
    for item in items:
        counts[type_of(item)] = counts.get(type_of(item), 0) + 1

    def key(item: T) -> float:
        ft = type_of(item)
        weight = weights.get(ft, MIN_WEIGHT) / counts[ft]
        return float(random() ** (1 / weight)) if weight > 0 else 0.0

    return sorted(items, key=key, reverse=True)
