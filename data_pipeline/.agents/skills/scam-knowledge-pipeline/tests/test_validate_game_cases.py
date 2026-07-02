#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]

GOOD_SCAM = {
    "case_key": "inv-scam-001", "fraud_type": "investment", "is_scam": True,
    "title": "帶單群保證獲利", "narrative": "你在社群看到投資廣告,加入後群組每天貼獲利截圖。" * 8,
    "red_flags": [{"tag": "greed", "text": "保證獲利"}, {"tag": "social_proof", "text": "群組刷單"}],
    "difficulty": 2, "source_document_ids": [1], "provenance": "改編自:165 案例",
    "mirror_of_key": None,
}
GOOD_LEGIT = dict(
    GOOD_SCAM, case_key="inv-legit-001", is_scam=False, mirror_of_key="inv-scam-001",
    title="銀行理專正規諮詢", source_document_ids=[],
    red_flags=[{"tag": None, "text": "主動揭露風險"}, {"tag": None, "text": "不催促"}],
)


def run_validate(records):
    with tempfile.TemporaryDirectory() as td:
        inp, ok, rej = Path(td) / "in.jsonl", Path(td) / "ok.jsonl", Path(td) / "rej.jsonl"
        inp.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "validate_game_cases.py"),
             "--input", str(inp), "--valid-output", str(ok), "--reject-output", str(rej)],
            text=True, capture_output=True,
        )
        return proc.returncode, json.loads(proc.stdout.strip().splitlines()[-1])


class GameCaseValidateTests(unittest.TestCase):
    def test_good_pair_passes(self):
        code, out = run_validate([GOOD_SCAM, GOOD_LEGIT])
        self.assertEqual((code, out["valid"], out["rejected"]), (0, 2, 0))

    def test_narrative_too_short_rejected(self):
        code, out = run_validate([dict(GOOD_SCAM, narrative="太短")])
        self.assertEqual(out["rejected"], 1)

    def test_scam_with_illegal_tag_rejected(self):
        bad = dict(GOOD_SCAM, red_flags=[{"tag": "fomo", "text": "x"}, {"tag": "greed", "text": "y"}])
        code, out = run_validate([bad])
        self.assertEqual(out["rejected"], 1)

    def test_scam_without_source_rejected(self):
        code, out = run_validate([dict(GOOD_SCAM, source_document_ids=[])])
        self.assertEqual(out["rejected"], 1)

    def test_legit_without_anchor_rejected(self):
        bad = dict(GOOD_LEGIT, mirror_of_key=None, source_document_ids=[])
        code, out = run_validate([bad])
        self.assertEqual(out["rejected"], 1)

    def test_pii_phone_rejected(self):
        bad = dict(GOOD_SCAM, narrative=GOOD_SCAM["narrative"] + "請撥 0912-345-678 聯繫")
        code, out = run_validate([bad])
        self.assertEqual(out["rejected"], 1)

    def test_url_rejected(self):
        bad = dict(GOOD_SCAM, narrative=GOOD_SCAM["narrative"] + " https://scam.example ")
        code, out = run_validate([bad])
        self.assertEqual(out["rejected"], 1)


if __name__ == "__main__":
    unittest.main()
