#!/usr/bin/env python3
"""game_cases ingest 的 dry-run 衝突與寫入計數回歸測試。"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "ingest_game_cases.py"

BASE_RECORD = {
    "case_key": "shopping-scam-001",
    "fraud_type": "shopping",
    "is_scam": True,
    "title": "測試題目",
    "narrative": "測試敘事",
    "red_flags": [{"tag": "time_pressure", "text": "催促付款"}],
    "difficulty": 1,
    "source_document_ids": [],
    "provenance": "測試來源",
    "mirror_of_key": None,
}

FAKE_PSQL = r"""#!/usr/bin/env python3
import json
import os
import sys

sql = sys.argv[sys.argv.index("-c") + 1] if "-c" in sys.argv else ""
mode = os.environ.get("FAKE_PSQL_MODE")
if "status <> 'draft'" in sql:
    if mode == "published-conflict":
        print(json.dumps([{"case_key": "shopping-scam-001", "status": "published"}]))
    else:
        print("[]")
elif "INSERT INTO game_cases" in sql:
    print("1" if mode == "write-one" and "shopping-scam-001" in sql else "")
elif "legit_without_anchor" in sql or "is_scam = false" in sql:
    print("0")
"""


class IngestGameCasesTests(unittest.TestCase):
    def run_ingest(self, records, *extra, mode):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_path = root / "cases.jsonl"
            input_path.write_text(
                "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
                + "\n",
                encoding="utf-8",
            )
            fake_psql = root / "psql"
            fake_psql.write_text(FAKE_PSQL, encoding="utf-8")
            fake_psql.chmod(0o755)
            env = {
                **os.environ,
                "PATH": f"{root}{os.pathsep}{os.environ.get('PATH', '')}",
                "DATABASE_URL": "postgresql://example.invalid/test",
                "FAKE_PSQL_MODE": mode,
            }
            return subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(input_path), *extra],
                cwd=str(SKILL / "scripts"),
                env=env,
                text=True,
                capture_output=True,
            )

    def test_dry_run_reports_non_draft_conflict_and_exits_nonzero(self):
        proc = self.run_ingest([BASE_RECORD], mode="published-conflict")

        self.assertNotEqual(proc.returncode, 0)
        summary = json.loads(proc.stdout.strip().splitlines()[0])
        self.assertEqual(
            summary["non_draft_conflicts"],
            [{"case_key": "shopping-scam-001", "status": "published"}],
        )
        self.assertIn("-v2", proc.stdout + proc.stderr)

    def test_apply_reports_rows_returned_by_upsert(self):
        second_record = dict(BASE_RECORD, case_key="shopping-scam-002")
        proc = self.run_ingest(
            [BASE_RECORD, second_record], "--apply", mode="write-one"
        )

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        result = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertEqual(result["ingested"], 1)


if __name__ == "__main__":
    unittest.main()
