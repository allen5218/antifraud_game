#!/usr/bin/env python3
"""published game_cases 種子匯出器的回歸測試。"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import export_published_seed  # noqa: E402
import leak_probe  # noqa: E402


class ExportPublishedSeedTests(unittest.TestCase):
    def test_copy_query_filters_published_and_nulls_unpublished_mirror(self):
        sql = export_published_seed.copy_query()
        self.assertIn("WHERE gc.status = 'published'", sql)
        self.assertIn("mirror.status = 'published'", sql)
        self.assertIn("ELSE NULL", sql)
        self.assertIn("ORDER BY gc.id", sql)

    def test_composed_seed_is_readable_by_leak_probe_and_sets_sequence(self):
        red_flags = json.dumps(
            [
                {"tag": "authority", "text": "自稱銀行專員要求依指示付款"},
                {"tag": "greed", "text": "聲稱投入少量資金就能得到大量收益"},
            ],
            ensure_ascii=False,
        )
        data = (
            "\t".join(
                [
                    "7",
                    "seed-scam-001",
                    "investment",
                    "t",
                    "群組裡的投資邀請",
                    "尚未揭曉結局的案例內容",
                    red_flags,
                    "2",
                    "{1}",
                    "測試出處",
                    r"\N",
                    "published",
                    r"\N",
                    "2026-01-01 00:00:00+00",
                    "2026-01-02 00:00:00+00",
                ]
            )
            + "\n"
        )
        seed = export_published_seed.compose_seed("-- pre\n", data, "-- post\n")
        self.assertIn("COPY public.game_cases", seed)
        self.assertIn("SELECT pg_catalog.setval", seed)
        self.assertIn("\\.\n", seed)

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "seed.sql"
            path.write_text(seed, encoding="utf-8")
            rows = leak_probe.load_from_dump(path)
        self.assertEqual([row["case_key"] for row in rows], ["seed-scam-001"])

    def test_dry_run_only_prints_stats_and_does_not_dump_schema(self):
        stats = {
            "published": 40,
            "scam": 20,
            "legit": 20,
            "detached_mirrors": 0,
        }
        with (
            patch.object(export_published_seed, "load_env"),
            patch.object(export_published_seed, "published_stats", return_value=stats),
            patch.object(export_published_seed, "dump_schema_section") as dump,
            patch("sys.argv", ["export_published_seed.py"]),
            patch("builtins.print") as output,
        ):
            code = export_published_seed.main()

        self.assertEqual(code, 0)
        dump.assert_not_called()
        self.assertIn('"published": 40', output.call_args.args[0])
