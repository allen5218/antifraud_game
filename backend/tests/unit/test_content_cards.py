"""日常模式卡片題庫（`backend/content/cards/*.jsonl`）的守門測試。

2026-11 改版：日常模式改成一張接一張的短卡片，一題只考一件事。
題目字數、選項規則、插圖用的班底 id、判斷題詐騙與正當的比例、
寫法（全形標點、不用破折號、不夾英文、選項不寫理由）都在這裡擋。

寫法規則跟資料管線的 `scripts/common.py`（`WRITING_RULES`、`OPTION_REASON_WORDS`）
與 `test_player_text.py` 一致，改了一邊記得改另一邊。

跑法：`cd backend && uv run pytest tests/unit/test_content_cards.py -v`
"""

import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from app.core.weakness import WEAKNESS_TAGS

CARDS_DIR = Path(__file__).resolve().parents[2] / "content" / "cards"

FRAUD_TYPES = {"investment", "fake-sale", "shopping", "romance", "atm", "general"}
KINDS = {"judge", "choice", "fill", "match", "spot", "reply", "order"}

# 插圖固定班底，另一個工作階段照這份清單畫圖，兩邊要一致。
SCENES = {"living-room", "street", "atm-corner", "shop", "office", "phone-screen"}
CAST = {
    "grandma",
    "grandpa",
    "office-worker",
    "student",
    "fake-cs",
    "seller",
    "buyer",
    "stranger",
    "bank-clerk",
    "police",
}
PROPS = {"phone", "chat", "atm", "parcel", "card", "laptop", "money", "house", "qr"}

POOLS = {"practice", "exam"}
PROVENANCE_PREFIXES = ("改編自：", "依據：")

# 判斷題的兩個選項固定這樣寫、這個順序，畫面與年長者模式的念法才一致。
JUDGE_OPTIONS = ["是詐騙", "不是詐騙"]
BLANK = "＿＿"

REQUIRED = {
    "card_key",
    "source_key",
    "fraud_type",
    "kind",
    "prompt",
    "explanation",
    "weakness_tag",
    "difficulty",
    "elder_ok",
    "art",
    "pool",
    "provenance",
}
# 每種題型自己的欄位；不屬於該題型的欄位不能出現。
KIND_FIELD = {
    "judge": "options",
    "choice": "options",
    "fill": "options",
    "reply": "options",
    "match": "pairs",
    "spot": "lines",
    "order": "steps",
}
OPTIONAL_FIELDS = set(KIND_FIELD.values())

# 字數上限（一個中文字算一個）。
MAX_PROMPT = 40
MAX_EXPLANATION = 60
MAX_OPTION = 20
MAX_LINE = 24
MAX_STEP = 16
MAX_PAIR_SIDE = 14
ELDER_MAX_PROMPT = 30
ELDER_MAX_OPTION = 10

CARD_KEY = re.compile(r"^(?P<ft>[a-z-]+)-(?P<kind>[a-z]+)-(?P<num>\d{3})$")
SOURCE_KEY = re.compile(r"^(?P<ft>[a-z-]+)-src-\d{3}$")

# ── 寫法規則（與 data_pipeline 的 WRITING_RULES 一致）───────────────────
CJK = "一-鿿"
WRITING_RULES = [
    (
        "中文旁要用全形標點（，：；！？（））",
        re.compile(rf"[{CJK}][,:;!?()]|[,:;!?()][{CJK}]"),
    ),
    ("不要用破折號", re.compile(r"—|--")),
    (
        "不要用 AI 腔的套話",
        re.compile(r"關鍵在於|值得注意的是|總而言之|綜上所述|不難發現|至關重要"),
    ),
    ("不要用公文用語", re.compile(r"予以|係指|係屬|之虞|爰此")),
    (
        "「此」「該」開頭的指稱改成「這」",
        re.compile(r"此類|此筆|該筆|該名|該帳號|該網站"),
    ),
]
OPTION_REASON_WORDS = re.compile(r"因為|所以|以免|才能|避免|確保")
NOT_BUT = re.compile(r"不是[^。，！？]*而是")
# 不夾英文：只放行畫面上大家本來就這樣叫的幾個字。
ENGLISH_WORD = re.compile(r"[A-Za-z]+")
ALLOWED_ENGLISH = {"ATM", "App", "LINE"}


