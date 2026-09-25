"""題庫文字修正:中文旁的半形標點轉全形,加上 13 處措詞改寫。

用法:
  就地改寫原稿與種子:
    python3 deploy/sql/2026-09-25-question-bank-wording.py <檔案>...
  產生給已上線環境的 UPDATE(舊種子取自改版前的 commit):
    git show 914d149:deploy/seed/game_cases.sql > /tmp/old_cases.sql
    python3 deploy/sql/2026-09-25-question-bank-wording.py --sql /tmp/old_cases.sql deploy/seed/game_cases.sql \
      > deploy/sql/2026-09-25-question-bank-wording.sql

就地改寫只動「緊鄰中文字」的半形標點,數字裡的逗號(1,500)、時間(10:30)不受影響。
jsonl 與 pg_dump 的 COPY 資料都直接以純文字處理:JSON 與 COPY 的結構字元
(引號後的逗號、冒號、tab)永遠不會緊鄰中文字,所以不會被改到。

給正式環境的 UPDATE **不在資料庫裡重做轉換**:網址裡緊鄰中文字的 ? 也會被轉,
草稿或手改過的列也會被波及。改成逐列、逐欄寫死新舊值,以 case_key 或
(question_key, version) 找列,**只有目前內容與舊種子一字不差才更新**。
重跑時舊值已不存在,什麼都不會改;對不上的列會留在最後的檢查報表裡。
"""

import re
import sys
from pathlib import Path

CJK = "一-鿿"
HALF_TO_FULL = {",": "，", ":": "：", ";": "；", "!": "！", "?": "？", "(": "（", ")": "）"}
_after_cjk = re.compile(rf"(?<=[{CJK}])([,:;!?()])")
_before_cjk = re.compile(rf"([,:;!?()])(?=[{CJK}])")

# 措詞改寫(套在全形化之後的文字上)。舊字串找不到就略過,重跑安全。
WORDING: list[tuple[str, str]] = [
    # 案例 312 investment-scam-002-v2
    (
        "那位主管說這份工作的收入不是靠底薪，而是靠參與分紅——只要自己也投入一筆資金進去跑單，就能同時領佣金和分紅。",
        "那位主管說這份工作不領底薪，收入靠分紅，只要自己也投入一筆資金進去跑單，就能同時領佣金和分紅。",
    ),
    # 案例 327 fake-sale-scam-001-v2
    (
        "那位客服說問題出在我這邊——我是賣家但還沒完成認證、也沒簽金流協定，",
        "那位客服說問題出在我這邊，因為我是賣家，卻還沒完成認證、也沒簽金流協定，",
    ),
    # 案例 329 fake-sale-scam-003-v2
    ("可以先寄再付一半——但講完又改口說平台規定不行。", "可以先寄再付一半，但講完又改口說平台規定不行。"),
    # 案例 337 investment-legit-013 的紅旗說明
    (
        "人頭帳戶詐騙的關鍵在於取得可實際操作帳戶的實體卡片與密碼，影本本身無法操作帳戶",
        "人頭帳戶要能拿來用，靠的是實體卡片與密碼，影本本身無法操作帳戶",
    ),
    # 查證題解說(8 則破折號,1125 另修「開程式」)
    (
        "再撥卡片背面印的號碼——那是唯一不會被對方指定的管道。開程式雖然也安全，",
        "再撥卡片背面印的號碼，那是唯一不會被對方指定的管道。打開銀行 App 雖然也安全，",
    ),
    ("對方在電話裡要你別說出匯款原因——那句話本身就是警訊。", "對方在電話裡要你別說出匯款原因，光是這句話就是警訊。"),
    (
        "剩下的只有把實物送進獨立鑑定——而他願不願意讓鞋先進鑑定，本身就是答案。",
        "剩下的只有把實物送進獨立鑑定，而他願不願意讓鞋先送鑑定，本身就是答案。",
    ),
    (
        "原平台入口在這裡根本沒有平台——錢是匯到個人帳戶。",
        "原平台入口在這裡用不上，因為根本沒有平台，錢是直接匯到個人帳戶。",
    ),
    (
        "而且電話要自己查——敘事裡她沒有加對方給的店長帳號，而是自行搜尋登記電話，那正是這題的重點。",
        "而且電話要自己查。敘事裡她沒有加對方給的店長帳號，而是自行搜尋登記電話，這正是這題的重點。",
    ),
    (
        "連自稱主管的人也在同一個群組裡——你手上沒有任何可以獨立找到的單位。",
        "連自稱主管的人也在同一個群組裡，你手上沒有任何可以獨立找到的單位。",
    ),
    (
        "而你的銀行是找得到本尊的——不要回訊息，",
        "而你的銀行是找得到本尊的。不要回訊息，",
    ),
    (
        "投影片還放了證照——這些都是查得到真假的。",
        "投影片還放了證照，這些都是查得到真假的。",
    ),
]


