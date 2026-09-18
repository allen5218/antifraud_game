#!/usr/bin/env python3
"""量測 game_cases 的「體裁洩題率」——不靠任何反詐知識、只憑敘事形式就猜中 is_scam 的比例。

為什麼需要這支:題庫改編自 165 等宣導素材,而宣導素材本身是「事後檢討」體裁。
詐騙案例以「事後我才知道…整個都是圈套」或「幸好及時收手」收尾,正當案例以
「正因為…我才放心」收尾——敘述者永遠在最後替讀者把答案講完。
玩家不需要懂反詐,只要看敘述者表態了什麼就能滿分——這是體裁層級的洩題,
把「官方保障」之類的刻意字眼刪掉並不會修好它。

四種探針(可疊加):
  lexical  純規則、免 API、可放進 CI:用結尾句式關鍵詞分類。
  match    純規則、免 API:逐句檢查 red_flag 是否洩漏自己 tag 或誤導到其他 tag。
  genre    LLM 探針,明令禁止使用反詐知識,只問「敘述者有沒有自己把答案講出來」,
           並回報是哪一句講的。
  title    只看標題判斷(標題本身也會洩題)。

另可用 --tag-balance 統計五種 tag 的出現次數、fraud_type 涵蓋與 tactics
合格題數；--min-tag-count N 可作為 CI 最低素材量門檻。

判讀:50% = 完全沒洩(等同擲硬幣);接近 100% = 題目在送分。
重寫題庫前先跑一次留 baseline,重寫後再跑一次比較。

範例:
  # 免 API、免 DB,直接量committed 的種子快照
  python3 scripts/leak_probe.py --from-dump ../../../../deploy/seed/game_cases.sql

  # 對 DB 裡的 published 題庫跑 LLM 體裁探針,並存下逐題明細
  python3 scripts/leak_probe.py --from-db --probe lexical,genre --json-output leak.json

  # CI 閘門:洩題率超過 0.75 就 fail
  python3 scripts/leak_probe.py --from-db --fail-over 0.75
"""

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

from common import WEAKNESS_TAGS, fetch_url, load_env, psql_scalar, read_jsonl

# ── 結尾句式關鍵詞(lexical 探針)────────────────────────────
# 每條都是「敘事形式」的訊號,不是詐騙手法的訊號——這正是重點:
# 這些詞彙跟受害者怎麼被騙無關,只跟「敘述者已經表態、答案已被說出」有關。
#
# 注意「逃過一劫」那一組:詐騙題不一定以壞結局收尾,有些寫成「幸好及時收手」。
# 它們一樣洩題(讀者照樣秒懂),只是方向不同——漏掉這組會低估洩題率。
SCAM_ENDING_PATTERNS = [
    (
        "事後才知",
        r"(事後|後來|這才|之後)[^。,,]{0,8}(知道|發現|驚覺|想起|明白|察覺|才懂|醒悟)",
    ),
    ("點破騙局", r"(圈套|騙局|上當|受騙|詐騙集團|詐團|人間蒸發|求償無門|血本無歸)"),
    (
        "對方消失",
        r"(封鎖我|已讀不回|失聯|聯繫不上|找不到人|再也(沒有|沒)|網站[^。,,]{0,6}關閉)",
    ),
    (
        "損失已成",
        r"(被轉走|拿不回|遲遲沒|始終沒收到|根本沒收到|對不上|沒收到貨|沒有出貨)",
    ),
    ("原來如此", r"原來[^。,,]{0,10}(就是|是這|手法|詐騙)"),
    (
        "逃過一劫",
        r"(幸好|所幸|還好)[^。,,]{0,12}(收手|沒|阻止|停下|掛掉|查證|想起|發現)",
    ),
    ("沒讓得逞", r"(沒讓對方得逞|沒有照做|沒有上當|沒有匯|差點就|及時收手|立刻阻止)"),
]
LEGIT_ENDING_PATTERNS = [
    ("正因為句式", r"正因為"),
    ("我才安心", r"我才[^。,,]{0,6}(放心|確定|安心|敢|不必|沒有)"),
    ("安心結語", r"(很安心|不必擔心|不用擔心|銀貨兩訖|有保障|才放心)"),
]