def _load() -> list[tuple[str, int, dict[str, Any]]]:
    rows: list[tuple[str, int, dict[str, Any]]] = []
    for path in sorted(CARDS_DIR.glob("*.jsonl")):
        for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not raw.strip():
                continue
            rows.append((path.name, line_no, json.loads(raw)))
    return rows


ROWS = _load()
CARDS = [card for _, _, card in ROWS]


def _where(card: dict[str, Any]) -> str:
    return str(card.get("card_key", "?"))


def _player_texts(card: dict[str, Any]) -> Iterator[tuple[str, str]]:
    """玩家看得到的每一段文字，連同欄位名稱。"""
    yield "prompt", card["prompt"]
    yield "explanation", card["explanation"]
    yield "provenance", card["provenance"]
    for opt in card.get("options", []):
        yield "options", opt["text"]
    for pair in card.get("pairs", []):
        yield "pairs", pair["left"]
        yield "pairs", pair["right"]
    for line in card.get("lines", []):
        yield "lines", line["text"]
    for step in card.get("steps", []):
        yield "steps", step


def test_cards_exist() -> None:
    assert CARDS_DIR.is_dir(), f"找不到 {CARDS_DIR}"
    assert CARDS, "卡片題庫是空的"


def test_file_names_match_fraud_types() -> None:
    names = {p.stem for p in CARDS_DIR.glob("*.jsonl")}
    assert names <= FRAUD_TYPES, f"檔名要是詐騙類型或 general：{names - FRAUD_TYPES}"
    wrong = [
        f"{fname}:{no} {_where(c)}"
        for fname, no, c in ROWS
        if c.get("fraud_type") != Path(fname).stem
    ]
    assert not wrong, f"fraud_type 跟檔名不一致：{wrong[:5]}"


def test_fields() -> None:
    errors = []
    for card in CARDS:
        keys = set(card)
        missing = REQUIRED - keys
        if missing:
            errors.append(f"{_where(card)} 缺欄位 {sorted(missing)}")
            continue
        kind = card["kind"]
        if kind not in KINDS:
            errors.append(f"{_where(card)} kind 不認得：{kind}")
            continue
        extra = keys - REQUIRED - {KIND_FIELD[kind]}
        if extra:
            errors.append(f"{_where(card)} 多了不屬於 {kind} 的欄位 {sorted(extra)}")
        if KIND_FIELD[kind] not in keys:
            errors.append(f"{_where(card)} 缺 {KIND_FIELD[kind]}")
    assert not errors, "\n".join(errors[:20])


def test_keys() -> None:
    errors = []
    for card in CARDS:
        m = CARD_KEY.match(card["card_key"])
        if not m:
            errors.append(f"{_where(card)} card_key 格式要是 <類型>-<題型>-NNN")
        elif m["ft"] != card["fraud_type"] or m["kind"] != card["kind"]:
            errors.append(f"{_where(card)} card_key 的類型或題型跟欄位不一致")
        s = SOURCE_KEY.match(card["source_key"])
        if not s or s["ft"] != card["fraud_type"]:
            errors.append(f"{_where(card)} source_key 格式要是 <類型>-src-NNN")
    dup = [k for k, n in Counter(c["card_key"] for c in CARDS).items() if n > 1]
    if dup:
        errors.append(f"card_key 重複：{dup}")
    assert not errors, "\n".join(errors[:20])


def test_source_groups() -> None:
    """同一句原料出 3～4 種題型，同一組卡片在同一個題庫（練習或檢測）。"""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in CARDS:
        groups[card["source_key"]].append(card)
    errors = []
    for key, cards in groups.items():
        kinds = [c["kind"] for c in cards]
        if not 3 <= len(cards) <= 4:
            errors.append(f"{key} 有 {len(cards)} 張，要 3～4 張")
        if len(set(kinds)) != len(kinds):
            errors.append(f"{key} 題型重複：{kinds}")
        if len({c["pool"] for c in cards}) != 1:
            errors.append(f"{key} 同一句原料分到練習和檢測，練習會先看過檢測題")
        if len({c["provenance"] for c in cards}) != 1:
            errors.append(f"{key} 同一句原料的出處不一致")
    assert not errors, "\n".join(errors[:20])


