"""新版情境對抗的劇本與人格資料檔檢查（格式說明見 content/scenarios/README.md）。

劇本與人格是分開抽的：任何人格都要能演任何劇本（詐騙或正當），
所以人格檔只寫說話方式和個性，騙術、任務、要對方做的事都寫在劇本裡。
是不是詐騙由劇本的 role 決定，程式照玩家按的動作卡結算，AI 不判分。
"""

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from app.core.fraud_types import FRAUD_TYPES
from app.core.weakness import WEAKNESS_TAGS

CONTENT_DIR = Path(__file__).resolve().parents[2] / "content" / "scenarios"
SCRIPTS_DIR = CONTENT_DIR / "scripts"
PERSONAS_DIR = CONTENT_DIR / "personas"

MIN_SCAM_SCRIPTS = 100
MIN_LEGIT_SCRIPTS = 50
MIN_PERSONAS = 20
MIN_CLUES = 4
# 線索的地點：玩家「我的手機」裡固定的幾個地方（每次事件都一樣，看不出線索藏在哪），
# 加上對話本身（點開對方傳的網址、照片看細節）
CLUE_PLACES = {
    "來電紀錄",
    "通訊錄",
    "瀏覽器",
    "銀行",
    "購物",
    "錢包",
    "新聞",
    "165",
    "對話",
}

ROLES = {"scam", "legit"}
SCRIPT_FRAUD_TYPES = {*FRAUD_TYPES, "other"}
CHANNELS = {"line", "sms", "phone", "fb", "ig", "dating", "marketplace", "email"}
ASSETS = {"cash", "savings", "property", "card", "otp", "account", "personal_data"}
ACTIONS = {
    "transfer_cash",
    "transfer_property",
    "give_otp",
    "give_card",
    "click_link",
    "install_app",
    "add_friend",
    "buy_product",
    "rent_out",
    "sell_property",
    "accept_refund",
}
GENDERS = {"男", "女"}

SCRIPT_FIELDS = {
    "key",
    "title",
    "role",
    "fraud_type",
    "channel",
    "opening",
    "target_assets",
    "actions",
    "tactics",
    "clues",
    "elder_ok",
    "sources",
}
PERSONA_FIELDS = {
    "key",
    "name",
    "age",
    "gender",
    "speech_style",
    "typing_habit",
    "temperament",
    "when_doubted",
}
KEY_PATTERN = re.compile(
    r"^(scam|legit)-(investment|fake-sale|shopping|romance|atm|other)-\d{3}$"
)
STAGES = {
    "scam": ["開場", "建立信任", "提出要求", "施壓", "收割"],
    "legit": ["開場", "建立信任", "提出要求", "施壓", "成交"],
}
REACTIONS = ["懷疑時", "要求查證時", "拒絕時"]

# 寫法規則跟題庫管線一致（data_pipeline 的 WRITING_RULES、test_player_text.py）
CJK = "一-鿿"
WRITING_RULES = [
    (
        "中文旁要用全形標點",
        re.compile(rf"[{CJK}][,:;!?()]|[,:;!?()][{CJK}]"),
    ),
    ("不要用破折號", re.compile(r"[—–―]|--")),
    (
        "不要用 AI 腔的套話",
        re.compile(r"關鍵在於|值得注意的是|總而言之|綜上所述|不難發現|至關重要"),
    ),
    ("不要用公文用語", re.compile(r"予以|係指|係屬|之虞|爰此")),
]
# 被害人、嫌犯的姓氏也不寫（新聞常寫「林姓女房東」）
SURNAME_PATTERN = re.compile(rf"[{CJK}]姓[{CJK}]{{0,2}}(男|女|婦|翁|嫌|車手|房東|子)")
# 人格只管說話方式，出現這些字表示把劇本的任務寫進人格了
PERSONA_TASK_WORDS = re.compile(
    r"詐騙|騙|匯款|轉帳|驗證碼|提款卡|信用卡|帳戶|投資|獲利|保證金|劇本|任務"
)
# 不夾英文；ATM、LINE 是大家平常就這樣講的名字
ALLOWED_ENGLISH = {"ATM", "LINE"}
# 這些欄位是代碼，不是給人看的文字
CODE_FIELDS = {
    "key",
    "role",
    "fraud_type",
    "channel",
    "target_assets",
    "actions",
    "tactics",
    "sources",
}
# 階段台詞要提到玩家的財產
ASSET_WORDS = re.compile(r"存款|戶頭|帳戶|公寓|房|卡|現金|錢|薪水|股票|金飾|積蓄|資產")