# match 題會把 red_flag.text 原文直接顯示給玩家。完整詞庫同時供報表使用；
# hard 子集合只放「看到詞本身就等於看到分類名稱」的分析式用語。其餘詞彙
# 常是案例不可或缺的具體行為或誘因，仍會列入報表，但不阻止草稿通過。
TAG_TELL_WORDS = {
    "time_pressure": ["時間壓力", "急迫", "限時", "倒數", "趕快", "催促"],
    "authority": ["權威", "官方", "冒充", "假冒", "主管機關"],
    "greed": ["貪念", "貪", "高報酬", "獲利", "超低價", "便宜"],
    "social_proof": ["社會認同", "從眾", "大家都", "很多人", "跟風"],
    "trust_building": ["信任", "取信", "建立關係", "感情"],
}

HARD_TAG_TELL_WORDS = {
    "time_pressure": ["時間壓力", "急迫"],
    "authority": ["權威", "官方", "主管機關"],
    "greed": ["貪念", "貪"],
    "social_proof": ["社會認同", "從眾", "跟風"],
    "trust_building": ["信任", "取信", "建立關係"],
}

# 尾段窗格:體裁洩題集中在結尾,單獨量一次尾段可證明這件事
TAIL_RATIO = 0.25
TAIL_MIN_CHARS = 80

GENRE_SYSTEM = """你是閱讀理解測驗員,完全不懂詐騙,也不准使用任何反詐騙知識。

你唯一的任務:判斷這段文字裡,**敘述者本人有沒有明講出結論**。

嚴格禁止:自己去評估文中的行為是否可疑、是否違反常識、是否有風險。
你不准推理「要求到 ATM 操作很奇怪」這種事——那需要反詐知識,你沒有。
你只能回報「敘述者說了什麼」:

- resolved_scam:敘述者已經明說這是一場騙局。包含事後懊悔(「事後才知道整個
  都是圈套」「對方封鎖我」),也包含逃過一劫(「幸好及時收手,沒讓對方得逞」
  「所幸家人阻止我」「我沒有照做,掛掉電話查證」)——只要敘述者已經表態
  「那是詐騙」,不論他有沒有損失,都算。
- resolved_legit:敘述者已經明說這是正常、安全、可信的(「正因為…我才放心」
  「我才確定這是正規流程」)。
- unresolved:敘述者沒有表態。事情停在進行中,結果未知,讀者必須自己判斷。

只輸出 JSON:
{"verdict": "resolved_scam" | "resolved_legit" | "unresolved",
 "confidence": 0.0 到 1.0,
 "giveaway": "敘述者表態的那一句(逐字抄錄;若 unresolved 則空字串)",
 "reason": "一句話說明"}"""

TITLE_SYSTEM = """你是標題語感分析員,完全不懂詐騙,也不准使用任何反詐騙知識。
只依標題的用詞與語氣,判斷它暗示的是一件「有人受害/被設局的事」,
還是一件「順利、安全、正常完成的事」。

只輸出 JSON:
{"verdict": "resolved_scam" | "resolved_legit" | "unresolved", "confidence": 0.0 到 1.0,
 "giveaway": "標題中最關鍵的詞", "reason": "一句話"}"""


# ── 資料來源 ────────────────────────────────────────────────
def _tail(text):
    """取敘事尾段——體裁洩題的集中處。"""
    n = max(TAIL_MIN_CHARS, int(len(text) * TAIL_RATIO))
    return text[-n:]


def _unescape_copy(value):
    """還原 pg_dump COPY 格式的跳脫字元。"""
    if value == r"\N":
        return None
    out, i = [], 0
    mapping = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\"}
    while i < len(value):
        if value[i] == "\\" and i + 1 < len(value) and value[i + 1] in mapping:
            out.append(mapping[value[i + 1]])
            i += 2
            continue
        out.append(value[i])
        i += 1
    return "".join(out)


