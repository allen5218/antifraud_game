"""練習重點(app/practice/)的純邏輯測試:比例計算、分析器結果的防呆、加權抽卡。"""

import asyncio
import random
import uuid
from collections import Counter

import pytest
from pydantic_ai.models.test import TestModel

from app.core.fraud_types import FRAUD_TYPES
from app.practice import analyzer, service
from app.practice.profile import (
    MAX_WEIGHT,
    MIN_WEIGHT,
    AnswerRow,
    PracticePlan,
    TypeStats,
    apply_rules,
    clamp_weights,
    compute_stats,
    rule_plan,
    settle_focus,
    stats_for_prompt,
    weighted_order,
    worse_than,
)


def _plan(answers: list[AnswerRow]) -> PracticePlan | None:
    return asyncio.run(service.build_plan(answers))


def _answers(wrong_type: str, wrong: int, right_each: int = 4) -> list[AnswerRow]:
    """某一類答錯 `wrong` 題,其他類各答對 `right_each` 題。"""
    rows = [AnswerRow("quiz", wrong_type, False, ["greed"]) for _ in range(wrong)]
    for ft in FRAUD_TYPES:
        rows += [AnswerRow("swipe", ft, True) for _ in range(right_each)]
    return rows


def _pretest(wrong_type: str) -> list[AnswerRow]:
    """前測每類 4 題,只有 `wrong_type` 全錯、其他全對。"""
    return [
        AnswerRow("pretest", ft, ft != wrong_type)
        for ft in FRAUD_TYPES
        for _ in range(4)
    ]


# ── clamp_weights ────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw",
    [
        {"romance": 1.0},  # 只給一類
        {"romance": 5, "atm": -3},  # 有負數
        {},  # 全空
        dict.fromkeys(FRAUD_TYPES, 1),  # 平均
        {"romance": 100, "atm": 100, "investment": 0.001},  # 兩類搶
    ],
)
def test_clamp_weights_always_sums_to_one_within_bounds(raw: dict[str, float]) -> None:
    weights = clamp_weights(raw)
    assert set(weights) == set(FRAUD_TYPES)
    assert sum(weights.values()) == pytest.approx(1, abs=1e-3)
    assert all(MIN_WEIGHT - 1e-3 <= w <= MAX_WEIGHT + 1e-3 for w in weights.values())


def test_clamp_weights_keeps_order_of_preference() -> None:
    weights = clamp_weights({"romance": 6, "atm": 3, "investment": 1})
    assert weights["romance"] > weights["atm"] > weights["investment"]


# ── settle_focus ─────────────────────────────────────────────


def test_settle_focus_none_when_weights_are_even() -> None:
    assert settle_focus(clamp_weights({})) is None


def test_settle_focus_rejects_proposal_that_is_not_the_top_weight() -> None:
    weights = clamp_weights({"romance": 5, "atm": 1})
    assert settle_focus(weights, "atm") == "romance"
    assert settle_focus(weights, "romance") == "romance"


def test_settle_focus_among_ties_skips_the_type_that_did_better() -> None:
    """兩類並列最高,分析器提的是表現比較好的那一類 —— 重點要給比較弱的。"""
    stats = compute_stats(
        [AnswerRow("quiz", "romance", False)] * 4
        + [AnswerRow("quiz", "atm", False)] * 2
        + [AnswerRow("quiz", "atm", True)] * 2
    )
    weights = {"romance": 0.35, "atm": 0.35, **dict.fromkeys(FRAUD_TYPES[:3], 0.1)}
    assert settle_focus(weights, "atm", stats) == "romance"


def test_settle_focus_between_identical_types_uses_fixed_order() -> None:
    """兩類表現完全一樣時不聽分析器挑,照固定順序,跟前測結果頁的最弱類型一致。"""
    answers = [
        AnswerRow("pretest", ft, ft not in ("shopping", "romance"))
        for ft in FRAUD_TYPES
        for _ in range(4)
    ]
    stats = compute_stats(answers)
    weights = {
        "romance": 0.28,
        "shopping": 0.28,
        **dict.fromkeys(("investment", "fake-sale", "atm"), 0.147),
    }
    first = next(ft for ft in FRAUD_TYPES if ft in ("shopping", "romance"))
    assert settle_focus(weights, "romance", stats) == first
    assert settle_focus(weights, "shopping", stats) == first


