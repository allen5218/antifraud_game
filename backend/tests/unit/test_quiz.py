import pytest

from app.core import quiz as quiz_core
from app.core.cases import GameCaseRow
from app.api.routes.quick import _cases_excluding
from app.core.quiz import (
    _compose_deck,
    _match_candidates,
    _select_match_material,
    case_tags,
    score_match,
    score_tactics,
    select_quiz_material,
)


def _case(
    case_id: int,
    *,
    fraud_type: str,
    is_scam: bool,
    tags: list[str | None],
    difficulty: int = 2,
    mirror_of: int | None = None,
) -> GameCaseRow:
    return GameCaseRow(
        id=case_id,
        fraud_type=fraud_type,
        is_scam=is_scam,
        title=f"案例 {case_id}",
        narrative="測試敘事",
        red_flags=[
            {"tag": tag, "text": f"例句 {case_id}-{index}"}
            for index, tag in enumerate(tags)
        ],
        difficulty=difficulty,
        provenance="pytest",
        mirror_of=mirror_of,
    )


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (1, (1, 0, 0)),
        (3, (2, 1, 0)),
        (5, (2, 2, 1)),
        (10, (5, 4, 1)),
    ],
)
def test_compose_deck_keeps_one_match_and_splits_the_rest(
    size: int, expected: tuple[int, int, int]
) -> None:
    composition = _compose_deck(size)

    assert (composition.verdict, composition.tactics, composition.match) == expected


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (1, (1, 0, 0, 0)),
        (2, (1, 1, 0, 0)),
        (3, (1, 1, 0, 1)),
        (5, (2, 1, 1, 1)),
        (10, (3, 3, 1, 3)),
    ],
)
def test_compose_deck_with_verification_keeps_all_four_types(
    size: int, expected: tuple[int, int, int, int]
) -> None:
    """查證題進來之後，四種題型都要還在，而且總題數不能縮水。"""
    quota = quiz_core.verification_quota(size)
    composition = _compose_deck(size, quota)

    assert tuple(composition) == expected
    assert sum(composition) == max(1, min(size, 10))


def test_compose_deck_backfills_when_no_verification_material() -> None:
    """查證題素材掛零時，verdict/tactics 要補回來，不能讓牌堆少一題。

    協作者原型的作法是硬扣 size-2，素材不足就讓 tactics 永遠發不出來。
    """
    composition = _compose_deck(5, 0)

    assert sum(composition) == 5
    assert composition.verification == 0
    assert composition.tactics > 0


def test_tactics_requires_exact_set() -> None:
    correct = {"time_pressure", "authority"}

    exact = score_tactics(correct, ["authority", "time_pressure"])
    missing = score_tactics(correct, ["time_pressure"])
    extra = score_tactics(correct, ["time_pressure", "authority", "greed"])

    assert exact.correct is True
    assert exact.missed_tags == set()
    assert exact.extra_tags == set()
    assert missing.correct is False
    assert missing.missed_tags == {"authority"}
    assert missing.extra_tags == set()
    assert extra.correct is False
    assert extra.missed_tags == set()
    assert extra.extra_tags == {"greed"}


def test_case_tags_dedupes_and_excludes_empty_or_unknown_tags() -> None:
    red_flags = [
        {"tag": "authority", "text": "冒充主管"},
        {"tag": "authority", "text": "再次施壓"},
        {"tag": None, "text": "一般訊號"},
        {"tag": "unknown", "text": "未知分類"},
    ]

    assert case_tags(red_flags) == {"authority"}


@pytest.mark.parametrize("invalid_tag", [None, 7, {"tag": "greed"}, ["greed"]])
def test_select_quiz_material_ignores_non_string_tags(invalid_tag: object) -> None:
    cases = [
        _case(1, fraud_type="investment", is_scam=True, tags=["authority", "greed"]),
        _case(2, fraud_type="shopping", is_scam=False, tags=[None]),
    ]
    cases.append(
        cases[0].model_copy(
            update={
                "id": 3,
                "red_flags": [{"tag": invalid_tag, "text": "髒資料"}],
            }
        )
    )

    candidates = _match_candidates(cases, set())

    assert all(pair.case.id != 3 for pairs in candidates.values() for pair in pairs)


def test_match_requires_every_pair_to_be_correct() -> None:
    correct = {
        "pair-a": "time_pressure",
        "pair-b": "authority",
        "pair-c": "greed",
        "pair-d": "social_proof",
        "pair-e": "trust_building",
    }

    exact = score_match(correct, correct.copy())
    one_wrong = score_match(correct, {**correct, "pair-e": "greed"})

    assert exact.correct is True
    assert all(exact.pair_correct.values())
    assert exact.incorrect_tags == []
    assert one_wrong.correct is False
    assert one_wrong.pair_correct["pair-e"] is False
    assert one_wrong.incorrect_tags == ["trust_building"]