def _check_options(card: dict[str, Any], errors: list[str]) -> None:
    kind = card["kind"]
    options = card["options"]
    texts = [o.get("text") for o in options]
    if any(set(o) != {"text", "correct"} for o in options):
        errors.append(f"{_where(card)} 選項只能有 text 與 correct")
        return
    if sum(o["correct"] is True for o in options) != 1:
        errors.append(f"{_where(card)} 要剛好一個正解")
    if len(set(texts)) != len(texts):
        errors.append(f"{_where(card)} 選項重複")
    if kind == "judge":
        if texts != JUDGE_OPTIONS:
            errors.append(f"{_where(card)} 判斷題選項固定是 {JUDGE_OPTIONS}")
    elif kind == "fill":
        if len(options) != 3:
            errors.append(f"{_where(card)} 填空題要 3 個選項")
        if card["prompt"].count(BLANK) != 1:
            errors.append(f"{_where(card)} 填空題要剛好一個「{BLANK}」")
    elif not 2 <= len(options) <= 3:
        errors.append(f"{_where(card)} {kind} 要 2～3 個選項")
    for text in texts:
        if len(text) > MAX_OPTION:
            errors.append(f"{_where(card)} 選項超過 {MAX_OPTION} 字：{text}")
        if m := OPTION_REASON_WORDS.search(text):
            errors.append(f"{_where(card)} 選項寫了理由（「{m.group(0)}」）：{text}")


def test_kind_rules() -> None:
    errors: list[str] = []
    for card in CARDS:
        kind = card["kind"]
        if kind != "fill" and BLANK in card["prompt"]:
            errors.append(f"{_where(card)} 只有填空題可以有「{BLANK}」")
        if KIND_FIELD[kind] == "options":
            _check_options(card, errors)
        elif kind == "match":
            pairs = card["pairs"]
            if not 3 <= len(pairs) <= 4:
                errors.append(f"{_where(card)} 配對要 3～4 組")
            if any(set(p) != {"left", "right"} for p in pairs):
                errors.append(f"{_where(card)} 配對只能有 left 與 right")
                continue
            for side in ("left", "right"):
                values = [p[side] for p in pairs]
                if len(set(values)) != len(values):
                    errors.append(f"{_where(card)} 配對的 {side} 重複")
                errors += [
                    f"{_where(card)} 配對超過 {MAX_PAIR_SIDE} 字：{v}"
                    for v in values
                    if len(v) > MAX_PAIR_SIDE
                ]
        elif kind == "spot":
            lines = card["lines"]
            if len(lines) != 3:
                errors.append(f"{_where(card)} 挑句題要 3 句")
            if any(set(x) != {"text", "suspicious"} for x in lines):
                errors.append(f"{_where(card)} 挑句只能有 text 與 suspicious")
                continue
            if sum(x["suspicious"] is True for x in lines) != 1:
                errors.append(f"{_where(card)} 要剛好一句可疑")
            errors += [
                f"{_where(card)} 句子超過 {MAX_LINE} 字：{x['text']}"
                for x in lines
                if len(x["text"]) > MAX_LINE
            ]
        elif kind == "order":
            steps = card["steps"]
            if not 3 <= len(steps) <= 4 or not all(isinstance(s, str) for s in steps):
                errors.append(f"{_where(card)} 排序要 3～4 步文字")
                continue
            if len(set(steps)) != len(steps):
                errors.append(f"{_where(card)} 步驟重複")
            for step in steps:
                if len(step) > MAX_STEP:
                    errors.append(f"{_where(card)} 步驟超過 {MAX_STEP} 字：{step}")
                if m := OPTION_REASON_WORDS.search(step):
                    errors.append(f"{_where(card)} 步驟寫了理由（「{m.group(0)}」）")
    assert not errors, "\n".join(errors[:30])


def test_lengths() -> None:
    errors = []
    for card in CARDS:
        if len(card["prompt"]) > MAX_PROMPT:
            errors.append(f"{_where(card)} 題目 {len(card['prompt'])} 字")
        if len(card["explanation"]) > MAX_EXPLANATION:
            errors.append(f"{_where(card)} 解說 {len(card['explanation'])} 字")
        if not card["explanation"].endswith("。"):
            errors.append(f"{_where(card)} 解說要用「。」結尾")
    assert not errors, "\n".join(errors[:20])