# ── 比例規則(apply_rules / worse_than)────────────────────────


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (TypeStats(4, 4, 4, 4), TypeStats(4, 0, 4, 0), True),  # 全錯 vs 全對
        (TypeStats(2, 0, 2, 0), TypeStats(8, 0, 8, 0), True),  # 都全對,a 練得少
        (TypeStats(4, 2, 4, 2), TypeStats(4, 2, 4, 2), False),  # 完全一樣
        (TypeStats(10, 3, 5, 1), TypeStats(1, 1, 1, 1), False),  # 錯比較多但也對比較多
        # 一樣 4 題錯 2 題,最近 2 題 b 全錯、a 全對
        (TypeStats(4, 2, 2, 0), TypeStats(4, 2, 2, 2), False),
        (TypeStats(4, 2, 2, 2), TypeStats(4, 2, 2, 0), True),
    ],
)
def test_worse_than(a: TypeStats, b: TypeStats, expected: bool) -> None:
    assert worse_than(a, b) is expected


def test_apply_rules_evens_out_types_with_identical_results() -> None:
    """前測只錯假交友,其他四類全對 —— 那四類的比例要一樣。"""
    stats = compute_stats(_pretest("romance"))
    shares = apply_rules(
        {"investment": 20, "fake-sale": 10, "shopping": 20, "romance": 40, "atm": 10},
        stats,
    )
    assert shares is not None
    others = {shares[ft] for ft in FRAUD_TYPES if ft != "romance"}
    assert len(others) == 1 and others.pop() == pytest.approx(0.15)
    assert shares["romance"] == pytest.approx(0.4)


def test_apply_rules_rejects_weaker_type_getting_less() -> None:
    stats = compute_stats(_pretest("romance"))
    assert apply_rules({"romance": 0.1, "atm": 0.3}, stats) is None
    assert apply_rules({}, stats) is None


def test_rule_plan_always_passes_the_rules() -> None:
    """規則版是分析器不合格時的退路,自己也必須符合同樣的規則。"""
    rng = random.Random(7)
    for _ in range(300):
        answers = [
            AnswerRow("quiz", rng.choice(FRAUD_TYPES), rng.random() < 0.6)
            for _ in range(rng.randint(5, 80))
        ]
        stats = compute_stats(answers)
        plan = rule_plan(stats)
        assert apply_rules(plan.weights, stats) is not None
        if plan.focus_type is not None:
            assert not any(
                worse_than(stats.by_type[ft], stats.by_type[plan.focus_type])
                for ft in FRAUD_TYPES
            )


# ── rule_plan ────────────────────────────────────────────────


def test_rule_plan_focuses_the_type_answered_wrong_most() -> None:
    plan = rule_plan(compute_stats(_answers("romance", 6)))
    assert plan.focus_type == "romance"
    assert max(plan.weights, key=plan.weights.__getitem__) == "romance"
    assert "假交友" in plan.note and "6" in plan.note
    assert plan.source == "rule"


def test_rule_plan_is_even_when_everything_is_right() -> None:
    plan = rule_plan(compute_stats(_answers("romance", 0)))
    assert plan.focus_type is None
    assert "平均" in plan.note


def test_rule_note_for_a_type_never_practised() -> None:
    """規則版會把沒練過的類型排高;說明不能寫成「答錯 0 題(共 0 題)」。"""
    answers = [AnswerRow("quiz", ft, True) for ft in FRAUD_TYPES[:4] for _ in range(4)]
    plan = rule_plan(compute_stats(answers))
    assert plan.focus_type == FRAUD_TYPES[4]
    assert "還沒練過" in plan.note and "0 題" not in plan.note


def test_recent_mistakes_count_more_than_old_ones() -> None:
    """最近答錯的類型,比很久以前答錯的更該多練。"""
    recent = [AnswerRow("quiz", "atm", False) for _ in range(4)]
    filler = [AnswerRow("swipe", ft, True) for ft in FRAUD_TYPES for _ in range(6)]
    old = [AnswerRow("quiz", "romance", False) for _ in range(4)]
    plan = rule_plan(compute_stats(recent + filler + old))  # 新到舊
    assert plan.weights["atm"] > plan.weights["romance"]


