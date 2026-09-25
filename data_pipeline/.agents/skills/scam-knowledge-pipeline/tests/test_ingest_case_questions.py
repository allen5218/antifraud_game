#!/usr/bin/env python3
"""查證題入庫使用注入的 SQL 執行器，不連線真實資料庫。"""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_validate_case_questions import GOOD_QUESTION

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import ingest_game_cases as ingest  # noqa: E402


class IngestQuestionTests(unittest.TestCase):
    def run_ingest(
        self, records, *, apply=False, missing=False, status="", written="1", table=True
    ):
        def scalar(sql):
            if "to_regclass" in sql:
                return "game_case_questions" if table else ""
            if "SELECT id FROM game_cases" in sql:
                return "" if missing else "17"
            if "SELECT status FROM game_case_questions" in sql:
                return status
            if "INSERT INTO game_case_questions" in sql:
                return written
            if "FROM documents" in sql:
                return "0"
            self.fail(f"非預期 SQL: {sql}")

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "questions.jsonl"
            path.write_text(
                "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
                encoding="utf-8",
            )
            argv = ["ingest_game_cases.py", "--kind", "questions", "--input", str(path)]
            if apply:
                argv.append("--apply")
            output = io.StringIO()
            with (
                patch.object(ingest, "load_env"),
                patch.object(ingest, "psql_scalar", side_effect=scalar) as sql,
                patch.object(ingest, "ensure_game_cases_schema") as schema,
                patch.object(ingest, "run_psql") as run_sql,
                patch("sys.argv", argv),
                contextlib.redirect_stdout(output),
            ):
                code = ingest.main()
            run_sql.assert_not_called()
            return (
                code,
                [json.loads(line) for line in output.getvalue().splitlines()],
                [call.args[0] for call in sql.call_args_list],
                schema.call_count,
            )

    def test_dry_run_reads_parent_but_never_mutates(self):
        code, reports, queries, ddl = self.run_ingest([GOOD_QUESTION], table=False)
        self.assertEqual((code, ddl), (0, 0))
        self.assertEqual(reports[-1]["rejected"], [])
        self.assertTrue(all(sql.startswith("SELECT") for sql in queries))

    def test_missing_parent_is_reported_and_apply_aborts(self):
        code, reports, queries, ddl = self.run_ingest(
            [GOOD_QUESTION], apply=True, missing=True
        )
        self.assertEqual((code, ddl), (1, 0))
        self.assertIn("找不到母案例", reports[-1]["rejected"][0]["errors"][0])
        self.assertTrue(all("INSERT" not in sql for sql in queries))

    def test_apply_upserts_default_version_and_all_fields_as_draft(self):
        code, reports, queries, ddl = self.run_ingest([GOOD_QUESTION], apply=True)
        self.assertEqual((code, ddl, reports[-1]["ingested"]), (0, 1, 1))
        sql = queries[-1]
        self.assertIn("ON CONFLICT (question_key, version)", sql)
        self.assertIn("'verify-test-001', 1, 17", sql)
        self.assertIn("ARRAY[]::bigint[], NULL, 'draft'", sql)
        self.assertIn("status = 'draft'", sql)
        for field in (
            "case_id",
            "question_kind",
            "question",
            "options",
            "correct_key",
            "explanation",
            "weakness_tag",
            "difficulty",
            "source_document_ids",
            "provenance",
        ):
            self.assertIn(f"{field} = EXCLUDED.{field}", sql)

    def test_version_provenance_and_quotes_are_preserved(self):
        record = dict(GOOD_QUESTION, version=3, provenance="改編自：測試 '來源'")
        code, _, queries, _ = self.run_ingest([record], apply=True)
        self.assertEqual(code, 0)
        self.assertIn("'verify-test-001', 3, 17", queries[-1])
        self.assertIn("改編自：測試 ''來源''", queries[-1])

    def test_non_draft_conflict_is_not_overwritten(self):
        for status in ("reviewed", "published", "archived"):
            with self.subTest(status=status):
                code, reports, queries, ddl = self.run_ingest(
                    [GOOD_QUESTION], apply=True, status=status
                )
                self.assertEqual((code, ddl), (1, 0))
                self.assertIn(status, reports[-1]["rejected"][0]["errors"][0])
                self.assertTrue(all("INSERT" not in sql for sql in queries))

    def test_concurrent_status_change_is_reported_as_rejection(self):
        code, reports, _, _ = self.run_ingest([GOOD_QUESTION], apply=True, written="0")
        self.assertEqual(code, 1)
        self.assertEqual(reports[-1]["ingested"], 0)
        self.assertIn("未寫入", reports[-1]["rejected"][0]["errors"][0])

    def test_invalid_question_aborts_before_db_access(self):
        code, reports, queries, ddl = self.run_ingest(
            [dict(GOOD_QUESTION, correct_key="D")], apply=True
        )
        self.assertEqual((code, queries, ddl), (1, [], 0))
        self.assertTrue(reports[-1]["rejected"])

    def test_missing_source_is_rejected(self):
        code, reports, _, ddl = self.run_ingest(
            [dict(GOOD_QUESTION, source_document_ids=[99])], apply=True
        )
        self.assertEqual((code, ddl), (1, 0))
        self.assertIn("document: 99", reports[-1]["rejected"][0]["errors"][0])
