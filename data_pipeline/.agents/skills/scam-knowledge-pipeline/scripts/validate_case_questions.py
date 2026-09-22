#!/usr/bin/env python3
"""驗證查證題草稿、選項洩題線索與整批素材分散度。"""

import argparse
import json
from collections import Counter

from common import ROOT, read_jsonl, write_jsonl
from validate_game_cases import PII_PATTERNS

try:
    from jsonschema import Draft202012Validator
except ImportError:  # 裸 python3 也要能 import 這個模組(CI 用的就是裸 python3)
    Draft202012Validator = None

VERIFICATION_WORDS = (
    "查證",
    "求證",
    "官方",
    "165",
    "客服專線",
    "自己打",
    "親自",
    "打電話去",
    "原本的",
    "平台站內",
)


def load_schema_validator():
    schema = json.loads(
        (ROOT / "schemas" / "game_case_question.schema.json").read_text(
            encoding="utf-8"
        )
    )
    if Draft202012Validator is None:
        # 不能像 validate_game_cases 那樣回傳 None 靜默跳過:
        # 查證題的選項 key、長度上限全靠 schema 擋,跳過等於整批不驗。
        raise SystemExit(
            "缺少 jsonschema,無法驗證查證題 schema。請用 `uv run` 執行,"
            "或先安裝 jsonschema。"
        )
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def semantic_errors(rec):
    """只接收已通過 schema 的物件，避免壞型別中斷整批驗證。"""
    errors = []
    options = rec["options"]
    keys = [option["key"] for option in options]
    correct = [option for option in options if option["key"] == rec["correct_key"]]
    if not correct:
        errors.append("correct_key 必須出現在 options 的 key 中")
    if len(keys) != len(set(keys)):
        errors.append("options 的 key 不得重複")
    # 字數採去除頭尾空白後的 Unicode 字元數，與題庫既有長度檢查一致。
    lengths = [len(option["text"].strip()) for option in options]
    if not min(lengths) or max(lengths) > 2 * min(lengths):
        errors.append("最長選項字數不得超過最短選項的 2 倍，且不得為空白")

    def has_verification(text):
        return any(word in text for word in VERIFICATION_WORDS)

    if (
        correct
        and has_verification(correct[0]["text"])
        and not any(
            has_verification(option["text"])
            for option in options
            if option["key"] != rec["correct_key"]
        )
    ):
        errors.append("正解不得是唯一含查證類字樣的選項，至少一個誘答項也須包含")
    fields = [("question", rec["question"]), ("explanation", rec["explanation"])]
    fields.extend(
        (f"options[{i}].text", option["text"]) for i, option in enumerate(options)
    )
    for field, text in fields:
        for name, pattern in PII_PATTERNS:
            if pattern.search(text):
                errors.append(f"{field}: possible {name}（去識別化違規）")
    if correct and rec["explanation"] == correct[0]["text"]:
        errors.append("explanation 不得完全照抄正解選項文字")
    return errors


def _cluster_key(rec):
    """同一組選項文字視為一個叢集(與順序無關)。"""
    return frozenset(option["text"] for option in rec["options"])


# 叢集分布只在夠大的批次上才有意義:一次只驗一兩題時,「這組選項用在幾題」
# 根本無從判斷。低於這個數量就不套叢集規則,避免把單題驗證誤判成違規。
MIN_BATCH_FOR_CLUSTER_RULES = 6


def cluster_problems(records):
    """檢查同領域叢集的兩條硬規則。

    這兩條原本只寫在 curation.md 裡,沒有任何東西在執行。實測過:選項只用在
    一兩題、或某個選項當正解的比例過半時,「知道叢集就固定挑眾數」的命中率
    會明顯高過 1/選項數的基準線,而題庫長大時沒人會發現。
    """
    if len(records) < MIN_BATCH_FOR_CLUSTER_RULES:
        return {}
    groups = {}
    for rec in records:
        groups.setdefault(_cluster_key(rec), []).append(rec)
    problems = {}
    for key, members in groups.items():
        errors = []
        if len(members) < 3:
            errors.append(
                f"選項組只用在 {len(members)} 題；同一組選項至少要橫跨 3 題，"
                "否則正解無法在組內分散"
            )
        correct_texts = Counter(
            next(
                option["text"]
                for option in rec["options"]
                if option["key"] == rec["correct_key"]
            )
            for rec in members
        )
        top_text, top_count = correct_texts.most_common(1)[0]
        if top_count * 2 > len(members):
            errors.append(
                f"選項「{top_text}」在這組 {len(members)} 題裡當了 {top_count} 次正解，"
                "超過一半；固定挑它就會贏"
            )
        if errors:
            problems[key] = errors
    return problems


def validate_rows(input_rows):
    validator = load_schema_validator()
    checked = []
    for line_no, rec in input_rows:
        if isinstance(rec, dict) and "__json_error__" in rec:
            errors = [rec["__json_error__"]]
        else:
            errors = [
                f"{'.'.join(str(p) for p in e.path) or '<root>'}: {e.message}"
                for e in validator.iter_errors(rec)
            ]
        checked.append((line_no, rec, errors))

    # 先統計完整批次，再判斷每筆；不讓輸入順序決定超額案例哪兩題倖存。
    candidates = [rec for _, rec, errors in checked if not errors]
    case_counts = Counter(rec["case_key"] for rec in candidates)
    kind_counts = Counter((rec["case_key"], rec["question_kind"]) for rec in candidates)
    concentrated = len(case_counts) * 2 < len(candidates)
    cluster_errors = cluster_problems(candidates)
    seen, valid, rejected = set(), [], []
    for line_no, rec, errors in checked:
        if not errors:
            errors.extend(semantic_errors(rec))
            key = (rec["question_key"], rec.get("version", 1))
            if key in seen:
                errors.append(f"duplicate question_key/version: {key}")
            seen.add(key)
            if case_counts[rec["case_key"]] > 2:
                errors.append(f"case_key {rec['case_key']} 底下最多兩題")
            if kind_counts[(rec["case_key"], rec["question_kind"])] > 1:
                errors.append("同一 case_key 每種 question_kind 最多一題")
            errors.extend(cluster_errors.get(_cluster_key(rec), ()))
            if concentrated:
                errors.append(
                    f"素材過度集中：案例數 {len(case_counts)} 不得少於查證題總數 "
                    f"{len(candidates)} 的一半"
                )
        if errors:
            rejected.append({"line": line_no, "errors": errors, "record": rec})
        else:
            valid.append(rec)
    return valid, rejected


def main():
    parser = argparse.ArgumentParser(
        description="驗證 game_case_questions 草稿 JSONL。"
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--valid-output", required=True)
    parser.add_argument("--reject-output", required=True)
    args = parser.parse_args()
    valid, rejected = validate_rows(list(read_jsonl(args.input)))
    write_jsonl(args.valid_output, valid)
    write_jsonl(args.reject_output, rejected)
    print(
        json.dumps({"valid": len(valid), "rejected": len(rejected)}, ensure_ascii=False)
    )
    return 1 if rejected else 0


if __name__ == "__main__":
    raise SystemExit(main())
