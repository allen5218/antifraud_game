#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]

GOOD_SCAM = {
    "case_key": "inv-scam-001",
    "fraud_type": "investment",
    "is_scam": True,
    "title": "群組裡的投資邀請",
    "narrative": "你在社群看到投資廣告,加入後群組每天貼收益截圖。" * 8,
    "red_flags": [
        {"tag": "greed", "text": "聲稱每月收益遠高於定存並要求持續加碼"},
        {"tag": "social_proof", "text": "群組成員輪流貼出入帳截圖並附和老師說法"},
    ],
    "difficulty": 2,
    "source_document_ids": [1],
    "provenance": "改編自:165 案例",
    "mirror_of_key": None,
}
GOOD_LEGIT = dict(
    GOOD_SCAM,
    case_key="inv-legit-001",
    is_scam=False,
    mirror_of_key="inv-scam-001",
    source_document_ids=[],
    surface_tag="authority",
    red_flags=[{"tag": None, "text": "主動揭露風險"}, {"tag": None, "text": "不催促"}],
)


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
                str(SKILL / "scripts" / "validate_game_cases.py"),
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
        rejected = [
            json.loads(line) for line in rej.read_text(encoding="utf-8").splitlines()
        ]
        return (
            proc.returncode,
            json.loads(proc.stdout.strip().splitlines()[-1]),
            rejected,
        )


class GameCaseValidateTests(unittest.TestCase):
    def test_good_pair_passes(self):
        code, out, _ = run_validate([GOOD_SCAM, GOOD_LEGIT])
        self.assertEqual((code, out["valid"], out["rejected"]), (0, 2, 0))

    def test_narrative_too_short_rejected(self):
        code, out, _ = run_validate([dict(GOOD_SCAM, narrative="太短")])
        self.assertEqual(out["rejected"], 1)

    def test_scam_with_illegal_tag_rejected(self):
        bad = dict(
            GOOD_SCAM,
            red_flags=[{"tag": "fomo", "text": "x"}, {"tag": "greed", "text": "y"}],
        )
        code, out, _ = run_validate([bad])
        self.assertEqual(out["rejected"], 1)

    def test_scam_without_source_rejected(self):
        code, out, _ = run_validate([dict(GOOD_SCAM, source_document_ids=[])])
        self.assertEqual(out["rejected"], 1)

    def test_legit_without_anchor_rejected(self):
        bad = dict(GOOD_LEGIT, mirror_of_key=None, source_document_ids=[])
        code, out, _ = run_validate([bad])
        self.assertEqual(out["rejected"], 1)

    def test_pii_phone_rejected(self):
        bad = dict(
            GOOD_SCAM, narrative=GOOD_SCAM["narrative"] + "請撥 0912-345-678 聯繫"
        )
        code, out, _ = run_validate([bad])
        self.assertEqual(out["rejected"], 1)

    def test_url_rejected(self):
        bad = dict(
            GOOD_SCAM, narrative=GOOD_SCAM["narrative"] + " https://scam.example "
        )
        code, out, _ = run_validate([bad])
        self.assertEqual(out["rejected"], 1)

    def test_narrative_that_reveals_ending_is_rejected_with_matched_text(self):
        bad = dict(GOOD_SCAM, narrative=GOOD_SCAM["narrative"] + "事後我才知道不對勁。")
        _, out, rejected = run_validate([bad])
        self.assertEqual(out["rejected"], 1)
        self.assertIn("事後我才知道", " ".join(rejected[0]["errors"]))

    def test_scam_requires_two_distinct_tags(self):
        bad = dict(
            GOOD_SCAM,
            red_flags=[
                {"tag": "greed", "text": "聲稱每月收益遠高於定存並要求持續加碼"},
                {"tag": "greed", "text": "用未實現的帳面數字吸引投入更多資金"},
            ],
        )
        _, out, rejected = run_validate([bad])
        self.assertEqual(out["rejected"], 1)
        self.assertIn("at least 2 distinct", " ".join(rejected[0]["errors"]))

    def test_scam_red_flag_text_must_be_8_to_40_characters(self):
        for text in (
            "太短",
            "這是一段超過四十個中文字而且無法直接作為配對題例句的冗長描述文字需要被驗證器拒絕掉",
        ):
            with self.subTest(text=text):
                flags = [
                    dict(GOOD_SCAM["red_flags"][0], text=text),
                    GOOD_SCAM["red_flags"][1],
                ]
                _, out, rejected = run_validate([dict(GOOD_SCAM, red_flags=flags)])
                self.assertEqual(out["rejected"], 1)
                self.assertIn(
                    "red_flags[0].text length", " ".join(rejected[0]["errors"])
                )

    def test_own_tag_hard_tell_word_is_rejected_but_report_word_is_allowed(self):
        hard_flags = [
            {"tag": "social_proof", "text": "直播留言營造搶購的從眾氣氛"},
            GOOD_SCAM["red_flags"][0],
        ]
        _, out, rejected = run_validate([dict(GOOD_SCAM, red_flags=hard_flags)])
        self.assertEqual(out["rejected"], 1)
        self.assertIn("從眾", " ".join(rejected[0]["errors"]))

        report_only_flags = [
            {"tag": "time_pressure", "text": "對方反覆催促你在查證前完成付款"},
            GOOD_SCAM["red_flags"][0],
        ]
        code, out, _ = run_validate([dict(GOOD_SCAM, red_flags=report_only_flags)])
        self.assertEqual((code, out["valid"]), (0, 1))

    def test_title_directional_word_and_length_are_rejected(self):
        for title in (
            "假冒客服來電",
            "短題",
            "這是一個刻意寫得非常非常冗長而且超過三十二個中文字限制的案例標題內容",
        ):
            with self.subTest(title=title):
                _, out, rejected = run_validate([dict(GOOD_SCAM, title=title)])
                self.assertEqual(out["rejected"], 1)
                self.assertTrue(
                    any("title" in error for error in rejected[0]["errors"])
                )

    def test_mirror_pair_titles_must_match(self):
        bad_legit = dict(GOOD_LEGIT, title="不同場景的投資邀請")
        _, out, rejected = run_validate([GOOD_SCAM, bad_legit])
        self.assertEqual(out["rejected"], 1)
        self.assertIn("mirror title", " ".join(rejected[0]["errors"]))

    def test_surface_tag_must_be_a_known_weakness_tag_or_null(self):
        _, out, _ = run_validate([GOOD_SCAM, dict(GOOD_LEGIT, surface_tag=None)])
        self.assertEqual(out["valid"], 2)

        _, out, rejected = run_validate(
            [GOOD_SCAM, dict(GOOD_LEGIT, surface_tag="fomo")]
        )
        self.assertEqual(out["rejected"], 1)
        self.assertIn("surface_tag", " ".join(rejected[0]["errors"]))


if __name__ == "__main__":
    unittest.main()