def load_from_dump(path, published_only=True):
    """從 committed 的 pg_dump 種子檔讀取——免 DB、免 API,CI 也跑得動。"""
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    header_re = re.compile(r"^COPY public\.game_cases \(([^)]*)\) FROM stdin;")
    start, cols = None, None
    for idx, line in enumerate(lines):
        m = header_re.match(line)
        if m:
            start = idx + 1
            cols = [c.strip() for c in m.group(1).split(",")]
            break
    if start is None:
        raise SystemExit(f"找不到 game_cases 的 COPY 區塊: {path}")

    cases = []
    for line in lines[start:]:
        if line == r"\.":
            break
        values = [_unescape_copy(v) for v in line.split("\t")]
        if len(values) != len(cols):
            continue
        row = dict(zip(cols, values))
        if published_only and row.get("status") != "published":
            continue
        cases.append(
            {
                "id": row.get("id"),
                "case_key": row.get("case_key"),
                "fraud_type": row.get("fraud_type"),
                "is_scam": row.get("is_scam") == "t",
                "title": row.get("title") or "",
                "narrative": row.get("narrative") or "",
                "red_flags": json.loads(row.get("red_flags") or "[]"),
            }
        )
    return cases


def load_from_db(published_only=True):
    where = "WHERE status = 'published'" if published_only else ""
    sql = (
        "SELECT COALESCE(json_agg(json_build_object("
        "'id', id, 'case_key', case_key, 'fraud_type', fraud_type, "
        "'is_scam', is_scam, 'title', title, 'narrative', narrative, "
        "'red_flags', red_flags"
        f") ORDER BY id), '[]'::json) FROM game_cases {where};"
    )
    return json.loads(psql_scalar(sql))


def load_from_jsonl(path):
    """讀策展中的草稿 JSONL——讓你在 ingest 之前就先驗收體裁。"""
    cases = []
    for line_no, rec in read_jsonl(path):
        if "__json_error__" in rec:
            raise SystemExit(f"{path}:{line_no} JSON 解析失敗: {rec['__json_error__']}")
        cases.append(
            {
                "id": rec.get("case_key"),
                "case_key": rec.get("case_key"),
                "fraud_type": rec.get("fraud_type"),
                "is_scam": bool(rec.get("is_scam")),
                "title": rec.get("title") or "",
                "narrative": rec.get("narrative") or "",
                "red_flags": rec.get("red_flags") or [],
            }
        )
    return cases


# ── 探針 ────────────────────────────────────────────────────
def _match_patterns(text, patterns):
    hits = []
    for name, pattern in patterns:
        m = re.search(pattern, text)
        if m:
            hits.append({"pattern": name, "matched": m.group(0)})
    return hits


def probe_lexical(case, scope="full"):
    text = case["narrative"] if scope == "full" else _tail(case["narrative"])
    scam_hits = _match_patterns(text, SCAM_ENDING_PATTERNS)
    legit_hits = _match_patterns(text, LEGIT_ENDING_PATTERNS)
    if len(scam_hits) == len(legit_hits):
        predicted = None  # 無法判定:等同擲硬幣
    else:
        predicted = len(scam_hits) > len(legit_hits)
    giveaway = "; ".join(h["matched"] for h in (scam_hits + legit_hits))
    return {
        "predicted_is_scam": predicted,
        "giveaway": giveaway,
        "reason": "; ".join(h["pattern"] for h in (scam_hits + legit_hits)),
        "hits": {"scam": scam_hits, "legit": legit_hits},
    }


def probe_match(cases):
    """逐句檢查 match 例句是否洩漏自己 tag，或被其他 tag 詞彙干擾。"""
    rows = []
    for case in cases:
        if not case.get("is_scam"):
            continue
        for index, flag in enumerate(case.get("red_flags") or [], 1):
            tag = flag.get("tag")
            text = flag.get("text") or ""
            own_hits = [word for word in TAG_TELL_WORDS.get(tag, []) if word in text]
            other_hits = {
                other_tag: [word for word in words if word in text]
                for other_tag, words in TAG_TELL_WORDS.items()
                if other_tag != tag and any(word in text for word in words)
            }
            rows.append(
                {
                    "case_key": case.get("case_key"),
                    "fraud_type": case.get("fraud_type"),
                    "flag_index": index,
                    "tag": tag,
                    "text": text,
                    "own_hits": own_hits,
                    "other_hits": other_hits,
                }
            )
    return rows


def match_score(rows):
    """match leak_rate 定義為自己 tag 洩題句數除以全部 scam 例句數。"""
    total = len(rows)
    own_leaks = sum(bool(row["own_hits"]) for row in rows)
    other_leaks = sum(bool(row["other_hits"]) for row in rows)
    return {
        "total": total,
        "own_leaks": own_leaks,
        "other_leaks": other_leaks,
        "leak_rate": round(own_leaks / total, 4) if total else None,
    }