def test_select_quiz_material_never_reuses_a_case_and_tactics_are_scam() -> None:
    tags = [
        "time_pressure",
        "authority",
        "greed",
        "social_proof",
        "trust_building",
    ]
    cases = [
        _case(
            case_id,
            fraud_type=f"type-{case_id % 5}",
            is_scam=True,
            tags=[tags[case_id % 5], tags[(case_id + 1) % 5]],
        )
        for case_id in range(15)
    ] + [
        _case(
            case_id,
            fraud_type=f"legit-{case_id}",
            is_scam=False,
            tags=[None, None],
        )
        for case_id in range(15, 25)
    ]

    material = select_quiz_material(cases, size=10)
    used_ids = [case.id for case in material.verdict]
    used_ids += [case.id for case in material.tactics]
    used_ids += [pair.case.id for pair in material.match]

    assert len(used_ids) == len(set(used_ids))
    assert len(material.verdict) == 5
    assert len(material.tactics) == 4
    assert len(material.match) == 5
    assert all(case.is_scam for case in material.tactics)
    verdict_scam = sum(case.is_scam for case in material.verdict)
    verdict_legit = len(material.verdict) - verdict_scam
    assert abs(verdict_scam - verdict_legit) <= 1


def test_select_quiz_material_omits_match_when_one_tag_is_missing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    cases = [
        _case(
            case_id,
            fraud_type=f"type-{case_id}",
            is_scam=True,
            tags=["time_pressure", "authority"],
        )
        for case_id in range(6)
    ]

    material = select_quiz_material(cases, size=5)

    assert len(material.verdict) == 3
    assert len(material.tactics) == 2
    assert material.match == []
    assert len(material.verdict) + len(material.tactics) == 5
    assert (
        "quiz match 素材不足，缺少 tag: greed, social_proof, trust_building"
        in caplog.text
    )


def test_select_quiz_material_backfills_missing_tactics_with_verdict(
    caplog: pytest.LogCaptureFixture,
) -> None:
    cases = [
        _case(
            case_id,
            fraud_type=f"type-{case_id}",
            is_scam=case_id < 2,
            tags=["time_pressure", "authority"] if case_id < 2 else [None],
        )
        for case_id in range(10)
    ]

    material = select_quiz_material(cases, size=5)

    assert len(material.tactics) == 1
    assert material.match == []
    assert len(material.verdict) == 4
    assert len(material.verdict) + len(material.tactics) == 5
    assert "quiz tactics 素材不足，缺少 1 題" in caplog.text


def test_select_quiz_material_prefers_five_fraud_types_for_match() -> None:
    tags = [
        "time_pressure",
        "authority",
        "greed",
        "social_proof",
        "trust_building",
    ]
    cases = [
        _case(
            index,
            fraud_type=f"type-{index % 5}",
            is_scam=True,
            tags=[tags[index % 5], tags[(index + 1) % 5]],
        )
        for index in range(15)
    ]

    material = select_quiz_material(cases, size=5)

    assert len(material.match) == 5
    assert len({pair.case.fraud_type for pair in material.match}) == 5


def test_match_fraud_type_permutations_are_capped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tags = [
        "time_pressure",
        "authority",
        "greed",
        "social_proof",
        "trust_building",
    ]
    cases = [
        _case(
            index,
            fraud_type=f"type-{index}",
            is_scam=True,
            tags=[tag],
        )
        for index, tag in enumerate(tags)
    ]

    def too_many_permutations(*_args: object, **_kwargs: object):
        for index in range(201):
            if index == 200:
                raise AssertionError("排列搜尋超過上限")
            yield tuple("missing" for _ in tags)

    monkeypatch.setattr(quiz_core, "permutations", too_many_permutations)

    selected = _select_match_material(cases, set())

    assert len(selected) == 5


def test_verdict_extra_item_does_not_always_favour_scam() -> None:
    """verdict 題數為奇數時,多出來的那題必須隨機落在 scam 或 legit。

    若永遠偏向同一側,玩家一律猜那一側就能穩定勝過 50%——
    這正是本專案在追殺的「不必懂反詐就能得分」。
    """
    fraud_types = ["investment", "shopping", "fake-sale", "romance", "atm"]
    cases = [
        _case(
            i,
            fraud_type=fraud_types[i % len(fraud_types)],
            is_scam=i % 2 == 0,
            tags=["greed", "authority"] if i % 2 == 0 else [],
        )
        for i in range(1, 41)
    ]
    seen_scam_counts = set()
    for _ in range(200):
        material = select_quiz_material(list(cases), size=5)
        seen_scam_counts.add(sum(case.is_scam for case in material.verdict))
    # 兩種都要出現過,才代表不是固定偏向某一側
    assert len(seen_scam_counts) > 1, f"verdict scam 數永遠是 {seen_scam_counts}"


