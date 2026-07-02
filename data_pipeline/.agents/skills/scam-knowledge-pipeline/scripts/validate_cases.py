#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from common import ROOT, TAXONOMY_CODES, read_jsonl, write_jsonl

try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None

REQUIRED = [
    "source_name", "source_type", "source_url", "fetched_at", "content_hash",
    "page_title", "body_text", "clean_text", "raw_payload", "taxonomy_code",
    "source_category_label", "matched_keywords", "classification_confidence",
    "category_evidence", "extraction_notes", "classification_notes",
    "validation_status", "source_verification_status"
]
EVIDENCE_REQUIRED = [
    "platforms", "payment_methods", "impersonated_roles", "transaction_context",
    "relationship_signals", "atm_or_installment_signals", "evidence_quotes"
]

def load_schema_validator():
    schema_path = ROOT / "schemas" / "scam_case.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if Draft202012Validator is None:
        return None
    validator = Draft202012Validator(schema)
    validator.check_schema(schema)
    return validator

def fallback_validate(record):
    errors = []
    if "__json_error__" in record:
        return [record["__json_error__"]]
    for key in REQUIRED:
        if key not in record:
            errors.append(f"missing {key}")
    if record.get("taxonomy_code") not in TAXONOMY_CODES:
        errors.append("invalid taxonomy_code")
    confidence = record.get("classification_confidence")
    if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
        errors.append("classification_confidence must be 0..1")
    for list_key in ["matched_keywords", "extraction_notes", "classification_notes"]:
        if not isinstance(record.get(list_key), list):
            errors.append(f"{list_key} must be array")
    evidence = record.get("category_evidence")
    if not isinstance(evidence, dict):
        errors.append("category_evidence must be object")
    else:
        for key in EVIDENCE_REQUIRED:
            if key not in evidence:
                errors.append(f"missing category_evidence.{key}")
    if record.get("validation_status") != "valid":
        errors.append("validation_status must be valid before ingest")
    return errors

def validate(record, schema_validator):
    if "__json_error__" in record:
        return [record["__json_error__"]]
    if schema_validator is None:
        return fallback_validate(record)
    errors = []
    for error in sorted(schema_validator.iter_errors(record), key=lambda e: list(e.path)):
        path = ".".join(str(part) for part in error.path)
        errors.append(f"{path or '<root>'}: {error.message}")
    if record.get("validation_status") != "valid":
        errors.append("validation_status must be valid before ingest")
    return errors

parser = argparse.ArgumentParser(description="Validate classified scam case JSONL.")
parser.add_argument("--input", required=True)
parser.add_argument("--valid-output", required=True)
parser.add_argument("--reject-output", required=True)
args = parser.parse_args()

schema_validator = load_schema_validator()
valid, rejected = [], []
for line_no, record in read_jsonl(args.input):
    errors = validate(record, schema_validator)
    if errors:
        rejected.append({"line": line_no, "errors": errors, "record": record})
    else:
        valid.append(record)

write_jsonl(args.valid_output, valid)
write_jsonl(args.reject_output, rejected)
print(json.dumps({"valid": len(valid), "rejected": len(rejected)}, ensure_ascii=False))
raise SystemExit(1 if rejected else 0)