def test_metadata() -> None:
    errors = []
    for card in CARDS:
        tag = card["weakness_tag"]
        if tag is not None and tag not in WEAKNESS_TAGS:
            errors.append(f"{_where(card)} weakness_tag 不認得：{tag}")
        diff = card["difficulty"]
        if not isinstance(diff, int) or isinstance(diff, bool) or not 1 <= diff <= 3:
            errors.append(f"{_where(card)} difficulty 要是 1～3")
        if card["pool"] not in POOLS:
            errors.append(f"{_where(card)} pool 要是 practice 或 exam")
        prov = card["provenance"]
        if not prov.startswith(PROVENANCE_PREFIXES) or len(prov) < 8:
            errors.append(
                f"{_where(card)} 出處要用「改編自：」或「依據：」開頭並寫來源"
            )
    assert not errors, "\n".join(errors[:20])


def test_elder_ok() -> None:
    """年長者模式只出兩個選項、字很短的卡（畫面寫華語、聲音念台語）。"""
    errors = []
    for card in CARDS:
        if card["elder_ok"] is not True:
            if card["elder_ok"] is not False:
                errors.append(f"{_where(card)} elder_ok 要是 true 或 false")
            continue
        if card["kind"] not in {"judge", "choice", "reply"}:
            errors.append(f"{_where(card)} {card['kind']} 不能進年長者模式")
            continue
        if len(card["options"]) != 2:
            errors.append(f"{_where(card)} 年長者模式只能兩個選項")
        if len(card["prompt"]) > ELDER_MAX_PROMPT:
            errors.append(f"{_where(card)} 年長者模式題目超過 {ELDER_MAX_PROMPT} 字")
        errors += [
            f"{_where(card)} 年長者模式選項超過 {ELDER_MAX_OPTION} 字：{o['text']}"
            for o in card["options"]
            if len(o["text"]) > ELDER_MAX_OPTION
        ]
    assert not errors, "\n".join(errors[:20])


def test_art_ids() -> None:
    errors = []
    for card in CARDS:
        art = card["art"]
        if not isinstance(art, dict) or set(art) != {"scene", "cast", "props"}:
            errors.append(f"{_where(card)} art 要有 scene、cast、props")
            continue
        if art["scene"] not in SCENES:
            errors.append(f"{_where(card)} scene 不在清單：{art['scene']}")
        for field, allowed in (("cast", CAST), ("props", PROPS)):
            values = art[field]
            if not isinstance(values, list) or len(values) > 3:
                errors.append(f"{_where(card)} {field} 要是最多 3 個的清單")
                continue
            if len(set(values)) != len(values):
                errors.append(f"{_where(card)} {field} 重複")
            bad = set(values) - allowed
            if bad:
                errors.append(f"{_where(card)} {field} 不在清單：{sorted(bad)}")
        if not art["cast"] and not art["props"]:
            errors.append(f"{_where(card)} 插圖至少要一個角色或道具")
    assert not errors, "\n".join(errors[:20])


def test_writing_rules() -> None:
    errors = []
    for card in CARDS:
        for field, text in _player_texts(card):
            for rule, pattern in WRITING_RULES:
                if m := pattern.search(text):
                    errors.append(f"{_where(card)} {field}：{rule}（「{m.group(0)}」）")
            english = set(ENGLISH_WORD.findall(text)) - ALLOWED_ENGLISH
            if english and field != "provenance":
                errors.append(f"{_where(card)} {field} 夾英文：{sorted(english)}")
        if NOT_BUT.search(card["explanation"]):
            errors.append(f"{_where(card)} 解說不要用「不是…而是…」當結論")
    assert not errors, "\n".join(errors[:30])


def test_unique_prompts() -> None:
    """判斷、選擇、填空、回覆題的題目不能重複（挑句、配對、排序可以共用問法）。"""
    prompts = [
        c["prompt"] for c in CARDS if c["kind"] in {"judge", "choice", "fill", "reply"}
    ]
    dup = [p for p, n in Counter(prompts).items() if n > 1]
    assert not dup, f"題目重複：{dup}"


