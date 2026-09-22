#!/usr/bin/env python3
"""verify 探針的遮蔽、基準線、種子讀取與 CLI 閘門；模型一律注入。"""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_leak_probe import make_dump
from test_validate_case_questions import GOOD_QUESTION

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import export_published_seed as exporter  # noqa: E402
import leak_probe as probe  # noqa: E402


def question_copy_data(records):
    """模擬 PostgreSQL COPY 的 JSON 與控制字元跳脫。"""
    lines = []
    for i, record in enumerate(records, 1):
        row = {
            **GOOD_QUESTION,
            "id": i,
            "version": 1,
            "case_id": 1,
            "status": "published",
            **record,
        }
        values = []
        for column in exporter.QUESTION_COLUMNS:
            value = row.get(column)
            if value is None:
                values.append(r"\N")
                continue
            if column == "options":
                value = json.dumps(value, ensure_ascii=False)
            values.append(
                str(value)
                .replace("\\", "\\\\")
                .replace("\n", r"\n")
                .replace("\t", r"\t")
            )
        lines.append("\t".join(values))
    return "\n".join(lines) + "\n"


def make_question_dump():
    parents = make_dump(
        [
            (
                "published-parent",
                "shopping",
                True,
                "不該看到的標題",
                "不該看到的敘事",
                "published",
            ),
            ("draft-parent", "shopping", True, "未發布標題", "未發布敘事", "draft"),
        ]
    )
    rows = [
        {"question_key": "visible-question", "question": "如何確認？含\t定位及\n換行"},
        {"question_key": "draft-question", "status": "draft"},
        {"question_key": "draft-parent-question", "case_id": 2},
    ]
    return (
        parents
        + f"COPY public.game_case_questions ({', '.join(exporter.QUESTION_COLUMNS)}) FROM stdin;\n"
        + question_copy_data(rows)
        + "\\.\n"
    )