def _skewed_cases(*, scam_count: int, legit_count: int) -> list[GameCaseRow]:
    tags = sorted(quiz_core.WEAKNESS_TAGS)
    scams = [
        _case(
            case_id,
            fraud_type=f"type-{case_id % 5}",
            is_scam=True,
            tags=[tags[case_id % 5], tags[(case_id + 1) % 5]],
            difficulty=1,
        )
        for case_id in range(scam_count)
    ]
    legit = [
        _case(
            100 + case_id,
            fraud_type=f"legit-{case_id}",
            is_scam=False,
            tags=[],
            difficulty=1,
        )
        for case_id in range(legit_count)
    ]
    return [*scams, *legit]


def test_select_quiz_material_finally_rebalances_10_scam_5_legit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(quiz_core, "random", lambda: 1.0)

    material = select_quiz_material(
        _skewed_cases(scam_count=10, legit_count=5), size=10
    )

    scam_count = sum(case.is_scam for case in material.verdict)
    legit_count = len(material.verdict) - scam_count
    assert abs(scam_count - legit_count) == 1


def test_select_quiz_material_skips_second_direction_at_theoretical_minimum(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selection_calls = 0
    original_select = quiz_core._select_quiz_material

    def count_selection(
        cases: list[GameCaseRow],
        *,
        size: int,
        enforce_mirror: bool,
        max_difficulty: int | None,
        prefer_scam_on_tie: bool,
        verification_count: int = 0,
    ) -> quiz_core.QuizMaterial:
        nonlocal selection_calls
        selection_calls += 1
        return original_select(
            cases,
            size=size,
            enforce_mirror=enforce_mirror,
            max_difficulty=max_difficulty,
            prefer_scam_on_tie=prefer_scam_on_tie,
            verification_count=verification_count,
        )

    monkeypatch.setattr(quiz_core, "_select_quiz_material", count_selection)
    monkeypatch.setattr(quiz_core, "random", lambda: 0.0)

    material = select_quiz_material(
        _skewed_cases(scam_count=10, legit_count=5), size=10
    )

    assert quiz_core._verdict_balance_gap(material) == 1
    assert selection_calls == 1


def test_select_quiz_material_10_scam_1_legit_keeps_material_minimum_and_coin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    random_calls = 0

    def choose_legit() -> float:
        nonlocal random_calls
        random_calls += 1
        return 1.0

    monkeypatch.setattr(quiz_core, "random", choose_legit)

    material = select_quiz_material(
        _skewed_cases(scam_count=10, legit_count=1), size=10
    )

    scam_count = sum(case.is_scam for case in material.verdict)
    legit_count = len(material.verdict) - scam_count
    assert abs(scam_count - legit_count) == 4
    assert random_calls == 1


def _material_cases(material: quiz_core.QuizMaterial) -> list[GameCaseRow]:
    return [
        *material.verdict,
        *material.tactics,
        *(pair.case for pair in material.match),
    ]


def test_select_quiz_material_excludes_mirrors_across_all_source_cases() -> None:
    tags = list(quiz_core.WEAKNESS_TAGS)
    scams = [
        _case(
            case_id,
            fraud_type=f"type-{case_id % 5}",
            is_scam=True,
            tags=[tags[case_id % 5], tags[(case_id + 1) % 5]],
        )
        for case_id in range(1, 16)
    ]
    legit = [
        _case(
            100 + case.id,
            fraud_type=case.fraud_type,
            is_scam=False,
            tags=[],
            mirror_of=case.id,
        )
        for case in scams
    ]

    material = select_quiz_material([*scams, *legit], size=10)
    selected = _material_cases(material)
    selected_ids = {case.id for case in selected}

    assert len(material.verdict) + len(material.tactics) + bool(material.match) == 10
    assert all(
        case.mirror_of not in selected_ids
        for case in selected
        if case.mirror_of is not None
    )
    assert material.mirror_relaxed_count == 0


def test_select_quiz_material_relaxes_mirrors_only_to_fill_deck(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scam = _case(
        1,
        fraud_type="investment",
        is_scam=True,
        tags=["greed", "authority"],
    )
    legit = _case(
        2,
        fraud_type="investment",
        is_scam=False,
        tags=[],
        mirror_of=scam.id,
    )
    monkeypatch.setattr(quiz_core, "random", lambda: 0.0)

    material = select_quiz_material([scam, legit], size=2)

    assert len(material.verdict) + len(material.tactics) == 2
    assert {case.id for case in _material_cases(material)} == {1, 2}
    assert material.mirror_relaxed_count == 1


@pytest.mark.parametrize(
    ("level", "expected"),
    [(1, 1), (2, 1), (3, 2), (5, 2), (6, None), (20, None)],
)
def test_max_difficulty_for_level(level: int, expected: int | None) -> None:
    assert quiz_core.max_difficulty_for_level(level) == expected


def test_difficulty_limit_only_applies_to_verdict_and_match_still_deals() -> None:
    tags_without_social = sorted(quiz_core.WEAKNESS_TAGS - {"social_proof"})
    low_cases = [
        _case(
            case_id,
            fraud_type=f"type-{case_id}",
            is_scam=case_id % 2 == 0,
            tags=[],
            difficulty=1,
        )
        for case_id in range(1, 7)
    ]
    high_cases = [
        _case(
            case_id,
            fraud_type=f"hard-{case_id % 5}",
            is_scam=True,
            tags=(
                ["social_proof", "authority"]
                if case_id in {20, 21}
                else [
                    tags_without_social[case_id % len(tags_without_social)],
                    tags_without_social[(case_id + 1) % len(tags_without_social)],
                ]
            ),
            difficulty=3,
        )
        for case_id in range(20, 32)
    ]

    material = select_quiz_material([*low_cases, *high_cases], size=5, max_difficulty=1)

    assert all(case.difficulty <= 1 for case in material.verdict)
    assert len(material.tactics) == 2
    assert all(case.difficulty == 3 for case in material.tactics)
    assert len(material.match) == 5
    assert all(pair.case.difficulty == 3 for pair in material.match)


def test_match_shortage_warning_names_missing_tags(
    caplog: pytest.LogCaptureFixture,
) -> None:
    tags = sorted(quiz_core.WEAKNESS_TAGS - {"social_proof"})
    cases = [
        _case(
            case_id,
            fraud_type=f"type-{case_id % 5}",
            is_scam=True,
            tags=[tags[case_id % len(tags)], tags[(case_id + 1) % len(tags)]],
        )
        for case_id in range(20)
    ]

    material = select_quiz_material(cases, size=5)

    assert material.match == []
    assert "quiz match 素材不足，缺少 tag: social_proof" in caplog.text


def test_select_quiz_material_relaxes_difficulty_before_mirrors() -> None:
    low_scam = _case(
        1,
        fraud_type="investment",
        is_scam=True,
        tags=["greed", "authority"],
        difficulty=1,
    )
    low_legit_mirror = _case(
        2,
        fraud_type="investment",
        is_scam=False,
        tags=[],
        difficulty=1,
        mirror_of=low_scam.id,
    )
    hard_legit = _case(
        3,
        fraud_type="shopping",
        is_scam=False,
        tags=[],
        difficulty=3,
    )

    material = select_quiz_material(
        [low_scam, low_legit_mirror, hard_legit],
        size=2,
        max_difficulty=1,
    )

    selected = _material_cases(material)
    selected_ids = {case.id for case in selected}
    assert 3 in selected_ids
    assert not {1, 2} <= selected_ids
    assert material.mirror_relaxed_count == 0


def _mirror_case(case_id: int, mirror_of: int | None) -> GameCaseRow:
    return GameCaseRow(
        id=case_id,
        fraud_type="investment",
        is_scam=mirror_of is None,
        title="同一個情境的兩面",
        narrative="敘事",
        red_flags=[],
        difficulty=1,
        provenance="測試",
        mirror_of=mirror_of,
    )


def test_cases_excluding_blocks_both_mirror_directions() -> None:
    """查證題佔走一個案例時，它的鏡像兩個方向都要從選材池移除。

    鏡像對的標題完全相同，同一副牌裡出現兩次會直接洩漏 verdict 題的答案。
    只擋單一方向的話，80 副牌裡還是會漏幾副——實測過。
    """
    scam = _mirror_case(1, None)
    legit = _mirror_case(2, mirror_of=1)
    other = _mirror_case(3, None)

    # 方向一：查證題佔走 scam，指向它的 legit 要被擋掉。
    assert [c.id for c in _cases_excluding([scam, legit, other], {1})] == [3]
    # 方向二：查證題佔走 legit，它指向的 scam 也要被擋掉。
    assert [c.id for c in _cases_excluding([scam, legit, other], {2})] == [3]
    # 沒有佔走任何案例時原樣回傳。
    assert len(_cases_excluding([scam, legit, other], set())) == 3