# ── 每個檔案的比例 ─────────────────────────────────────────────


def _by_file() -> dict[str, list[dict[str, Any]]]:
    files: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fname, _, card in ROWS:
        files[fname].append(card)
    return files


FILES = _by_file()


@pytest.mark.parametrize("fname", sorted(FILES))
def test_judge_balance(fname: str) -> None:
    """判斷題詐騙和正當各半，玩家不能靠「全按詐騙」拿高分。"""
    judges = [c for c in FILES[fname] if c["kind"] == "judge"]
    if len(judges) < 10:
        pytest.skip("判斷題太少，不看比例")
    scam = sum(c["options"][0]["correct"] for c in judges)
    ratio = scam / len(judges)
    assert 0.4 <= ratio <= 0.6, f"{fname} 判斷題詐騙 {scam}/{len(judges)}"


@pytest.mark.parametrize("fname", sorted(FILES))
def test_exam_share(fname: str) -> None:
    """約一成標 exam，只在檢測出現。"""
    cards = FILES[fname]
    if len(cards) < 50:
        pytest.skip("卡片太少，不看比例")
    ratio = sum(c["pool"] == "exam" for c in cards) / len(cards)
    assert 0.05 <= ratio <= 0.15, f"{fname} 檢測卡佔 {ratio:.0%}"


@pytest.mark.parametrize("fname", sorted(FILES))
def test_easy_share(fname: str) -> None:
    """定義題和簡單識別題（difficulty 1）佔一半左右。"""
    cards = FILES[fname]
    if len(cards) < 50:
        pytest.skip("卡片太少，不看比例")
    ratio = sum(c["difficulty"] == 1 for c in cards) / len(cards)
    assert 0.4 <= ratio <= 0.6, f"{fname} 簡單題佔 {ratio:.0%}"


@pytest.mark.parametrize("fname", sorted(FILES))
def test_answer_does_not_leak(fname: str) -> None:
    """正解的位置不能集中，也不能老是最長或最短的那個（看長度就猜得到）。"""
    cards = [c for c in FILES[fname] if c["kind"] in {"choice", "fill", "reply"}]
    if len(cards) < 10:
        pytest.skip("選擇類題目太少，不看比例")
    positions = Counter(
        next(i for i, o in enumerate(c["options"]) if o["correct"]) for c in cards
    )
    top = max(positions.values()) / len(cards)
    assert top <= 0.6, f"{fname} 正解位置太集中：{dict(positions)}"

    def extreme_is_correct(card: dict[str, Any], pick: Any) -> bool:
        lengths = [len(o["text"]) for o in card["options"]]
        target = pick(lengths)
        hits = [o for o in card["options"] if len(o["text"]) == target]
        return len(set(lengths)) > 1 and len(hits) == 1 and hits[0]["correct"]

    longest = sum(extreme_is_correct(c, max) for c in cards) / len(cards)
    shortest = sum(extreme_is_correct(c, min) for c in cards) / len(cards)
    assert longest <= 0.4, f"{fname} 正解剛好是最長選項的比例 {longest:.0%}"
    assert shortest <= 0.4, f"{fname} 正解剛好是最短選項的比例 {shortest:.0%}"
    # 一邊太多、一邊太少也會洩題（例如正解從來不是最長的，玩家就學會別選最長的）。
    assert abs(longest - shortest) <= 0.15, (
        f"{fname} 正解是最長 {longest:.0%}、最短 {shortest:.0%}，差太多"
    )


@pytest.mark.parametrize("fname", sorted(FILES))
def test_spot_position_spread(fname: str) -> None:
    """挑句題的可疑句不能老是同一個位置（例如每次都是最後一句）。"""
    spots = [c for c in FILES[fname] if c["kind"] == "spot"]
    if len(spots) < 10:
        pytest.skip("挑句題太少，不看比例")
    positions = Counter(
        next(i for i, x in enumerate(c["lines"]) if x["suspicious"]) for c in spots
    )
    top = max(positions.values()) / len(spots)
    assert top <= 0.6, f"{fname} 可疑句位置太集中：{dict(positions)}"