def test_stats_for_prompt_uses_chinese_names() -> None:
    """玩法與話術給中文名,分析器才不會把英文代號抄進給玩家看的說明。"""
    text = stats_for_prompt(compute_stats(_answers("romance", 6)))
    assert "題組" in text and "滑卡" in text
    assert "quiz" not in text and "swipe" not in text
    assert "用好處引誘你" in text and "greed" not in text


# ── weighted_order ───────────────────────────────────────────


def test_weighted_order_follows_type_weights_not_card_counts() -> None:
    """romance 只有 6 張、其他類各 30 張,比例給 romance 一半,抽出來仍約一半是 romance。"""
    cards = [("romance", i) for i in range(6)] + [
        (ft, i) for ft in FRAUD_TYPES if ft != "romance" for i in range(30)
    ]
    weights = clamp_weights(
        {"romance": 5, **{ft: 1.25 for ft in FRAUD_TYPES if ft != "romance"}}
    )
    counts: Counter[str] = Counter()
    for _ in range(400):
        for ft, _ in weighted_order(cards, lambda c: c[0], weights)[:4]:
            counts[ft] += 1
    share = counts["romance"] / sum(counts.values())
    assert 0.4 < share < 0.6, share


# ── 分析器(Gemini)結果的防呆 ─────────────────────────────


def _fake_output(**overrides: object) -> dict[str, object]:
    output: dict[str, object] = {
        "weights": {
            "investment": 0.1,
            "fake_sale": 0.1,
            "shopping": 0.1,
            "romance": 0.6,
            "atm": 0.1,
        },
        "focus_type": "romance",
        "note": "最近假交友錯了 6 題，接下來會多練這一類",
    }
    output.update(overrides)
    return output


