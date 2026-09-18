#!/usr/bin/env python3
"""leak_probe.py 的回歸測試——只涵蓋免 API 的部分(COPY 解析、lexical 探針、計分、CI 閘門)。"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import leak_probe  # noqa: E402

COPY_HEADER = (
    "COPY public.game_cases (id, case_key, fraud_type, is_scam, title, narrative, "
    "red_flags, difficulty, source_document_ids, provenance, mirror_of, status, "
    "review_notes, created_at, published_at) FROM stdin;"
)

# 詐騙題的典型回顧式結尾:結局已揭曉、語氣懊悔
SCAM_TAIL = "我依指示匯了款,對方隨即封鎖我。事後我才知道,整個都是圈套。"
# 正當題的典型結尾:「正因為…我才…」把答案直接寫進句式
LEGIT_TAIL = "全程都在平台內完成。正因為交易紀錄可查,我才放心付款。"
# 沒有結局的當下視角敘述——這是重寫後應該長的樣子
NEUTRAL = "對方說名額只剩三個,要我今天之內把訂金匯到指定帳戶,匯完就幫我保留。"


def make_dump(rows):
    """組出一個最小可解析的 pg_dump COPY 區塊。"""
    lines = ["-- fake dump", "", COPY_HEADER]
    for i, row in enumerate(rows, 1):
        key, ftype, is_scam, title, narrative, status, *rest = row
        red_flags = rest[0] if rest else []
        lines.append(
            "\t".join(
                [
                    str(i),
                    key,
                    ftype,
                    "t" if is_scam else "f",
                    title,
                    narrative,
                    json.dumps(red_flags, ensure_ascii=False),
                    "2",
                    "{}",
                    "prov",
                    r"\N",
                    status,
                    r"\N",
                    "2026-07-02 16:21:25+00",
                    "2026-07-03 05:31:15+00",
                ]
            )
        )
    lines.append("\\.")
    return "\n".join(lines) + "\n"


class TestDumpParsing(unittest.TestCase):
    def test_parses_rows_and_filters_drafts(self):
        dump = make_dump(
            [
                ("a-scam-001", "shopping", True, "標題A", SCAM_TAIL, "published"),
                ("a-legit-001", "shopping", False, "標題B", LEGIT_TAIL, "published"),
                ("a-scam-002", "romance", True, "標題C", SCAM_TAIL, "draft"),
            ]
        )
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "dump.sql"
            path.write_text(dump, encoding="utf-8")

            published = leak_probe.load_from_dump(str(path))
            self.assertEqual(
                [c["case_key"] for c in published], ["a-scam-001", "a-legit-001"]
            )
            self.assertIs(published[0]["is_scam"], True)
            self.assertIs(published[1]["is_scam"], False)
            self.assertEqual(published[0]["narrative"], SCAM_TAIL)
            self.assertEqual(published[0]["red_flags"], [])

            self.assertEqual(
                len(leak_probe.load_from_dump(str(path), published_only=False)), 3
            )

    def test_missing_copy_block_is_fatal(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "dump.sql"
            path.write_text("-- nothing here\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                leak_probe.load_from_dump(str(path))

    def test_unescape_copy(self):
        self.assertIsNone(leak_probe._unescape_copy(r"\N"))
        self.assertEqual(leak_probe._unescape_copy(r"a\tb\nc"), "a\tb\nc")
        self.assertEqual(leak_probe._unescape_copy(r"back\\slash"), "back\\slash")


class TestLexicalProbe(unittest.TestCase):
    def test_detects_retrospective_scam_ending(self):
        result = leak_probe.probe_lexical({"narrative": SCAM_TAIL})
        self.assertIs(result["predicted_is_scam"], True)
        self.assertTrue(result["giveaway"])

    def test_detects_reassuring_legit_ending(self):
        result = leak_probe.probe_lexical({"narrative": LEGIT_TAIL})
        self.assertIs(result["predicted_is_scam"], False)
        self.assertIn("正因為", result["giveaway"])

    def test_abstains_on_unresolved_narrative(self):
        """重寫成當下視角、結局未揭曉後,規則探針應該無法判定。"""
        self.assertIsNone(
            leak_probe.probe_lexical({"narrative": NEUTRAL})["predicted_is_scam"]
        )


class TestMatchProbe(unittest.TestCase):
    CASES = [
        {
            "case_key": "s1",
            "fraud_type": "investment",
            "is_scam": True,
            "red_flags": [
                {
                    "tag": "social_proof",
                    "text": "直播留言營造搶購的從眾氣氛",
                },
                {
                    "tag": "authority",
                    "text": "自稱銀行專員並用感情話術要求付款",
                },
            ],
        },
        {
            "case_key": "l1",
            "fraud_type": "investment",
            "is_scam": False,
            "red_flags": [{"tag": None, "text": "正當訊號不列入 match"}],
        },
    ]

    def test_reports_own_and_other_tag_tell_words_per_sentence(self):
        rows = leak_probe.probe_match(self.CASES)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["flag_index"], 1)
        self.assertEqual(rows[0]["own_hits"], ["從眾"])
        self.assertEqual(rows[1]["other_hits"], {"trust_building": ["感情"]})

        summary = leak_probe.match_score(rows)
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["own_leaks"], 1)
        self.assertEqual(summary["other_leaks"], 1)
        self.assertEqual(summary["leak_rate"], 0.5)


class TestTagBalance(unittest.TestCase):
    def test_counts_occurrences_type_coverage_and_tactics_qualified_cases(self):
        cases = [
            {
                "case_key": "s1",
                "fraud_type": "investment",
                "is_scam": True,
                "red_flags": [
                    {"tag": "authority", "text": "a"},
                    {"tag": "authority", "text": "b"},
                    {"tag": "greed", "text": "c"},
                ],
            },
            {
                "case_key": "s2",
                "fraud_type": "romance",
                "is_scam": True,
                "red_flags": [{"tag": "authority", "text": "d"}],
            },
        ]
        balance = leak_probe.tag_balance(cases)
        self.assertEqual(balance["tags"]["authority"]["count"], 3)
        self.assertEqual(balance["tags"]["authority"]["fraud_type_count"], 2)
        self.assertEqual(balance["tactics_qualified"], 1)
        self.assertEqual(balance["scam_cases"], 2)

    def test_tail_scope_only_reads_the_ending(self):
        narrative = LEGIT_TAIL + "x" * 400
        self.assertIs(
            leak_probe.probe_lexical({"narrative": narrative}, "tail")[
                "predicted_is_scam"
            ],
            None,
        )
        self.assertIs(
            leak_probe.probe_lexical({"narrative": narrative}, "full")[
                "predicted_is_scam"
            ],
            False,
        )


class TestScoring(unittest.TestCase):
    def test_undecided_counts_as_coin_flip(self):
        rows = [
            {"is_scam": True, "predicted_is_scam": True},
            {"is_scam": False, "predicted_is_scam": False},
            {"is_scam": True, "predicted_is_scam": None},
            {"is_scam": False, "predicted_is_scam": True},
        ]
        s = leak_probe.score(rows)
        self.assertEqual(s["correct"], 2)
        self.assertEqual(s["wrong"], 1)
        self.assertEqual(s["undecided"], 1)
        self.assertAlmostEqual(s["leak_rate"], (2 + 0.5) / 4)
        self.assertAlmostEqual(s["accuracy_when_decided"], 2 / 3, places=3)

    def test_perfectly_clean_bank_scores_fifty_percent(self):
        """全部無法判定 = 50%,也就是「沒洩題」的目標值。"""
        rows = [{"is_scam": i % 2 == 0, "predicted_is_scam": None} for i in range(10)]
        self.assertEqual(leak_probe.score(rows)["leak_rate"], 0.5)

    def test_api_errors_are_excluded_from_the_metric(self):
        """呼叫失敗是量測故障,不能當成棄權去稀釋洩題率。"""
        rows = [
            {"is_scam": True, "predicted_is_scam": True},
            {"is_scam": False, "predicted_is_scam": False},
            {"is_scam": True, "predicted_is_scam": None, "error": "HTTP 429"},
            {"is_scam": False, "predicted_is_scam": None, "error": "HTTP 429"},
        ]
        s = leak_probe.score(rows)
        self.assertEqual(s["errors"], 2)
        self.assertEqual(s["scored"], 2)
        self.assertEqual(s["leak_rate"], 1.0)  # 而非把失敗算成 0.5 後的 0.75

    def test_all_errors_yields_no_metric_instead_of_a_fake_number(self):
        rows = [{"is_scam": True, "predicted_is_scam": None, "error": "boom"}]
        self.assertIsNone(leak_probe.score(rows)["leak_rate"])

    def test_pattern_precision_flags_noisy_rules(self):
        rows = [
            {
                "is_scam": True,
                "hits": {"scam": [{"pattern": "好規則", "matched": "x"}], "legit": []},
            },
            {
                "is_scam": False,
                "hits": {
                    "scam": [{"pattern": "噪音規則", "matched": "y"}],
                    "legit": [],
                },
            },
            {
                "is_scam": True,
                "hits": {
                    "scam": [{"pattern": "噪音規則", "matched": "y"}],
                    "legit": [],
                },
            },
        ]
        stats = leak_probe.pattern_stats(rows)
        self.assertEqual(stats["好規則"]["precision"], 1.0)
        self.assertEqual(stats["噪音規則"]["precision"], 0.5)


class TestLenientParse(unittest.TestCase):
    def test_strict_json_is_not_flagged_lenient(self):
        parsed, lenient = leak_probe._lenient_parse(
            '{"verdict": "resolved_scam", "giveaway": "圈套"}'
        )
        self.assertEqual(parsed["verdict"], "resolved_scam")
        self.assertFalse(lenient)

    def test_recovers_verdict_from_malformed_json(self):
        """模型偶爾在 reason 裡放未跳脫引號——別為了一個引號丟掉整題。"""
        bad = '{"verdict": "resolved_legit", "giveaway": "正因為", "reason": "他說"很安心"啊"}'
        parsed, lenient = leak_probe._lenient_parse(bad)
        self.assertEqual(parsed["verdict"], "resolved_legit")
        self.assertEqual(parsed["giveaway"], "正因為")
        self.assertTrue(lenient)

    def test_returns_none_when_no_verdict_present(self):
        parsed, _ = leak_probe._lenient_parse("模型今天不想回答")
        self.assertIsNone(parsed)


class TestCli(unittest.TestCase):
    def run_cli(self, rows, *extra):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "dump.sql"
            path.write_text(make_dump(rows), encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(SKILL / "scripts" / "leak_probe.py"),
                    "--from-dump",
                    str(path),
                    *extra,
                ],
                capture_output=True,
                text=True,
                cwd=str(SKILL / "scripts"),
            )

    LEAKY = [
        ("s1", "shopping", True, "被騙的一天", SCAM_TAIL, "published"),
        ("l1", "shopping", False, "安心的一天", LEGIT_TAIL, "published"),
    ]
    CLEAN = [
        ("s1", "shopping", True, "一則訊息", NEUTRAL, "published"),
        ("l1", "shopping", False, "另一則訊息", NEUTRAL, "published"),
    ]

    MATCH = [
        (
            "s1",
            "shopping",
            True,
            "一則訊息",
            NEUTRAL,
            "published",
            [
                {"tag": "social_proof", "text": "直播留言營造搶購的從眾氣氛"},
                {"tag": "authority", "text": "自稱銀行專員並用感情話術要求付款"},
            ],
        ),
        ("l1", "shopping", False, "另一則訊息", NEUTRAL, "published", []),
    ]

    def test_reports_leak_rate_as_json(self):
        proc = self.run_cli(self.LEAKY)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        summary = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertEqual(summary["lexical"]["leak_rate"], 1.0)

    def test_fail_over_gate_blocks_leaky_bank(self):
        proc = self.run_cli(self.LEAKY, "--fail-over", "0.75")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("超過門檻", proc.stderr)

    def test_fail_over_gate_passes_clean_bank(self):
        proc = self.run_cli(self.CLEAN, "--fail-over", "0.75")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        summary = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertEqual(summary["lexical"]["leak_rate"], 0.5)

    def test_llm_probe_requires_api_key(self):
        proc = self.run_cli(
            self.CLEAN, "--probe", "genre", "--api-key-env", "DEFINITELY_UNSET_KEY"
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("DEFINITELY_UNSET_KEY", proc.stdout + proc.stderr)

    def test_match_probe_reports_own_tag_rate_and_fail_over_uses_it(self):
        proc = self.run_cli(self.MATCH, "--probe", "match", "--fail-over", "0.4")
        self.assertEqual(proc.returncode, 1)
        summary = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertEqual(summary["match"]["leak_rate"], 0.5)
        self.assertIn("自己 tag 洩題句數 / scam red_flag 總句數", proc.stdout)

    def test_match_fail_over_handles_input_without_scam_flags(self):
        only_legit = [("l1", "shopping", False, "另一則訊息", NEUTRAL, "published", [])]
        proc = self.run_cli(only_legit, "--probe", "match", "--fail-over", "0.75")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        summary = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertIsNone(summary["match"]["leak_rate"])

    def test_tag_balance_minimum_gate(self):
        failed = self.run_cli(
            self.MATCH, "--probe", "lexical", "--tag-balance", "--min-tag-count", "2"
        )
        self.assertEqual(failed.returncode, 1)
        self.assertIn("低於門檻", failed.stderr)

        passed = self.run_cli(
            self.MATCH, "--probe", "lexical", "--tag-balance", "--min-tag-count", "0"
        )
        self.assertEqual(passed.returncode, 0, passed.stderr)
        summary = json.loads(passed.stdout.strip().splitlines()[-1])
        self.assertEqual(summary["tag_balance"]["tactics_qualified"], 1)


if __name__ == "__main__":
    unittest.main()
