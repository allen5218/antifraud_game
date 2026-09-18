#!/usr/bin/env python3
"""staging upsert 必須更新同一 case_key，且保留 staging id。"""

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
INGEST = SKILL / "scripts" / "ingest_jsonb.py"


class IngestUpsertTests(unittest.TestCase):
    def test_apply_upserts_same_source_and_case_key_without_replacing_id(self):
        record = {
            "source_name": "tw_165_article_search",
            "source_type": "government_warning",
            "source_url": "https://example.test/article/1",
            "canonical_url": "https://example.test/article/1",
            "case_key": "stable-case-key",
            "content_hash": "sha256:changed",
            "validation_status": "valid",
            "source_verification_status": "verified",
            "fetched_at": "2026-09-17T00:00:00Z",
            "content_kind": "domain_list",
            "clean_text": "已修正的純文字",
        }
        with tempfile.TemporaryDirectory() as td:
            inp = Path(td) / "input.jsonl"
            inp.write_text(
                json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            log = Path(td) / "psql.log"
            psql = Path(td) / "psql"
            psql.write_text(
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    printf '%s\\n' "$*" >> "$PSQL_LOG"
                    cat >> "$PSQL_LOG"
                    printf 'ok\\n'
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
                [sys.executable, str(INGEST), "--input", str(inp), "--apply"],
                text=True,
                capture_output=True,
                env=env,
            )
            executed = log.read_text(encoding="utf-8")

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ON CONFLICT (source_name, case_key)", executed)
        self.assertIn("raw_json = EXCLUDED.raw_json", executed)
        self.assertNotIn("id = EXCLUDED.id", executed)


if __name__ == "__main__":
    unittest.main()