@pytest.fixture
def gemini(monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    """開啟分析器,並用 TestModel 取代真的 Gemini。回傳一個設定假輸出的函式。"""
    monkeypatch.setattr(analyzer, "enabled", lambda: True)

    def use(output: dict[str, object]):  # type: ignore[no-untyped-def]
        return analyzer.analyzer_agent.override(
            model=TestModel(custom_output_args=output)
        )

    return use


def test_build_plan_uses_gemini_output_after_clamping(gemini) -> None:  # type: ignore[no-untyped-def]
    with gemini(_fake_output()):
        plan = _plan(_answers("romance", 6))
    assert plan is not None and plan.source == "gemini"
    assert plan.focus_type == "romance"
    assert plan.weights["romance"] == pytest.approx(MAX_WEIGHT)  # 0.6 被夾到上限
    assert plan.note == "最近假交友錯了 6 題，接下來會多練這一類"


def test_build_plan_replaces_note_with_english(gemini) -> None:  # type: ignore[no-untyped-def]
    with gemini(_fake_output(note="Practice more romance scams")):
        plan = _plan(_answers("romance", 6))
    assert plan is not None
    assert "romance" not in plan.note and "假交友" in plan.note


def test_build_plan_corrects_focus_that_contradicts_weights(gemini) -> None:  # type: ignore[no-untyped-def]
    """分析器說重點是 atm、比例卻給 romance 最高 —— 以比例為準,說明也不能講 atm。"""
    with gemini(_fake_output(focus_type="atm", note="最近解除分期錯最多")):
        plan = _plan(_answers("romance", 6))
    assert plan is not None
    assert plan.focus_type == "romance"
    assert "解除分期" not in plan.note


def test_build_plan_evens_out_uneven_gemini_weights(gemini) -> None:  # type: ignore[no-untyped-def]
    """2026-09-25 實測:前測只錯假交友,Gemini 給了 20/10/20/40/10。"""
    weights = {
        "investment": 0.2,
        "fake_sale": 0.1,
        "shopping": 0.2,
        "romance": 0.4,
        "atm": 0.1,
    }
    with gemini(_fake_output(weights=weights, note="前測假交友錯了 4 題")):
        plan = _plan(_pretest("romance"))
    assert plan is not None and plan.source == "gemini"
    assert plan.focus_type == "romance"
    assert len({plan.weights[ft] for ft in FRAUD_TYPES if ft != "romance"}) == 1
    assert plan.note == "前測假交友錯了 4 題"


def test_build_plan_falls_back_when_gemini_breaks_the_rules(gemini) -> None:  # type: ignore[no-untyped-def]
    """假交友全錯,Gemini 卻把最高比例給全對的投資 —— 整份不採用。"""
    weights = {
        "investment": 0.4,
        "fake_sale": 0.1,
        "shopping": 0.1,
        "romance": 0.3,
        "atm": 0.1,
    }
    with gemini(_fake_output(weights=weights, focus_type="investment")):
        plan = _plan(_pretest("romance"))
    assert plan is not None and plan.source == "rule"
    assert plan.focus_type == "romance"


def test_build_plan_replaces_note_with_invented_numbers(gemini) -> None:  # type: ignore[no-untyped-def]
    with gemini(_fake_output(note="假交友錯了 9 題，比例提高到 60%")):
        plan = _plan(_answers("romance", 6))
    assert plan is not None
    assert "9" not in plan.note and "60" not in plan.note


def test_build_plan_falls_back_to_rules_when_gemini_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(analyzer, "enabled", lambda: True)

    async def fail(_stats: object) -> None:
        return None

    monkeypatch.setattr(analyzer, "analyze", fail)
    plan = _plan(_answers("romance", 6))
    assert plan is not None and plan.source == "rule"
    assert plan.focus_type == "romance"


def test_build_plan_needs_enough_answers() -> None:
    assert _plan([AnswerRow("quiz", "romance", False)] * 3) is None


@pytest.mark.parametrize(
    ("note", "usable"),
    [
        ("最近假交友錯了 6 題", True),
        ("最近假交友錯了 ６ 題", True),  # 全形數字
        ("最近假交友錯了 7 題", False),  # 統計裡沒有 7
        ("最近假交友錯了 30 題", False),  # 30 只出現在表頭「最近30題」
        ("最近假交友錯了七題", False),  # 中文數字
        ("假交友錯了 4 題", False),  # 4 是答對的題數,不是錯題數
        ("最近投資詐騙錯了 6 題", False),  # 沒講練習重點那一類
        ("假交友錯了 6 題，投資詐騙都對", False),  # 提到別的類型
        ("妳最近假交友錯了 6 題", True),  # 「妳」會換成「你」
        ("", False),
        ("Practice romance more", False),
        ("很" * 61, False),
    ],
)
def test_usable_note(note: str, usable: bool) -> None:
    stats = compute_stats(_answers("romance", 6))
    assert (analyzer.usable_note(note, stats, "romance") is not None) is usable


# ── 背景分析的排隊與節流 ─────────────────────────────────────


def test_refresh_runs_one_at_a_time_per_player(monkeypatch: pytest.MonkeyPatch) -> None:
    """分析中又結算三輪:不會同時跑四次,只在跑完後補跑一次。"""
    calls: list[str] = []
    gate = asyncio.Event()

    async def fake_once(_user_id: uuid.UUID) -> None:
        calls.append("run")
        if len(calls) == 1:
            await gate.wait()

    monkeypatch.setattr(service, "_refresh_once", fake_once)
    monkeypatch.setattr(analyzer, "enabled", lambda: False)
    user = uuid.uuid4()

    async def scenario() -> None:
        first = asyncio.create_task(service.refresh_profile(user))
        await asyncio.sleep(0)
        for _ in range(3):
            await service.refresh_profile(user)  # 正在跑,只記下要補跑
        gate.set()
        await first

    asyncio.run(scenario())
    assert calls == ["run", "run"]


def test_refresh_waits_between_gemini_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """有呼叫 Gemini 時,同一位玩家兩次分析至少隔 REFRESH_COOLDOWN 秒。"""
    started: list[float] = []

    async def fake_once(_user_id: uuid.UUID) -> None:
        started.append(asyncio.get_running_loop().time())

    monkeypatch.setattr(service, "_refresh_once", fake_once)
    monkeypatch.setattr(service, "REFRESH_COOLDOWN", 0.2)
    monkeypatch.setattr(analyzer, "enabled", lambda: True)
    user = uuid.uuid4()

    async def scenario() -> None:
        await service.refresh_profile(user)
        await service.refresh_profile(user)

    asyncio.run(scenario())
    assert len(started) == 2 and started[1] - started[0] >= 0.19