def tag_balance(cases):
    """統計 scam red_flag 出現次數、類型涵蓋與 tactics 合格題數。"""
    tag_types = {tag: set() for tag in TAG_TELL_WORDS}
    counts = {tag: 0 for tag in TAG_TELL_WORDS}
    scam_cases = 0
    tactics_qualified = 0
    for case in cases:
        if not case.get("is_scam"):
            continue
        scam_cases += 1
        distinct = set()
        for flag in case.get("red_flags") or []:
            tag = flag.get("tag")
            if tag not in WEAKNESS_TAGS:
                continue
            counts[tag] += 1
            distinct.add(tag)
            tag_types[tag].add(case.get("fraud_type"))
        tactics_qualified += len(distinct) >= 2
    return {
        "tags": {
            tag: {
                "count": counts[tag],
                "fraud_type_count": len(tag_types[tag]),
                "fraud_types": sorted(tag_types[tag]),
            }
            for tag in TAG_TELL_WORDS
        },
        "scam_cases": scam_cases,
        "tactics_qualified": tactics_qualified,
    }


# 用 responseSchema 強制結構化輸出;僅靠 responseMimeType 時模型會偶爾吐出
# reason 欄位含未跳脫引號、或物件後面多接內容的非法 JSON。
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "verdict": {
            "type": "STRING",
            "enum": ["resolved_scam", "resolved_legit", "unresolved"],
        },
        "confidence": {"type": "NUMBER"},
        "giveaway": {"type": "STRING"},
        "reason": {"type": "STRING"},
    },
    "required": ["verdict", "giveaway", "reason"],
}
VERDICT_RE = re.compile(r'"verdict"\s*:\s*"(resolved_scam|resolved_legit|unresolved)"')
GIVEAWAY_RE = re.compile(r'"giveaway"\s*:\s*"(.*?)"\s*[,}]', re.S)


def _lenient_parse(text):
    """先照嚴格 JSON 解;失敗就退回抓 verdict/giveaway 欄位。

    模型偶爾產出非法 JSON,但 verdict 幾乎總是可辨識的——為了一個逗號
    把整題丟掉會讓量測失真,所以這裡寬容,但仍在結果標記 lenient。
    """
    try:
        return json.loads(text), False
    except ValueError:
        m = VERDICT_RE.search(text)
        if not m:
            return None, False
        g = GIVEAWAY_RE.search(text)
        return {
            "verdict": m.group(1),
            "giveaway": g.group(1) if g else "",
            "reason": "",
        }, True


