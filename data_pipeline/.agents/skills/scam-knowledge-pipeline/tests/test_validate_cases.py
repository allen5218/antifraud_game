#!/usr/bin/env python3
"""驗證 stance/content_kind 欄位進入 schema 必填。離線可跑(用 fallback 或 jsonschema)。"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]

BASE_RECORD = {
    "source_name": "t", "source_type": "t", "source_url": "https://x", "fetched_at": "2026-07-02T00:00:00Z",
    "content_hash": "sha256:0123456789abcdef", "page_title": "t", "body_text": "b", "clean_text": "c",
    "raw_payload": {}, "taxonomy_code": "investment_fraud", "source_category_label": "投資詐欺",
    "matched_keywords": [], "classification_confidence": 0.9,
    "category_evidence": {"platforms": [], "payment_methods": [], "impersonated_roles": [],
                          "transaction_context": None, "relationship_signals": [],
                          "atm_or_installment_signals": [], "evidence_quotes": []},
    "extraction_notes": [], "classification_notes": [],
    "validation_status": "valid", "source_verification_status": "verified",
    "case_stance": "scam", "content_kind": "case_narrative",
}


def run_validate(records):
    with tempfile.TemporaryDirectory() as td:
        inp, ok, rej = Path(td) / "in.jsonl", Path(td) / "ok.jsonl", Path(td) / "rej.jsonl"
        inp.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "validate_cases.py"),
             "--input", str(inp), "--valid-output", str(ok), "--reject-output", str(rej)],
            text=True, capture_output=True,
        )
        return proc.returncode, json.loads(proc.stdout.strip().splitlines()[-1])


class StanceFieldTests(unittest.TestCase):
    def test_valid_record_passes(self):
        code, out = run_validate([BASE_RECORD])
        self.assertEqual((code, out["valid"], out["rejected"]), (0, 1, 0))

    def test_missing_stance_rejected(self):
        rec = {k: v for k, v in BASE_RECORD.items() if k != "case_stance"}
        code, out = run_validate([rec])
        self.assertEqual((code, out["rejected"]), (1, 1))

    def test_bad_content_kind_rejected(self):
        rec = dict(BASE_RECORD, content_kind="blog")
        code, out = run_validate([rec])
        self.assertEqual((code, out["rejected"]), (1, 1))


if __name__ == "__main__":
    unittest.main()
