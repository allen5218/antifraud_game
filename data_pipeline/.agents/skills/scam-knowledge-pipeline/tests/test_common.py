#!/usr/bin/env python3
"""共用資料庫連線參數的回歸測試。"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import common  # noqa: E402


class DatabaseArgsTests(unittest.TestCase):
    def test_message_sample_is_a_supported_content_kind(self):
        self.assertIn("message_sample", common.CONTENT_KINDS)

    def test_clean_text_removes_html_and_preserves_block_breaks(self):
        raw = (
            "<p>第一段&nbsp;內容</p><div>第二段<br>換行</div><script>不應保留</script>"
        )

        self.assertEqual(common.clean_text(raw), "第一段 內容\n第二段\n換行")

    def test_missing_database_url_fails_with_connection_guidance(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit) as caught:
                common.db_args()

        message = str(caught.exception)
        self.assertIn("DATABASE_URL", message)
        self.assertIn("--env-file", message)

    def test_psql_bin_supports_command_with_arguments(self):
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql://db/example",
                "PSQL_BIN": "docker exec -i pg psql",
            },
            clear=True,
        ):
            self.assertEqual(
                common.db_args(),
                [
                    "docker",
                    "exec",
                    "-i",
                    "pg",
                    "psql",
                    "-v",
                    "ON_ERROR_STOP=1",
                    "-X",
                    "postgresql://db/example",
                ],
            )

    def test_pg_dump_bin_supports_command_with_arguments(self):
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql://db/example",
                "PG_DUMP_BIN": "docker exec -i pg pg_dump",
            },
            clear=True,
        ):
            self.assertEqual(
                common.pg_dump_args(),
                [
                    "docker",
                    "exec",
                    "-i",
                    "pg",
                    "pg_dump",
                    "postgresql://db/example",
                ],
            )

    def test_run_psql_file_pipes_contents_through_stdin(self):
        with tempfile.TemporaryDirectory() as td:
            sql_path = Path(td) / "input.sql"
            sql_path.write_text("SELECT 1;\n", encoding="utf-8")
            with patch.dict(
                os.environ, {"DATABASE_URL": "postgresql://db/example"}, clear=True
            ):
                with patch("common.subprocess.run") as run:
                    run.return_value.returncode = 0
                    run.return_value.stdout = "ok"
                    run.return_value.stderr = ""
                    result = common.run_psql_file(sql_path)

            self.assertEqual(result, "ok")
            args, kwargs = run.call_args
            self.assertNotIn("-f", args[0])
            self.assertEqual(kwargs["input"], "SELECT 1;\n")

    def test_copy_from_rows_sql_uses_inline_stdin_instead_of_local_path(self):
        sql = common.copy_from_rows_sql(
            "tmp_rows",
            ["id", "text"],
            [{"id": "1", "text": "含有\t定位字元"}],
        )
        self.assertIn("COPY tmp_rows (id, text) FROM STDIN", sql)
        self.assertIn("\\.\n", sql)
        self.assertNotIn("\\copy", sql)


if __name__ == "__main__":
    unittest.main()
