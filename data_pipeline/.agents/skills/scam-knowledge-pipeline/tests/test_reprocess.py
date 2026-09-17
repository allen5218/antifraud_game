#!/usr/bin/env python3
"""既有文件重處理必須可預覽，且以 staging_id 原地更新。"""

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
NORMALIZE = SKILL / "scripts" / "normalize_jsonb.py"


class ReprocessTests(unittest.TestCase):
    def test_reprocess_dry_run_reports_existing_rows_without_writing(self):
        with tempfile.TemporaryDirectory() as td:
            psql = Path(td) / "psql"
            psql.write_text(
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    case "$*" in
                      *"count(*) FILTER"*) printf '1|2|3\\n' ;;
                      *) printf '0\\n' ;;
                    esac
                    """
                ),
                encoding="utf-8",
            )
            psql.chmod(0o755)
            env = dict(
                os.environ,
                DATABASE_URL="postgresql://unused/test",
                PSQL_BIN=str(psql),
            )

            proc = subprocess.run(
                [
                    sys.executable,
                    str(NORMALIZE),
                    "--source",
                    "tw_165_article_search",
                    "--reprocess",
                ],
                text=True,
                capture_output=True,
                env=env,
            )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        summary = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertEqual(summary["new_documents"], 1)
        self.assertEqual(summary["changed_documents"], 2)
        self.assertEqual(summary["reprocessed_documents"], 3)
        self.assertFalse(summary["apply"])

    def test_reprocess_apply_updates_by_staging_id_without_replacing_document_id(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "psql.log"
            psql = Path(td) / "psql"
            psql.write_text(
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    printf '%s\\n' "$*" >> "$PSQL_LOG"
                    case "$*" in
                      *"count(*) FILTER"*) printf '0|1|1\\n' ;;
                      *) printf 'ok\\n' ;;
                    esac
                    """
                ),
                encoding="utf-8",
            )
            psql.chmod(0o755)
            env = dict(
                os.environ,
                DATABASE_URL="postgresql://unused/test",
                PSQL_BIN=str(psql),
                PSQL_LOG=str(log),
            )

            proc = subprocess.run(
                [
                    sys.executable,
                    str(NORMALIZE),
                    "--source",
                    "tw_165_article_search",
                    "--reprocess",
                    "--apply",
                ],
                text=True,
                capture_output=True,
                env=env,
            )
            executed = log.read_text(encoding="utf-8")

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ON CONFLICT (staging_id) DO UPDATE", executed)
        self.assertNotIn("id = EXCLUDED.id", executed)
        self.assertIn("DELETE FROM category_evidence", executed)
        self.assertIn("s.raw_json->'metadata'", executed)
        self.assertIn(
            "WHERE NULLIF(s.raw_json->>'taxonomy_code', '') IS NOT NULL", executed
        )


if __name__ == "__main__":
    unittest.main()
