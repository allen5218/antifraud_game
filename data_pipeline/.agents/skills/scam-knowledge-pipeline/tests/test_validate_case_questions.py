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

    def test_player_text_writing_rules(self):
        cases = {
            "全形標點": dict(GOOD_QUESTION, explanation="聯絡方式要自己找,才不會再接到同一方。"),
            "破折號": dict(GOOD_QUESTION, question="接下來——應該如何確認？"),
            "改編自：": dict(GOOD_QUESTION, provenance="金管會公告的合法業者名單"),
        }
        for message, record in cases.items():
            with self.subTest(message=message):
                self.rejected([record], message)
        self.assertEqual(
            validator.validate_rows(
                [(1, dict(GOOD_QUESTION, provenance="依據：金管會合法業者名單"))]
            )[1],
            [],
        )

    def test_option_must_not_carry_the_reason(self):
        """理由只寫在正解時,不看題目也知道選它。"""
        bad = copy.deepcopy(GOOD_QUESTION)
        bad["options"][0]["text"] = "打原本的客服專線，以免被轉接"
        self.rejected([bad], "選項只寫做法")

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

    def test_option_key_with_trailing_newline_rejected(self):
        """`^[A-D]$` 在 Python re 下也會匹配結尾換行,所以 "A\n" 過得了 pattern。

        真的放行的話,前端送 "A" 對不上存進去的 "A\n",送 "A\n" 又會被 API 的
        max_length=1 擋成 422——這題等於永遠答不對。schema 必須用 enum。
        """
        bad = copy.deepcopy(GOOD_QUESTION)
        bad["options"][0]["key"] = "A\n"
        bad["correct_key"] = "A\n"
        self.rejected([bad], "is not one of")

    def _cluster_batch(self, correct_keys):
        """受測叢集 + 一組合格的填充叢集。

        叢集規則有批次下限（少於 MIN_BATCH_FOR_CLUSTER_RULES 筆就不套，
        因為分布無從判斷），所以要補足數量才驗得到受測的那一組。
        """
        opts = [
            {"key": "A", "text": "從原平台官方入口查帳戶狀態"},
            {"key": "B", "text": "掛斷後自行改撥卡片背面客服"},
            {"key": "C", "text": "從主管機關官方名單查資格"},
        ]
        # 三個都含查證字樣,免得先被「正解不得是唯一含查證字樣的選項」擋下,
        # 那樣就驗不到叢集規則了。
        filler_opts = [
            {"key": "A", "text": "從官方入口查看實物的規格說明"},
            {"key": "B", "text": "送獨立機構鑑定並取得官方報告"},
            {"key": "C", "text": "向官方發證單位查詢憑證真偽"},
        ]
        batch = [
            dict(
                GOOD_QUESTION,
                question_key=f"verify-cluster-{i:03d}",
                case_key=f"shopping-scam-{i:03d}",
                options=copy.deepcopy(opts),
                correct_key=key,
            )
            for i, key in enumerate(correct_keys, 1)
        ]
        batch += [
            dict(
                GOOD_QUESTION,
                question_key=f"verify-filler-{i:03d}",
                case_key=f"fake-sale-scam-{i:03d}",
                options=copy.deepcopy(filler_opts),
                correct_key=key,
            )
            # 四筆,正解 A/B/C/A —— A 佔 2/4 未過半,填充叢集自己是合格的。
            for i, key in enumerate("ABCA", 1)
        ]
        return batch

    def test_cluster_used_in_too_few_questions_rejected(self):
        """選項組只用在一兩題時,正解沒辦法在組內分散。"""
        self.rejected(self._cluster_batch(["A", "B"]), "至少要橫跨 3 題")

    def test_cluster_with_dominant_correct_option_rejected(self):
        """同一個選項在組內當正解超過一半 → 固定挑它就會贏。"""
        self.rejected(self._cluster_batch(["A", "A", "A", "B"]), "超過一半")

    def test_balanced_cluster_passes(self):
        valid, rejected = validator.validate_rows(
            list(enumerate(self._cluster_batch(["A", "B", "C"]), 1))
        )
        self.assertEqual(len(valid), 7)
        self.assertFalse(rejected)

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
