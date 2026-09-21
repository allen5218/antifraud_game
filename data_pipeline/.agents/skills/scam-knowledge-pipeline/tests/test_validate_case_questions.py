#!/usr/bin/env python3
"""查證題八條語意規則與草稿 schema 的正反例。"""

import copy
import json
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import validate_case_questions as validator  # noqa: E402

GOOD_QUESTION = {
    "question_key": "verify-test-001",
    "case_key": "shopping-scam-001",
    "question_kind": "next_action",
    "question": "接下來應該如何確認？",
    "options": [
        {"key": "A", "text": "自己打原本的客服專線詢問"},
        {"key": "B", "text": "撥打對方提供的官方專線"},
        {"key": "C", "text": "請群組管理員代為確認內容"},
    ],
    "correct_key": "A",
    "explanation": "聯絡方式須獨立取得，才不會再接到同一方提供的窗口。",
    "weakness_tag": "authority",
    "difficulty": 2,
}


class QuestionValidationTests(unittest.TestCase):
    def rejected(self, records, message):
        valid, rejected = validator.validate_rows(list(enumerate(records, 1)))
        self.assertTrue(rejected)
        self.assertIn(message, " ".join(e for r in rejected for e in r["errors"]))
        return valid, rejected

    def test_good_pair_and_diversity_boundary_pass(self):
        second = dict(
            GOOD_QUESTION,
            question_key="verify-test-002",
            question_kind="evidence_scope",
        )
        valid, rejected = validator.validate_rows([(1, GOOD_QUESTION), (2, second)])
        self.assertEqual((len(valid), rejected), (2, []))

    def test_correct_key_must_exist(self):
        self.rejected([dict(GOOD_QUESTION, correct_key="D")], "correct_key 必須出現")

    def test_duplicate_option_keys_rejected(self):
        bad = copy.deepcopy(GOOD_QUESTION)
        bad["options"][2]["key"] = "B"
        self.rejected([bad], "key 不得重複")

    def test_length_ratio_rejected_and_exactly_two_passes(self):
        bad = copy.deepcopy(GOOD_QUESTION)
        bad["options"][2]["text"] = "先問朋友"
        self.rejected([bad], "2 倍")
        bad["options"] = [
            {"key": "A", "text": "查證來源再作決定"},
            {"key": "B", "text": "官方專線"},
            {"key": "C", "text": "先問朋友"},
        ]
        self.assertEqual(validator.validate_rows([(1, bad)])[1], [])

    def test_correct_only_verification_words_rejected(self):
        bad = copy.deepcopy(GOOD_QUESTION)
        bad["options"][1]["text"] = "撥打對方提供的聯絡號碼"
        self.rejected([bad], "唯一含查證類字樣")

    def test_required_verification_words(self):
        for word in (
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
        ):
            with self.subTest(word=word):
                bad = copy.deepcopy(GOOD_QUESTION)
                bad["options"] = [
                    {"key": "A", "text": word + "後再確認內容"},
                    {"key": "B", "text": "請對方重新解釋內容"},
                    {"key": "C", "text": "請朋友重新解釋內容"},
                ]
                self.rejected([bad], "唯一含查證類字樣")

    def test_duplicate_key_and_default_version_rejected(self):
        duplicate = dict(GOOD_QUESTION, version=1, case_key="another-case")
        self.rejected([GOOD_QUESTION, duplicate], "duplicate question_key/version")
        distinct = dict(duplicate, version=2)
        self.assertEqual(
            validator.validate_rows([(1, GOOD_QUESTION), (2, distinct)])[1], []
        )

    def test_pii_in_all_player_text_fields_rejected(self):
        for field in ("question", "explanation", 0, 1, 2):
            for name, value in (
                ("phone", "0912-345-678"),
                ("landline", "02-2345-6789"),
                ("national_id", "A123456789"),
                ("account_number", "123456789012"),
                ("url", "https://test.invalid"),
                ("email", "a@test.invalid"),
            ):
                with self.subTest(field=field, name=name):
                    bad = copy.deepcopy(GOOD_QUESTION)
                    if isinstance(field, int):
                        bad["options"][field]["text"] = value
                    else:
                        bad[field] = value
                    self.rejected([bad], f"possible {name}")

    def test_explanation_cannot_copy_correct_text(self):
        self.rejected(
            [dict(GOOD_QUESTION, explanation=GOOD_QUESTION["options"][0]["text"])],
            "完全照抄",
        )

    def test_max_two_questions_and_batch_concentration_rejected(self):
        records = [dict(GOOD_QUESTION, question_key=f"verify-{i}") for i in range(3)]
        valid, rejected = self.rejected(records, "最多兩題")
        self.assertEqual(len(valid), 0)
        self.assertTrue(
            all(any("總數 3 的一半" in e for e in r["errors"]) for r in rejected)
        )

    def test_duplicate_kind_rejected_even_when_batch_is_distributed(self):
        records = [GOOD_QUESTION, dict(GOOD_QUESTION, question_key="verify-second")]
        records.append(
            dict(GOOD_QUESTION, question_key="verify-third", case_key="second-case")
        )
        self.rejected(records, "每種 question_kind 最多一題")

    def test_schema_bad_shapes_are_rejected_without_crashing(self):
        for rec in (
            None,
            [],
            7,
            {"question": "不足欄位"},
            dict(GOOD_QUESTION, options=None),
            dict(GOOD_QUESTION, version=0),
            dict(GOOD_QUESTION, weakness_tag="fomo"),
        ):
            with self.subTest(rec=rec):
                valid, rejected = validator.validate_rows([(1, rec)])
                self.assertEqual((len(valid), len(rejected)), (0, 1))

    def test_schema_tags_match_backend_single_source(self):
        repo = SKILL.parents[3]
        tags = runpy.run_path(str(repo / "backend/app/core/weakness.py"))[
            "WEAKNESS_TAGS"
        ]
        self.assertEqual(
            set(
                validator.load_schema_validator().schema["properties"]["weakness_tag"][
                    "enum"
                ]
            ),
            tags,
        )

    def test_cli_outputs_json_counts_and_reject_line_numbers(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inp, valid, rejected = [
                root / name for name in ("input.jsonl", "valid.jsonl", "rejected.jsonl")
            ]
            inp.write_text(
                json.dumps(GOOD_QUESTION)
                + "\n{broken\n"
                + json.dumps(
                    dict(
                        GOOD_QUESTION,
                        case_key="other-case",
                        question_key="bad-question",
                        correct_key="D",
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SKILL / "scripts/validate_case_questions.py"),
                    "--input",
                    str(inp),
                    "--valid-output",
                    str(valid),
                    "--reject-output",
                    str(rejected),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 1, proc.stderr)
            self.assertEqual(json.loads(proc.stdout), {"valid": 1, "rejected": 2})
            self.assertEqual(json.loads(valid.read_text()), GOOD_QUESTION)
            self.assertEqual(
                [
                    json.loads(line)["line"]
                    for line in rejected.read_text().splitlines()
                ],
                [2, 3],
            )


if __name__ == "__main__":
    unittest.main()
