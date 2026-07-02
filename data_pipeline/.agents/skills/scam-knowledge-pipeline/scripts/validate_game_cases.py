#!/usr/bin/env python3
"""驗證 game_cases 草稿 JSONL(spec §5 品質規則 + 去識別化檢查)。"""
import argparse
import json
import re
from common import ROOT, WEAKNESS_TAGS, read_jsonl, write_jsonl

try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None

NARRATIVE_MIN, NARRATIVE_MAX = 150, 600
PII_PATTERNS = [
    ("phone", re.compile(r"09\d{2}[- ]?\d{3}[- ]?\d{3}")),
    ("landline", re.compile(r"0\d{1,2}[- ]?\d{3,4}[- ]?\d{4}")),
    ("national_id", re.compile(r"[A-Z][12]\d{8}")),
    ("account_number", re.compile(r"\d{10,16}")),
    ("url", re.compile(r"https?://")),
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
]


def load_schema_validator():
    schema = json.loads((ROOT / "schemas" / "game_case.schema.json").read_text(encoding="utf-8"))
    if Draft202012Validator is None:
        return None
    v = Draft202012Validator(schema)
    v.check_schema(schema)
    return v


def semantic_errors(rec):
    errors = []
    narrative = rec.get("narrative") or ""
    if not (NARRATIVE_MIN <= len(narrative) <= NARRATIVE_MAX):
        errors.append(f"narrative length {len(narrative)} not in {NARRATIVE_MIN}..{NARRATIVE_MAX}")
    tags = [f.get("tag") for f in rec.get("red_flags", []) if isinstance(f, dict)]
    if rec.get("is_scam"):
        if not tags or any(t not in WEAKNESS_TAGS for t in tags):
            errors.append("scam red_flags tags must all be one of the 5 weakness_tags")
        if not rec.get("source_document_ids"):
            errors.append("scam case requires at least one source_document_id")
    else:
        if any(t is not None for t in tags):
            errors.append("legit red_flags tags must all be null")
        if not rec.get("mirror_of_key") and not rec.get("source_document_ids"):
            errors.append("legit case requires mirror_of_key or source_document_ids")
    for text in [narrative, rec.get("title") or ""]:
        for name, pattern in PII_PATTERNS:
            if pattern.search(text):
                errors.append(f"possible {name} in text (去識別化違規)")
    return errors


parser = argparse.ArgumentParser(description="Validate game_cases draft JSONL.")
parser.add_argument("--input", required=True)
parser.add_argument("--valid-output", required=True)
parser.add_argument("--reject-output", required=True)
args = parser.parse_args()

schema_validator = load_schema_validator()
seen_keys, valid, rejected = set(), [], []
for line_no, rec in read_jsonl(args.input):
    errors = []
    if "__json_error__" in rec:
        errors = [rec["__json_error__"]]
    else:
        if schema_validator is not None:
            for e in sorted(schema_validator.iter_errors(rec), key=lambda e: list(e.path)):
                errors.append(f"{'.'.join(str(p) for p in e.path) or '<root>'}: {e.message}")
        errors.extend(semantic_errors(rec))
        key = rec.get("case_key")
        if key in seen_keys:
            errors.append(f"duplicate case_key: {key}")
        seen_keys.add(key)
    (rejected if errors else valid).append(
        {"line": line_no, "errors": errors, "record": rec} if errors else rec
    )

write_jsonl(args.valid_output, valid)
write_jsonl(args.reject_output, rejected)
print(json.dumps({"valid": len(valid), "rejected": len(rejected)}, ensure_ascii=False))
raise SystemExit(1 if rejected else 0)
