#!/usr/bin/env python3
"""GraphQL schema errors 即使 HTTP 200 也不可通過來源驗證。"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_fetch_source import install_fake_curl

SKILL = Path(__file__).resolve().parents[1]
PROBE = SKILL / "scripts" / "probe_source.py"


class ProbeSourceTests(unittest.TestCase):
    def test_graphql_errors_are_not_counted_as_records(self):
        with tempfile.TemporaryDirectory() as td:
            install_fake_curl(
                td,
                {
                    "api.cofacts.tw/graphql": {
                        "content_type": "application/json",
                        "body": json.dumps({"errors": [{"message": "bad field"}]}),
                    }
                },
            )
            output = Path(td) / "probe.json"
            env = dict(os.environ, PATH=td + os.pathsep + os.environ.get("PATH", ""))
            proc = subprocess.run(
                [
                    sys.executable,
                    str(PROBE),
                    "--source",
                    "tw_cofacts_scam_messages",
                    "--out",
                    str(output),
                ],
                text=True,
                capture_output=True,
                env=env,
            )
            report = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(report["verification_status"], "failed")
        self.assertEqual(report["results"][0]["parsed_record_count"], 0)

    def test_fsc_probe_posts_configured_form(self):
        fixture = (
            SKILL
            / "tests"
            / "fixtures"
            / "live_capture"
            / "fsc_press_list_keyword_page1.html"
        )
        with tempfile.TemporaryDirectory() as td:
            install_fake_curl(
                td,
                {
                    "home.jsp?id=96": {
                        "content_type": "text/html",
                        "body": fixture.read_text(encoding="utf-8"),
                        "expected_args": [
                            "POST",
                            "page=1",
                            "pagesize=20",
                            "keyword=詐",
                        ],
                    }
                },
            )
            output = Path(td) / "probe.json"
            env = dict(os.environ, PATH=td + os.pathsep + os.environ.get("PATH", ""))
            proc = subprocess.run(
                [
                    sys.executable,
                    str(PROBE),
                    "--source",
                    "tw_fsc_antifraud_press",
                    "--out",
                    str(output),
                ],
                text=True,
                capture_output=True,
                env=env,
            )
            report = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(report["verification_status"], "verified")
        self.assertGreater(report["parsed_records"], 0)


if __name__ == "__main__":
    unittest.main()
