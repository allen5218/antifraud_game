"""玩家看得到的固定文字:中文旁不能用半形標點,也不能有破折號。

題庫是資料管線產的,2026-09-25 發現 120 題裡有 80 題的敘述用半形逗號
(「三個月,他常談未來」)、13 處有「——」這類一看就是 AI 寫的句式。
這裡把會進到畫面的來源都檢查一遍,之後管線新產的題目混進來會直接擋下。
修正工具見 deploy/sql/2026-09-25-question-bank-wording.py。
"""

import re
from collections.abc import Iterator
from pathlib import Path

import pytest

from app.core.db import SWIPE_CARDS_SEED
from app.core.weakness import WEAKNESS_LABELS, WEAKNESS_SUGGESTIONS
from app.game.seed import PRETEST_QUESTIONS
from app.scenario.config import LEGIT_SIGNALS

CJK = "一-鿿"
BAD = re.compile(rf"[{CJK}][,:;!?()]|[,:;!?()][{CJK}]|——")

SEED_DIR = Path(__file__).resolve().parents[3] / "deploy" / "seed"


def _strings(obj: object) -> Iterator[str]:
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from _strings(value)
    elif isinstance(obj, list | tuple):
        for value in obj:
            yield from _strings(value)


@pytest.mark.parametrize(
    ("name", "source"),
    [
        (
            "前測題",
            [
                {k: v for k, v in q.items() if k != "legacy_text"}
                for q in PRETEST_QUESTIONS
            ],
        ),
        (
            "滑卡",
            [
                {k: v for k, v in c.items() if k != "legacy_text"}
                for c in SWIPE_CARDS_SEED
            ],
        ),
        ("話術名稱", WEAKNESS_LABELS),
        ("話術建議", WEAKNESS_SUGGESTIONS),
        ("正常訊號", LEGIT_SIGNALS),
    ],
)
def test_builtin_texts(name: str, source: object) -> None:
    bad = [s for s in _strings(source) if BAD.search(s)]
    assert not bad, f"{name}有 {len(bad)} 則:{bad[:3]}"


@pytest.mark.parametrize("filename", ["game_cases.sql", "game_case_questions.sql"])
def test_question_bank_seed(filename: str) -> None:
    path = SEED_DIR / filename
    if not path.exists():  # 容器裡只有 backend/,沒有 deploy/
        pytest.skip(f"找不到 {path}")
    hits = [
        line[max(0, m.start() - 20) : m.end() + 20]
        for line in path.read_text().splitlines()
        for m in BAD.finditer(line)
    ]
    assert not hits, f"{filename} 有 {len(hits)} 處:{hits[:3]}"
