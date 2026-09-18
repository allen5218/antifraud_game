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
    "source_name": "t",
    "source_type": "t",
    "source_url": "https://x",
    "fetched_at": "2026-07-02T00:00:00Z",
    "content_hash": "sha256:0123456789abcdef",
    "page_title": "t",
    "body_text": "這是一則完整案例敘事。" * 20,
    "clean_text": "這是一則完整案例敘事。" * 20,
    "raw_payload": {},
    "taxonomy_code": "investment_fraud",
    "source_category_label": "投資詐欺",
    "matched_keywords": [],
    "classification_confidence": 0.9,
    "category_evidence": {
        "platforms": [],
        "payment_methods": [],
        "impersonated_roles": [],
        "transaction_context": None,
        "relationship_signals": [],
        "atm_or_installment_signals": [],
        "evidence_quotes": [],
    },
    "extraction_notes": [],
    "classification_notes": [],
    "validation_status": "valid",
    "source_verification_status": "verified",
    "case_stance": "scam",
    "content_kind": "case_narrative",
}


def run_validate(records):
    with tempfile.TemporaryDirectory() as td:
        inp, ok, rej = (
            Path(td) / "in.jsonl",
            Path(td) / "ok.jsonl",
            Path(td) / "rej.jsonl",
        )
        inp.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in records),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                sys.executable,
                str(SKILL / "scripts" / "validate_cases.py"),
                "--input",
                str(inp),
                "--valid-output",
                str(ok),
                "--reject-output",
                str(rej),
            ],
            text=True,
            capture_output=True,
        )
        rejects = [
            json.loads(line)
            for line in rej.read_text(encoding="utf-8").splitlines()
            if line
        ]
        return (
            proc.returncode,
            json.loads(proc.stdout.strip().splitlines()[-1]),
            rejects,
        )


class StanceFieldTests(unittest.TestCase):
    def test_valid_record_passes(self):
        code, out, _ = run_validate([BASE_RECORD])
        self.assertEqual((code, out["valid"], out["rejected"]), (0, 1, 0))

    def test_missing_stance_rejected(self):
        rec = {k: v for k, v in BASE_RECORD.items() if k != "case_stance"}
        code, out, _ = run_validate([rec])
        self.assertEqual((code, out["rejected"]), (1, 1))

    def test_bad_content_kind_rejected(self):
        rec = dict(BASE_RECORD, content_kind="blog")
        code, out, _ = run_validate([rec])
        self.assertEqual((code, out["rejected"]), (1, 1))

    def test_message_sample_content_kind_is_accepted(self):
        rec = dict(
            BASE_RECORD, content_kind="message_sample", clean_text="投資邀請訊息" * 8
        )

        code, out, _ = run_validate([rec])

        self.assertEqual((code, out["valid"], out["rejected"]), (0, 1, 0))

    def test_empty_taxonomy_is_allowed_only_for_advisory_material(self):
        advisory = dict(
            BASE_RECORD,
            taxonomy_code=None,
            source_category_label=None,
            classification_confidence=0,
            classification_method="manual",
            case_stance="advisory",
            content_kind="advisory",
        )
        code, out, _ = run_validate([advisory])
        self.assertEqual((code, out["valid"], out["rejected"]), (0, 1, 0))

        invalid = dict(advisory, case_stance="scam", content_kind="message_sample")
        code, out, _ = run_validate([invalid])
        self.assertEqual((code, out["rejected"]), (1, 1))

    def test_cofacts_scam_message_may_keep_empty_taxonomy(self):
        record = dict(
            BASE_RECORD,
            source_name="tw_cofacts_scam_messages",
            taxonomy_code=None,
            source_category_label=None,
            classification_confidence=0,
            classification_method="manual",
            case_stance="scam",
            content_kind="message_sample",
        )

        code, out, _ = run_validate([record])

        self.assertEqual((code, out["valid"], out["rejected"]), (0, 1, 0))

    def test_case_narrative_shorter_than_150_chars_is_rejected_and_counted(self):
        rec = dict(BASE_RECORD, clean_text="短" * 149)

        code, out, rejects = run_validate([rec])

        self.assertEqual(code, 1)
        self.assertEqual(out["rejection_reasons"]["case_narrative_too_short"], 1)
        self.assertIn("case_narrative_too_short", rejects[0]["quality_reasons"])

    def test_case_narrative_longer_than_20000_chars_is_rejected_and_counted(self):
        rec = dict(BASE_RECORD, clean_text="長" * 20001)

        code, out, rejects = run_validate([rec])

        self.assertEqual(code, 1)
        self.assertEqual(out["rejection_reasons"]["case_narrative_too_long"], 1)
        self.assertIn("case_narrative_too_long", rejects[0]["quality_reasons"])

    def test_case_narrative_with_html_tag_is_rejected_and_counted(self):
        rec = dict(BASE_RECORD, clean_text="案例內容" * 40 + "<p>殘留標籤</p>")

        code, out, rejects = run_validate([rec])

        self.assertEqual(code, 1)
        self.assertEqual(out["rejection_reasons"]["case_narrative_contains_html"], 1)
        self.assertIn("case_narrative_contains_html", rejects[0]["quality_reasons"])

    def test_case_narrative_length_boundaries_are_allowed(self):
        records = [
            dict(BASE_RECORD, clean_text="字" * 150),
            dict(BASE_RECORD, clean_text="字" * 20000),
        ]

        code, out, _ = run_validate(records)

        self.assertEqual(code, 0)
        self.assertEqual((out["valid"], out["rejected"]), (2, 0))


if __name__ == "__main__":
    unittest.main()