class VerifyProbeTests(unittest.TestCase):
    def test_broken_copy_row_is_not_silently_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "seed.sql"
            path.write_text(
                make_question_dump().replace(
                    "visible-question\t", "visible-question\textra\t"
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SystemExit, "COPY 欄位數不符"):
                probe.load_questions_from_dump(path)

    def test_question_jsonl_cannot_run_case_probes(self):
        with patch(
            "sys.argv",
            ["leak_probe.py", "--input", "unused.jsonl", "--probe", "verify,title"],
        ):
            with self.assertRaisesRegex(SystemExit, "混合探針"):
                probe.main()

    def test_prompt_whitelist_hides_case_answer_explanation_and_metadata(self):
        question = dict(
            GOOD_QUESTION,
            title="秘密標題",
            narrative="秘密敘事",
            provenance="秘密出處",
            case={"title": "秘密母案例"},
        )
        with patch.object(
            probe, "_gemini_json", return_value={"selected_key": "B", "reason": "測試"}
        ) as model:
            result = probe.probe_llm(
                question,
                system=probe.VERIFY_SYSTEM,
                field="verify",
                model="fake",
                api_key="fake",
            )
        self.assertEqual(result["predicted_key"], "B")
        self.assertEqual(
            json.loads(model.call_args.args[1]),
            {
                "question": GOOD_QUESTION["question"],
                "options": GOOD_QUESTION["options"],
            },
        )
        self.assertEqual(
            model.call_args.kwargs["response_schema"]["properties"]["selected_key"][
                "enum"
            ],
            ["A", "B", "C"],
        )

    def test_gemini_transport_uses_verification_schema_without_network(self):
        payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {"selected_key": "A", "reason": "測試"}
                                )
                            }
                        ]
                    }
                }
            ]
        }
        with patch.object(
            probe, "fetch_url", return_value={"ok": True, "body": json.dumps(payload)}
        ) as fetch:
            result = probe.probe_verify(GOOD_QUESTION, model="fake", api_key="fake")
        self.assertEqual(result["predicted_key"], "A")
        body = fetch.call_args.kwargs["json_body"]
        self.assertIn(
            "selected_key", body["generationConfig"]["responseSchema"]["properties"]
        )
        self.assertEqual(
            set(json.loads(body["contents"][0]["parts"][0]["text"])),
            {"question", "options"},
        )

    def test_invalid_answer_and_api_error_are_measurement_errors(self):
        for response in ({"selected_key": "Z"}, {"__error__": "HTTP 429"}, {}):
            with patch.object(probe, "_gemini_json", return_value=response):
                result = probe.probe_verify(GOOD_QUESTION, model="fake", api_key="fake")
            self.assertTrue(result["error"])
            self.assertIsNone(
                probe.verify_score([dict(GOOD_QUESTION, **result)])["leak_rate"]
            )

    def test_mixed_option_counts_and_errors_have_correct_baseline(self):
        three = dict(GOOD_QUESTION, predicted_key="A")
        four = dict(
            GOOD_QUESTION,
            predicted_key="B",
            options=GOOD_QUESTION["options"] + [{"key": "D", "text": "第四選項"}],
        )
        failed = dict(GOOD_QUESTION, predicted_key=None, error="失敗")
        score = probe.verify_score([three, four, failed])
        self.assertEqual(score["baseline"], round((1 / 3 + 1 / 4) / 2, 4))
        self.assertEqual(
            (score["leak_rate"], score["scored"], score["errors"]), (0.5, 2, 1)
        )

    def test_dump_filters_parent_and_child_and_decodes_copy(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "seed.sql"
            path.write_text(make_question_dump(), encoding="utf-8")
            rows = probe.load_questions_from_dump(path)
            self.assertEqual([r["question_key"] for r in rows], ["visible-question"])
            self.assertEqual(rows[0]["question"], "如何確認？含\t定位及\n換行")
            self.assertEqual(rows[0]["options"], GOOD_QUESTION["options"])
            self.assertEqual(len(probe.load_questions_from_dump(path, False)), 3)

    def test_dump_ignores_superseded_versions(self):
        """改版後的舊題不能進量測集合——後端根本不會把它發出去。

        關鍵在順序:必須先算出「所有狀態」裡的最大 version,再篩發布狀態。
        反過來先濾 draft 的話,v2=draft 會消失、v1=published 變成最大版本,
        於是量到一題實際上發不出來的舊題,還會稀釋掉新版的洩題率。
        """
        rows = [
            # v1 published、v2 draft → 整個 question_key 都不該被量到
            {"question_key": "superseded", "version": 1, "id": 1},
            {"question_key": "superseded", "version": 2, "id": 2, "status": "draft"},
            # v1 published、v2 published → 只量 v2
            {"question_key": "revised", "version": 1, "id": 3},
            {"question_key": "revised", "version": 2, "id": 4},
        ]
        dump = (
            make_dump(
                [
                    (
                        "published-parent",
                        "shopping",
                        True,
                        "標題",
                        "敘事",
                        "published",
                    )
                ]
            )
            + f"COPY public.game_case_questions ({', '.join(exporter.QUESTION_COLUMNS)}) FROM stdin;\n"
            + question_copy_data(rows)
            + "\\.\n"
        )
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "seed.sql"
            path.write_text(dump, encoding="utf-8")
            loaded = probe.load_questions_from_dump(path)
        self.assertEqual(
            [(q["question_key"], q["version"]) for q in loaded], [("revised", 2)]
        )

    def test_cli_jsonl_and_dump_fail_over_and_report_baseline(self):
        for source in ("--input", "--from-dump"):
            for selected, expected in (("A", 1), ("B", 0)):
                with (
                    self.subTest(source=source, selected=selected),
                    tempfile.TemporaryDirectory() as td,
                ):
                    path, report = Path(td) / "input", Path(td) / "report.json"
                    path.write_text(
                        json.dumps(GOOD_QUESTION) + "\n"
                        if source == "--input"
                        else make_question_dump(),
                        encoding="utf-8",
                    )
                    output = io.StringIO()
                    with (
                        patch.object(
                            probe,
                            "_gemini_json",
                            return_value={"selected_key": selected, "reason": "測試"},
                        ),
                        patch.dict("os.environ", {"GOOGLE_API_KEY": "fake"}),
                        patch(
                            "sys.argv",
                            [
                                "leak_probe.py",
                                source,
                                str(path),
                                "--probe",
                                "verify",
                                "--fail-over",
                                "0.5",
                                "--json-output",
                                str(report),
                                "--detail",
                                "1",
                            ],
                        ),
                        contextlib.redirect_stdout(output),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        code = probe.main()
                    self.assertEqual(code, expected)
                    summary = json.loads(output.getvalue().strip().splitlines()[-1])[
                        "verify"
                    ]
                    self.assertEqual(summary["baseline"], 0.3333)
                    self.assertEqual(summary["leak_rate"], float(selected == "A"))
                    self.assertIn("33.3%", output.getvalue())
                    self.assertIn("實測命中率", output.getvalue())
                    self.assertEqual(
                        json.loads(report.read_text())["summary"]["verify"], summary
                    )

    def test_cli_all_model_errors_fails_instead_of_passing_gate(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "questions.jsonl"
            path.write_text(json.dumps(GOOD_QUESTION), encoding="utf-8")
            with (
                patch.object(
                    probe, "_gemini_json", return_value={"__error__": "HTTP 429"}
                ),
                patch.dict("os.environ", {"GOOGLE_API_KEY": "fake"}),
                patch(
                    "sys.argv",
                    [
                        "leak_probe.py",
                        "--input",
                        str(path),
                        "--probe",
                        "verify",
                        "--fail-over",
                        "0.5",
                    ],
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(probe.main(), 1)
