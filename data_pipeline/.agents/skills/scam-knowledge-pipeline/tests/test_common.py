#!/usr/bin/env python3
"""共用資料庫連線參數的回歸測試。"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import common  # noqa: E402


class DatabaseArgsTests(unittest.TestCase):
    def test_missing_database_url_fails_with_connection_guidance(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit) as caught:
                common.db_args()

        message = str(caught.exception)
        self.assertIn("DATABASE_URL", message)
        self.assertIn("--env-file", message)


if __name__ == "__main__":
    unittest.main()
