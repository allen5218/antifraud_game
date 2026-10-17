"""題庫改寫(2026-10-16):依題目檢查清單的拍板,改寫練習案例與查證題。

80 則案例(敘事、紅旗／正當訊號、出處、難度、1 組標題)與 25 題查證題(選項、正解、解析)。
改法:標「改」的題目重寫成口語、詐騙題只留兩種話術、正常題不放一看就知道答案的提示;
查證題換掉查不同對象的三組選項,每組選項仍橫跨 3 題以上、正解不過半。
原稿 data_pipeline/data/manual/*.jsonl 與兩份種子已一起改好;這支只負責產生給已上線環境的 UPDATE。

用法(舊值取自改版前的種子):
  git show 70db330:deploy/seed/game_cases.sql > /tmp/old_cases.sql
  python3 deploy/sql/2026-10-16-question-rewrites.py /tmp/old_cases.sql deploy/seed/game_cases.sql \
    > deploy/sql/2026-10-16-question-rewrites.sql

UPDATE 逐列逐欄寫死新舊值,以 case_key 或 (question_key, version) 找列,
只有目前內容與舊種子一字不差才更新;重跑時舊值已不存在,什麼都不會改。
對不上的列留在檔尾的檢查查詢裡。
"""

import re
import sys
from pathlib import Path

COPY_ESCAPES = {
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "v": "\v",
    "\\": "\\",
}

# 每張表:(用來找列的欄位, 要比對更新的欄位, 其中是 jsonb 的, 其中是整數的)
TABLES = {
    "game_cases": (
        ("case_key",),
        ("title", "narrative", "provenance", "red_flags", "difficulty"),
        {"red_flags"},
        {"difficulty"},
    ),
    "game_case_questions": (
        ("question_key", "version"),
        ("question", "options", "correct_key", "explanation"),
        {"options"},
        set(),
    ),
}


def _unescape(field: str) -> str | None:
    if field == "\\N":
        return None
    return re.sub(r"\\(.)", lambda m: COPY_ESCAPES.get(m.group(1), m.group(1)), field)


def copy_rows(dump: str, table: str) -> list[dict[str, str | None]]:
    lines = dump.splitlines()
    head = next(
        i for i, ln in enumerate(lines) if ln.startswith(f"COPY public.{table} (")
    )
    columns = lines[head][lines[head].index("(") + 1 : lines[head].index(")")].split(
        ", "
    )
    rows = []
    for ln in lines[head + 1 :]:
        if ln == "\\.":
            break
        rows.append(dict(zip(columns, map(_unescape, ln.split("\t")), strict=True)))
    return rows


def _literal(value: str) -> str:
    tag = "$rw$"
    assert tag not in value, "內容裡剛好有 dollar-quote 標記,換一個"
    return f"{tag}{value}{tag}"


def _value(col: str, value: str, jsonb: set[str], ints: set[str]) -> str:
    if col in ints:
        return str(int(value))
    return _literal(value) + ("::jsonb" if col in jsonb else "")


def sql(old_dump: str, new_dump: str) -> tuple[str, int]:
    statements = []
    for table, (keys, columns, jsonb, ints) in TABLES.items():
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
                if old[col] == new[col]:
                    continue
                assert old[col] is not None and new[col] is not None, (table, key, col)
                statements.append(
                    f"UPDATE public.{table} SET {col} = {_value(col, new[col], jsonb, ints)}\n"
                    f"  WHERE {where} AND {col} = {_value(col, old[col], jsonb, ints)};"
                )
    body = "\n".join(statements)
    check = (
        "-- 檢查:改寫後應有的列數(已發布的案例 120、查證題 34)\n"
        "SELECT 'game_cases' AS 資料表, count(*) FROM public.game_cases WHERE status = 'published'\n"
        "UNION ALL\n"
        "SELECT 'game_case_questions', count(*) FROM public.game_case_questions WHERE status = 'published';\n"
    )
    out = (
        "-- 題庫改寫(2026-10-16):練習案例與查證題依題目檢查清單的拍板改寫。\n"
        "-- 由同名的 .py 產生(說明見 .py 開頭)。逐列逐欄寫死新舊值,只有內容與舊種子一字不差才更新,可重複執行。\n"
        "BEGIN;\n" + body + "\nCOMMIT;\n\n" + check
    )
    return out, len(statements)


if __name__ == "__main__":
    old_path, new_path = sys.argv[1:3]
    text, n = sql(
        Path(old_path).read_text(encoding="utf-8"),
        Path(new_path).read_text(encoding="utf-8"),
    )
    print(text, end="")
    print(f"{n} 條 UPDATE", file=sys.stderr)