def _gemini_json(system, user, *, model, api_key, retries=1):
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
        },
    }
    last_error = ""
    for _ in range(retries + 1):
        resp = fetch_url(url, method="POST", json_body=body, timeout=60)
        if not resp["ok"]:
            last_error = f"HTTP {resp['status']}: {resp['body'][:600]}"
            continue
        try:
            payload = json.loads(resp["body"])
            parts = payload["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts)
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            # 不吞錯:留下原始 body 讓失敗可診斷,而不是靜靜算成棄權
            last_error = f"{type(exc).__name__}: {exc} | raw={resp['body'][:600]}"
            continue
        parsed, lenient = _lenient_parse(text)
        if parsed is not None:
            parsed["__lenient__"] = lenient
            return parsed
        last_error = f"無法從模型輸出取出 verdict | text={text[:600]}"
    return {"__error__": last_error}


def probe_llm(case, *, system, field, model, api_key):
    content = case["title"] if field == "title" else case["narrative"]
    result = _gemini_json(system, content, model=model, api_key=api_key)
    if "__error__" in result:
        return {
            "predicted_is_scam": None,
            "giveaway": "",
            "reason": f"[error] {result['__error__']}",
            "error": result["__error__"],
        }
    verdict = result.get("verdict")
    predicted = {"resolved_scam": True, "resolved_legit": False}.get(verdict)
    return {
        "predicted_is_scam": predicted,
        "giveaway": str(result.get("giveaway", "")),
        "reason": str(result.get("reason", "")),
        "confidence": result.get("confidence"),
        "lenient": bool(result.get("__lenient__")),
    }


# ── 計分 ────────────────────────────────────────────────────
def score(rows):
    """回傳整體與分組統計。

    leak_rate 是頭條數字:把「棄權」算成擲硬幣(0.5),
    等於「一個只會這招的玩家實際能拿到的分數」。50% = 沒洩,100% = 全送。

    呼叫失敗(errors)是量測故障、不是模型棄權,一律排除在分母外——
    否則 API 越不穩、洩題率看起來越低,指標會自己騙自己。
    """
    total = len(rows)
    errors = sum(1 for r in rows if r.get("error"))
    scored = [r for r in rows if not r.get("error")]
    n = len(scored)
    base = {"total": total, "errors": errors, "scored": n}
    if n == 0:
        return {
            **base,
            "leak_rate": None,
            "accuracy_when_decided": None,
            "coverage": None,
        }
    correct = sum(1 for r in scored if r["predicted_is_scam"] == r["is_scam"])
    undecided = sum(1 for r in scored if r["predicted_is_scam"] is None)
    decided = n - undecided
    return {
        **base,
        "correct": correct,
        "wrong": n - correct - undecided,
        "undecided": undecided,
        "lenient": sum(1 for r in scored if r.get("lenient")),
        "leak_rate": round((correct + 0.5 * undecided) / n, 4),
        "accuracy_when_decided": round(correct / decided, 4) if decided else None,
        "coverage": round(decided / n, 4),
    }


def group_score(rows, key):
    groups = {}
    for r in rows:
        groups.setdefault(r[key], []).append(r)
    return {
        str(k): score(v) for k, v in sorted(groups.items(), key=lambda kv: str(kv[0]))
    }


def pattern_stats(rows):
    """每條 lexical 規則命中幾題、其中多少題方向正確——用來汰換噪音規則。"""
    stats = {}
    for r in rows:
        hits = r.get("hits")
        if not hits:
            continue
        for side, expected in (("scam", True), ("legit", False)):
            for h in hits[side]:
                s = stats.setdefault(
                    h["pattern"], {"fired": 0, "aligned": 0, "side": side}
                )
                s["fired"] += 1
                s["aligned"] += int(r["is_scam"] == expected)
    for s in stats.values():
        s["precision"] = round(s["aligned"] / s["fired"], 4) if s["fired"] else None
    return dict(sorted(stats.items(), key=lambda kv: kv[1]["fired"], reverse=True))


# ── 報表 ────────────────────────────────────────────────────
def _bar(rate):
    filled = int(round(rate * 20))
    return "█" * filled + "·" * (20 - filled)


def print_report(name, rows, *, show_patterns=False, detail_limit=0):
    s = score(rows)
    print(f"\n{'=' * 66}")
    print(f"探針:{name}")
    print("=" * 66)
    if s["total"] == 0 or s["leak_rate"] is None:
        print(f"  無有效資料(全部 {s['errors']} 題呼叫失敗)")
        return s
    print(
        f"  洩題率 leak_rate  {s['leak_rate']:>7.1%}  {_bar(s['leak_rate'])}"
        f"   (50% = 沒洩,100% = 全送分)"
    )
    print(
        f"  判定涵蓋率        {s['coverage']:>7.1%}"
        f"   猜對 {s['correct']} / 猜錯 {s['wrong']} / 棄權 {s['undecided']}"
        f"   有效題數 {s['scored']}/{s['total']}"
        + (f"(呼叫失敗 {s['errors']} 題已排除)" if s["errors"] else "")
    )
    if s.get("lenient"):
        print(f"  ⚠ 其中 {s['lenient']} 題的模型輸出非嚴格 JSON,以寬容模式取出 verdict")

    print("\n  ── 依 is_scam ──")
    for label, sub in group_score(rows, "is_scam").items():
        tag = "詐騙題" if label == "True" else "正當題"
        print(
            f"    {tag}({sub['total']:>2} 題)  洩題率 {sub['leak_rate']:>6.1%}  {_bar(sub['leak_rate'])}"
        )

    print("\n  ── 依 fraud_type ──")
    for label, sub in group_score(rows, "fraud_type").items():
        print(
            f"    {label:<12}({sub['total']:>2} 題)  洩題率 {sub['leak_rate']:>6.1%}  {_bar(sub['leak_rate'])}"
        )

    if show_patterns:
        stats = pattern_stats(rows)
        if stats:
            print("\n  ── 各規則命中狀況(precision 低的是噪音規則,該汰換)──")
            for pat, st in stats.items():
                print(
                    f"    {pat:<10} 命中 {st['fired']:>2} 題  方向正確率 {st['precision']:>6.1%}"
                )

    if detail_limit:
        print(f"\n  ── 逐題明細(前 {detail_limit} 題,giveaway = 洩題的那句話)──")
        for r in rows[:detail_limit]:
            mark = (
                "✓"
                if r["predicted_is_scam"] == r["is_scam"]
                else ("?" if r["predicted_is_scam"] is None else "✗")
            )
            print(
                f"    {mark} {str(r['case_key']):<26} 實際={'scam ' if r['is_scam'] else 'legit'}"
            )
            if r["giveaway"]:
                print(f"        洩題句:{r['giveaway'][:70]}")
    return s


def print_match_report(rows):
    summary = match_score(rows)
    print(f"\n{'=' * 66}")
    print("探針:match(免 API，逐句檢查 tag 洩題詞)")
    print("=" * 66)
    if summary["leak_rate"] is None:
        print("  無 scam red_flag 可量測")
        return summary
    print(
        f"  match leak_rate   {summary['leak_rate']:>7.1%}  {_bar(summary['leak_rate'])}"
    )
    print(
        "  定義:自己 tag 洩題句數 / scam red_flag 總句數 = "
        f"{summary['own_leaks']} / {summary['total']}"
    )
    print(f"  含其他 tag 洩題詞的句數:{summary['other_leaks']}")
    print("\n  ── 逐句明細 ──")
    for row in rows:
        own = ",".join(row["own_hits"]) or "-"
        other = (
            ";".join(
                f"{tag}:{','.join(words)}" for tag, words in row["other_hits"].items()
            )
            or "-"
        )
        print(
            f"    {row['case_key']}#{row['flag_index']} [{row['tag']}] "
            f"自己={own} 其他={other} | {row['text']}"
        )
    return summary


def print_tag_balance(balance):
    print(f"\n{'=' * 66}")
    print("tag balance(published 或輸入中的 scam red_flags)")
    print("=" * 66)
    for tag, stats in balance["tags"].items():
        print(
            f"  {tag:<16} 出現 {stats['count']:>2} 次  "
            f"fraud_type {stats['fraud_type_count']} 種 "
            f"({', '.join(stats['fraud_types']) or '-'})"
        )
    print(
        f"  tactics 合格題數:{balance['tactics_qualified']} / {balance['scam_cases']} scam"
    )


# ── 主流程 ──────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(
        description="量測 game_cases 的體裁洩題率(不用反詐知識就能猜中 is_scam 的比例)。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--from-db", action="store_true", help="從 DB 讀(需 DATABASE_URL)")
    src.add_argument(
        "--from-dump", metavar="PATH", help="從 pg_dump 種子檔讀(免 DB、免 API)"
    )
    src.add_argument("--input", metavar="PATH", help="從策展草稿 JSONL 讀")
    p.add_argument(
        "--probe",
        default="lexical",
        help="逗號分隔:lexical(免費) / match(免費) / genre(LLM) / title(LLM) / all。預設 lexical",
    )
    p.add_argument(
        "--tag-balance",
        action="store_true",
        help="統計五種 tag 覆蓋與 tactics 合格題數",
    )
    p.add_argument(
        "--min-tag-count",
        type=int,
        metavar="N",
        help="任一 tag 出現次數低於 N 就 exit 1（需搭配 --tag-balance）",
    )
    p.add_argument(
        "--all-statuses", action="store_true", help="含 draft(預設只看 published)"
    )
    p.add_argument("--model", default="gemini-3.5-flash", help="LLM 探針用的模型")
    p.add_argument("--api-key-env", default="GOOGLE_API_KEY")
    p.add_argument("--env-file", help="載入 .env(不覆蓋既有環境變數)")
    p.add_argument("--concurrency", type=int, default=4, help="LLM 探針並發數")
    p.add_argument("--limit", type=int, help="只跑前 N 題(試跑用)")
    p.add_argument("--detail", type=int, default=0, help="印出前 N 題的逐題明細")
    p.add_argument("--json-output", help="把完整逐題結果寫成 JSON")
    p.add_argument(
        "--fail-over",
        type=float,
        metavar="RATE",
        help="任一探針洩題率超過此值就 exit 1(CI 閘門,例如 0.75)",
    )
    args = p.parse_args()

    if args.env_file:
        load_env(args.env_file)

    published_only = not args.all_statuses
    if args.from_dump:
        cases = load_from_dump(args.from_dump, published_only)
    elif args.from_db:
        cases = load_from_db(published_only)
    else:
        cases = load_from_jsonl(args.input)
    if args.limit:
        cases = cases[: args.limit]
    if not cases:
        raise SystemExit("沒有題目可量測")

    probes = [x.strip() for x in args.probe.split(",") if x.strip()]
    if "all" in probes:
        probes = ["lexical", "lexical-tail", "match", "genre", "title"]
    if args.min_tag_count is not None and not args.tag_balance:
        raise SystemExit("--min-tag-count 必須搭配 --tag-balance")

    needs_llm = any(x in probes for x in ("genre", "title"))
    api_key = os.environ.get(args.api_key_env, "")
    if needs_llm and not api_key:
        raise SystemExit(
            f"LLM 探針需要環境變數 {args.api_key_env}(或用 --env-file 載入)"
        )

    scam_n = sum(1 for c in cases if c["is_scam"])
    print(f"題數:{len(cases)}(詐騙 {scam_n} / 正當 {len(cases) - scam_n})")

    results, summary = {}, {}
    for probe in probes:
        if probe == "lexical":
            rows = [dict(c, **probe_lexical(c, "full")) for c in cases]
            label = "lexical(全文關鍵詞,免 API)"
        elif probe == "lexical-tail":
            rows = [dict(c, **probe_lexical(c, "tail")) for c in cases]
            label = f"lexical-tail(僅末 {int(TAIL_RATIO * 100)}% 文字)"
        elif probe == "match":
            rows = probe_match(cases)
            results[probe] = rows
            summary[probe] = print_match_report(rows)
            continue
        elif probe in ("genre", "title"):
            system = GENRE_SYSTEM if probe == "genre" else TITLE_SYSTEM
            field = "narrative" if probe == "genre" else "title"
            with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as pool:
                probed = list(
                    pool.map(
                        lambda c: probe_llm(
                            c,
                            system=system,
                            field=field,
                            model=args.model,
                            api_key=api_key,
                        ),
                        cases,
                    )
                )
            rows = [dict(c, **r) for c, r in zip(cases, probed)]
            label = (
                f"genre(LLM,禁用反詐知識,只問敘述者有沒有自己講出答案;{args.model})"
                if probe == "genre"
                else f"title(LLM,只看標題;{args.model})"
            )
        else:
            raise SystemExit(f"未知探針: {probe}")

        results[probe] = rows
        summary[probe] = print_report(
            label,
            rows,
            show_patterns=probe.startswith("lexical"),
            detail_limit=args.detail,
        )

    if args.tag_balance:
        balance = tag_balance(cases)
        print_tag_balance(balance)
        summary["tag_balance"] = balance

    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(
                {"summary": summary, "results": results},
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"\n逐題結果已寫入 {args.json_output}")

    exit_code = 0
    if args.fail_over is not None:
        breached = {
            k: v["leak_rate"]
            for k, v in summary.items()
            if v.get("leak_rate") is not None and v["leak_rate"] > args.fail_over
        }
        if breached:
            print(f"\n✗ 洩題率超過門檻 {args.fail_over}: {breached}", file=sys.stderr)
            exit_code = 1
        else:
            print(f"\n✓ 所有探針洩題率都在門檻 {args.fail_over} 以內")

    if args.min_tag_count is not None:
        below = {
            tag: stats["count"]
            for tag, stats in summary["tag_balance"]["tags"].items()
            if stats["count"] < args.min_tag_count
        }
        if below:
            print(
                f"\n✗ tag 出現次數低於門檻 {args.min_tag_count}: {below}",
                file=sys.stderr,
            )
            exit_code = 1
        else:
            print(f"\n✓ 所有 tag 出現次數都至少為 {args.min_tag_count}")

    # JSON 摘要永遠是 stdout 的最後一行,方便 CI 直接 tail -1 解析
    print("\n" + json.dumps(summary, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