def normalize(text: str) -> str:
    text = _after_cjk.sub(lambda m: HALF_TO_FULL[m.group(1)], text)
    text = _before_cjk.sub(lambda m: HALF_TO_FULL[m.group(1)], text)
    for old, new in WORDING:
        text = text.replace(old, new)
    return text


COPY_ESCAPES = {"b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v", "\\": "\\"}


def _unescape(field: str) -> str | None:
    """pg_dump COPY 文字格式的欄位還原成原值。"""
    if field == "\\N":
        return None
    return re.sub(r"\\(.)", lambda m: COPY_ESCAPES.get(m.group(1), m.group(1)), field)


def copy_rows(dump: str, table: str) -> list[dict[str, str | None]]:
    """讀出 pg_dump 裡某張表的 COPY 資料。"""
    lines = dump.splitlines()
    head = next(i for i, ln in enumerate(lines) if ln.startswith(f"COPY public.{table} ("))
    columns = lines[head][lines[head].index("(") + 1 : lines[head].index(")")].split(", ")
    rows = []
    for ln in lines[head + 1 :]:
        if ln == "\\.":
            break
        rows.append(dict(zip(columns, map(_unescape, ln.split("\t")), strict=True)))
    return rows


def _literal(value: str) -> str:
    tag = "$wording$"
    assert tag not in value, "內容裡剛好有 dollar-quote 標記,換一個"
    return f"{tag}{value}{tag}"


# 每張表:(用來找列的欄位, 要更新的欄位, 其中是 jsonb 的)
TABLES = {
    "game_cases": (("case_key",), ("title", "narrative", "provenance", "red_flags"), {"red_flags"}),
    "game_case_questions": (
        ("question_key", "version"),
        ("question", "explanation", "provenance", "options"),
        {"options"},
    ),
}


def sql(old_dump: str, new_dump: str) -> str:
    statements = []
    for table, (keys, columns, jsonb) in TABLES.items():
        old_rows = {tuple(r[k] for k in keys): r for r in copy_rows(old_dump, table)}
        for new in copy_rows(new_dump, table):
            key = tuple(new[k] for k in keys)
            old = old_rows.get(key)
            if old is None:
                continue
            where = " AND ".join(
                f"{k} = {v}" if k == "version" else f"{k} = {_literal(str(v))}"
                for k, v in zip(keys, key, strict=True)
            )
            for col in columns:
                if old[col] == new[col] or new[col] is None or old[col] is None:
                    continue
                cast = "::jsonb" if col in jsonb else ""
                statements.append(
                    f"UPDATE public.{table} SET {col} = {_literal(new[col])}{cast}\n"
                    f"  WHERE {where} AND {col} = {_literal(old[col])}{cast};"
                )
    pattern = f"[{CJK}][,:;!?()]|[,:;!?()][{CJK}]|——"
    body = "\n".join(statements)
    return f"""-- 題庫文字修正(2026-09-25):中文旁的半形標點轉全形 + 13 處措詞改寫。
-- 由同名的 .py 產生(說明見 .py 開頭)。逐列逐欄寫死新舊值,只有內容與舊種子一字不差才更新,可重複執行。
-- 用法見 docs/handoff/2026-09-24-adaptive-practice-wip.md 的「部署」一節。
BEGIN;
{body}
COMMIT;

-- 檢查:已發布的題目裡還剩幾列有中文旁的半形標點或破折號(應該都是 0)。
SELECT 'game_cases' AS 資料表, count(*) AS 還沒改到的列
  FROM public.game_cases
 WHERE status = 'published'
   AND (title || narrative || provenance || red_flags::text) ~ '{pattern}'
UNION ALL
SELECT 'game_case_questions', count(*)
  FROM public.game_case_questions
 WHERE status = 'published'
   AND (question || explanation || coalesce(provenance, '') || options::text) ~ '{pattern}';
"""


if __name__ == "__main__":
    if sys.argv[1:2] == ["--sql"]:
        old_path, new_path = sys.argv[2:4]
        print(sql(Path(old_path).read_text(), Path(new_path).read_text()), end="")
        sys.exit(0)
    for name in sys.argv[1:]:
        p = Path(name)
        before = p.read_text()
        after = normalize(before)
        changed = sum(1 for a, b in zip(before.splitlines(), after.splitlines()) if a != b)
        p.write_text(after)
        print(f"{changed:4d} 行  {name}")
