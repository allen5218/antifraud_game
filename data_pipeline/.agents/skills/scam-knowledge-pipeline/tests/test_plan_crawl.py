#!/usr/bin/env python3
"""Cofacts crawl plan 必須帶出 staging 內最新時間，供 fetch 增量停止。"""

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
PLAN = SKILL / "scripts" / "plan_crawl.py"


class PlanCrawlTests(unittest.TestCase):
    def test_cofacts_plan_includes_latest_message_timestamp_as_since(self):
        with tempfile.TemporaryDirectory() as td:
            psql = Path(td) / "psql"
            psql.write_text(
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    printf 'tw_cofacts_scam_messages\\thttps://cofacts.tw/article/old\\tsha256:old\\t2026-09-16T02:03:04.000Z\\told-article-id\\n'
                    """
                ),
                encoding="utf-8",
            )
            psql.chmod(0o755)
            output = Path(td) / "plan.json"
            env = dict(
                os.environ, DATABASE_URL="postgresql://unused/test", PSQL_BIN=str(psql)
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(PLAN),
                    "--out",
                    str(output),
                    "--include-unverified",
                ],
                text=True,
                capture_output=True,
                env=env,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            plan = json.loads(output.read_text(encoding="utf-8"))

        source = next(
            item
            for item in plan["sources"]
            if item["source_name"] == "tw_cofacts_scam_messages"
        )
        self.assertEqual(source["items"][0]["since"], "2026-09-16T02:03:04.000Z")
        self.assertEqual(
            source["items"][0]["fetch_args"],
            ["--since", "2026-09-16T02:03:04.000Z", "--known-id", "old-article-id"],
        )


if __name__ == "__main__":
    unittest.main()