def _parse(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    assert match, f"{path.name} 缺 YAML frontmatter"
    meta = yaml.safe_load(match.group(1))
    assert isinstance(meta, dict), f"{path.name} 的 frontmatter 不是對照表"
    return meta, match.group(2)


def _sections(body: str, level: int) -> dict[str, str]:
    """把本文依 `##`（level=2）或 `###`（level=3）標題切段。"""
    marks = "#" * level
    parts = re.split(rf"^{marks} (.+)$", body, flags=re.MULTILINE)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def _bullets(text: str) -> list[str]:
    return [m.strip() for m in re.findall(r"^- (.+)$", text, re.MULTILINE)]


def _strings(obj: object) -> list[str]:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in _strings(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in _strings(v)]
    return []


SCRIPT_FILES = sorted(SCRIPTS_DIR.glob("*.md"))
PERSONA_FILES = sorted(p for p in PERSONAS_DIR.glob("*.md") if p.name != "SOURCES.md")


def _ids(paths: list[Path]) -> list[str]:
    return [p.stem for p in paths]


def test_counts() -> None:
    roles = [_parse(p)[0].get("role") for p in SCRIPT_FILES]
    assert roles.count("scam") >= MIN_SCAM_SCRIPTS, (
        f"詐騙劇本 {roles.count('scam')} 個，至少要 {MIN_SCAM_SCRIPTS} 個"
    )
    assert roles.count("legit") >= MIN_LEGIT_SCRIPTS, (
        f"正當劇本 {roles.count('legit')} 個，至少要 {MIN_LEGIT_SCRIPTS} 個"
    )
    assert len(PERSONA_FILES) >= MIN_PERSONAS, (
        f"人格 {len(PERSONA_FILES)} 個，至少要 {MIN_PERSONAS} 個"
    )


@pytest.mark.parametrize("path", SCRIPT_FILES, ids=_ids(SCRIPT_FILES))
def test_script_frontmatter(path: Path) -> None:
    meta, _ = _parse(path)
    role = meta.get("role")
    expected = SCRIPT_FIELDS | ({"benefit"} if role == "legit" else {"trap"})
    assert set(meta) == expected, (
        f"缺 {sorted(expected - set(meta))}，多 {sorted(set(meta) - expected)}"
    )

    key = meta["key"]
    assert key == path.stem, "key 要和檔名一樣"
    match = KEY_PATTERN.match(key)
    assert match, f"key 格式不對：{key}"
    assert match.group(1) == role, "key 開頭要和 role 一樣"
    assert match.group(2) == meta["fraud_type"], "key 中間要和 fraud_type 一樣"

    assert role in ROLES
    assert meta["fraud_type"] in SCRIPT_FRAUD_TYPES
    assert meta["channel"] in CHANNELS, f"channel 不在清單內：{meta['channel']}"
    for field in ("title", "opening"):
        assert isinstance(meta[field], str) and meta[field].strip(), f"{field} 是空的"
    assert len(meta["title"]) <= 15, "title 要短（15 字內）"

    for field, allowed in (("target_assets", ASSETS), ("actions", ACTIONS)):
        values = meta[field]
        assert isinstance(values, list) and values, f"{field} 至少要一項"
        assert len(values) == len(set(values)), f"{field} 有重複"
        assert set(values) <= allowed, f"{field} 有不認得的值：{set(values) - allowed}"

    tactics = meta["tactics"]
    assert isinstance(tactics, list)
    assert set(tactics) <= WEAKNESS_TAGS, (
        f"tactics 不認得：{set(tactics) - WEAKNESS_TAGS}"
    )
    if role == "scam":
        assert tactics, "詐騙劇本至少要用一種話術"

    if role == "legit":
        benefit = meta["benefit"]
        assert isinstance(benefit, str) and benefit.strip(), "正當劇本要寫好處"
        if meta["fraud_type"] == "investment":
            assert "跌" in benefit, "投資商品的好處要寫明會漲跌"

    # 線索像解謎遊戲：放在遊戲裡讓玩家自己去找，每次只放一部分；
    # 玩家一定會漏看，所以寫四條，加上對話裡的破綻，放兩條時還有三條路推得到
    clues = meta["clues"]
    assert isinstance(clues, list) and len(clues) >= MIN_CLUES, (
        f"clues 至少要 {MIN_CLUES} 條"
    )
    for clue in clues:
        place, _, found = str(clue).partition("：")
        assert place in CLUE_PLACES and found.strip(), (
            f"線索要寫成「地點：看到什麼」，地點從 {sorted(CLUE_PLACES)} 挑：{clue}"
        )

    # 詐騙劇本要寫：玩家用對方給的管道查（對方的電話、連結、通話中按 165），會被假的人接起來
    if role == "scam":
        channel, _, found = str(meta["trap"]).partition("：")
        assert channel.strip() and found.strip(), (
            f"trap 要寫成「對方給的管道：看到什麼」：{meta['trap']}"
        )

    assert isinstance(meta["elder_ok"], bool), "elder_ok 要是 true 或 false"

    sources = meta["sources"]
    assert isinstance(sources, list), "sources 要是網址清單"
    assert len(sources) == len(set(sources)), "sources 有重複"
    assert all(re.match(r"^https?://\S+$", s) for s in sources), "sources 要是網址"
    min_sources = 2 if role == "scam" else 1
    assert len(sources) >= min_sources, (
        f"{role} 劇本至少要 {min_sources} 個來源（詐騙要新聞加詳細經過）"
    )


@pytest.mark.parametrize("path", SCRIPT_FILES, ids=_ids(SCRIPT_FILES))
def test_script_sections(path: Path) -> None:
    meta, body = _parse(path)
    role = meta["role"]
    explain = "破綻" if role == "scam" else "為什麼是真的"
    sections = _sections(body, 2)
    assert list(sections) == ["背景", "階段", explain, "玩家反應"], (
        f"段落要依序是 背景／階段／{explain}／玩家反應，現在是 {list(sections)}"
    )
    for name, text in sections.items():
        assert text, f"「{name}」是空的"

    stages = _sections(sections["階段"], 3)
    assert list(stages) == STAGES[role], f"階段要依序是 {STAGES[role]}"
    for name, text in stages.items():
        lines = _bullets(text)
        assert 2 <= len(lines) <= 3, (
            f"階段「{name}」要 2～3 句台詞，現在 {len(lines)} 句"
        )
        assert all(line.startswith("「") for line in lines), (
            f"階段「{name}」的台詞要用「」括起來"
        )
    assert ASSET_WORDS.search(sections["階段"]), "階段台詞要提到玩家的財產"

    reactions = _sections(sections["玩家反應"], 3)
    assert list(reactions) == REACTIONS, f"玩家反應要依序是 {REACTIONS}"
    assert all(reactions.values()), "玩家反應每一項都要寫"


@pytest.mark.parametrize("path", PERSONA_FILES, ids=_ids(PERSONA_FILES))
def test_persona(path: Path) -> None:
    meta, body = _parse(path)
    assert set(meta) == PERSONA_FIELDS, (
        f"缺 {sorted(PERSONA_FIELDS - set(meta))}，多 {sorted(set(meta) - PERSONA_FIELDS)}"
    )
    assert meta["key"] == path.stem, "key 要和檔名一樣"
    assert re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", meta["key"]), "key 用小寫英文和連字號"
    assert isinstance(meta["age"], int) and 18 <= meta["age"] <= 90, "age 要是 18～90"
    assert meta["gender"] in GENDERS
    for field in PERSONA_FIELDS - {"key", "age", "gender"}:
        assert isinstance(meta[field], str) and meta[field].strip(), f"{field} 是空的"

    sections = _sections(body, 2)
    assert list(sections) == ["說話方式", "口頭禪", "示範句"], (
        f"段落要依序是 說話方式／口頭禪／示範句，現在是 {list(sections)}"
    )
    assert sections["說話方式"], "說話方式是空的"
    assert _bullets(sections["口頭禪"]), "口頭禪至少一個"
    assert len(_bullets(sections["示範句"])) >= 5, "示範句至少 5 句"

    hits = PERSONA_TASK_WORDS.findall(path.read_text(encoding="utf-8"))
    assert not hits, f"人格只寫說話方式，不寫騙術或任務：{sorted(set(hits))}"


def test_keys_and_names_unique() -> None:
    script_keys = [_parse(p)[0]["key"] for p in SCRIPT_FILES]
    assert len(script_keys) == len(set(script_keys)), "劇本 key 重複"
    names = [_parse(p)[0]["name"] for p in PERSONA_FILES]
    assert len(names) == len(set(names)), "人格名稱重複"


def test_persona_sources_listed() -> None:
    sources = PERSONAS_DIR / "SOURCES.md"
    assert sources.exists(), "人格的參考來源要記在 personas/SOURCES.md"
    assert re.search(r"https?://", sources.read_text(encoding="utf-8")), (
        "SOURCES.md 至少要有一個網址"
    )


@pytest.mark.parametrize(
    "path",
    [*SCRIPT_FILES, *PERSONA_FILES],
    ids=_ids([*SCRIPT_FILES, *PERSONA_FILES]),
)
def test_writing_rules(path: Path) -> None:
    meta, body = _parse(path)
    texts = [*_strings({k: v for k, v in meta.items() if k not in CODE_FIELDS}), body]
    errors = [
        f"{rule}（「{m.group(0)}」）"
        for text in texts
        for rule, pattern in WRITING_RULES
        for m in pattern.finditer(text)
    ]
    assert not errors, errors[:5]
    surnames = [m.group(0) for text in texts for m in SURNAME_PATTERN.finditer(text)]
    assert not surnames, f"不要寫當事人的姓氏：{surnames[:3]}"
    english = {w for text in texts for w in re.findall(r"[A-Za-z]+", text)}
    assert english <= ALLOWED_ENGLISH, (
        f"不要夾英文：{sorted(english - ALLOWED_ENGLISH)}"
    )
