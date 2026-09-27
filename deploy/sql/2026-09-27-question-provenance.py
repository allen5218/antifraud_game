"""題庫出處修正(2026-09-27):兩類標示不實的 provenance。

1. 假網拍詐騙 4 題寫「數位發展部高風險業者通報清單」,但連結的來源文件
   (source_document_ids 29～32、39)其實是 165 全民防騙網的「民眾通報高風險業者」。
2. 27 題引用 tw_manual_legit_process_docs 的 5 份文件,出處寫成「官方正規流程文件」
   或直接寫文件名。那 5 份是團隊依官方規範整理的流程說明,不是官方發布的文件,
   改標「團隊整理的正規流程說明」或「團隊整理的「…」」。

用法:
  就地改寫原稿與種子:
    python3 deploy/sql/2026-09-27-question-provenance.py <檔案>...
  產生給已上線環境的 UPDATE(舊值取自改版前的種子):
    git show HEAD:deploy/seed/game_cases.sql > /tmp/old_cases.sql
    python3 deploy/sql/2026-09-27-question-provenance.py --sql /tmp/old_cases.sql \
      > deploy/sql/2026-09-27-question-provenance.sql

只改 provenance 欄。UPDATE 逐列寫死新舊值,只有目前內容與舊種子一字不差才更新,可重複執行。
"""

import json
import sys
from pathlib import Path

# 依序套用;舊字串找不到就略過。半形版本給改版前的舊草稿用。
RULES: list[tuple[str, str]] = [
    (
        "數位發展部高風險業者通報清單（假網路拍賣）",
        "165 全民防騙網「民眾通報高風險業者」（假網路拍賣）",
    ),
    (
        "數位發展部高風險業者通報清單(假網路拍賣)",
        "165 全民防騙網「民眾通報高風險業者」(假網路拍賣)",
    ),
    ("官方正規流程文件「", "團隊整理的正規流程說明「"),
    ("依據：「正常網路交友互動特徵」", "依據：團隊整理的「正常網路交友互動特徵」"),
    ("依據:「正常網路交友互動特徵」", "依據:團隊整理的「正常網路交友互動特徵」"),
    ("與「正常網路交友互動特徵」", "與團隊整理的「正常網路交友互動特徵」"),
    ("依據：正常網路交友互動特徵與", "依據：團隊整理的「正常網路交友互動特徵」與"),
    ("依據:正常網路交友互動特徵與", "依據:團隊整理的「正常網路交友互動特徵」與"),
]


def fix(provenance: str) -> str:
    for old, new in RULES:
        provenance = provenance.replace(old, new)
    return provenance


def _copy_rows(text: str):
    """逐列產出 (行號, 欄位名, 欄位值);只看 game_cases 的 COPY 區塊。"""
    lines = text.split("\n")
    cols: list[str] | None = None
    for i, line in enumerate(lines):
        if line.startswith("COPY public.game_cases ("):
            cols = [
                c.strip()
                for c in line[line.index("(") + 1 : line.index(")")].split(",")
            ]
            continue
        if cols is not None:
            if line == "\\.":
                cols = None
                continue
            yield i, cols, line.split("\t")


def rewrite_dump(text: str) -> tuple[str, int]:
    lines = text.split("\n")
    changed = 0
    for i, cols, fields in _copy_rows(text):
        p = cols.index("provenance")
        new = fix(fields[p])
        if new != fields[p]:
            fields[p] = new
            lines[i] = "\t".join(fields)
            changed += 1
    return "\n".join(lines), changed


def rewrite_jsonl(text: str) -> tuple[str, int]:
    out, changed = [], 0
    for line in text.split("\n"):
        if line.strip():
            rec = json.loads(line)
            old = rec.get("provenance")
            if isinstance(old, str) and fix(old) != old:
                # 只替換 provenance 的值,保留原檔的鍵順序與格式
                enc = lambda s: json.dumps(s, ensure_ascii=False)[1:-1]  # noqa: E731
                assert line.count(enc(old)) == 1, rec.get("case_key")
                line = line.replace(enc(old), enc(fix(old)))
                changed += 1
        out.append(line)
    return "\n".join(out), changed


def emit_sql(old_dump: str) -> str:
    tag = "$prov$"
    rows = []
    for _, cols, fields in _copy_rows(old_dump):
        key, old = fields[cols.index("case_key")], fields[cols.index("provenance")]
        new = fix(old)
        if new != old:
            rows.append(
                f"UPDATE public.game_cases SET provenance = {tag}{new}{tag}\n"
                f"  WHERE case_key = {tag}{key}{tag} AND provenance = {tag}{old}{tag};"
            )
    head = [
        "-- 題庫出處修正(2026-09-27):假網拍 4 題的來源機構、27 題團隊整理文件的標示。",
        "-- 由同名的 .py 產生(說明見 .py 開頭)。逐列寫死新舊值,只有內容與舊種子一字不差才更新,可重複執行。",
        "BEGIN;",
    ]
    check = (
        "-- 檢查:應該都是 0\n"
        "SELECT count(*) FILTER (WHERE provenance LIKE '%數位發展部高風險業者%') AS moda_label,\n"
        "       count(*) FILTER (WHERE provenance LIKE '%官方正規流程文件%') AS official_label,\n"
        "       count(*) FILTER (WHERE provenance LIKE '%正常網路交友互動特徵%'\n"
        "                        AND provenance NOT LIKE '%團隊整理的%') AS unlabeled_team_doc\n"
        "  FROM public.game_cases;"
    )
    return "\n".join(head + rows + ["COMMIT;", "", check, ""])


def main(argv: list[str]) -> None:
    if argv[:1] == ["--sql"]:
        sys.stdout.write(emit_sql(Path(argv[1]).read_text(encoding="utf-8")))
        return
    for name in argv:
        path = Path(name)
        text = path.read_text(encoding="utf-8")
        new, n = rewrite_jsonl(text) if path.suffix == ".jsonl" else rewrite_dump(text)
        if n:
            path.write_text(new, encoding="utf-8")
        print(f"{name}: {n} 列", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
