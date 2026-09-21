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
    def test_questions_require_published_parent_and_child(self):
        sql = export_published_seed.question_copy_query()
        self.assertIn("JOIN public.game_cases gc ON gc.id = q.case_id", sql)
        self.assertIn("q.status = 'published' AND gc.status = 'published'", sql)
        self.assertIn("ORDER BY q.id", sql)
        for column in export_published_seed.QUESTION_COLUMNS:
            self.assertIn(f"q.{column}", sql)

    def test_schema_dump_includes_both_tables_in_both_sections(self):
        with patch.object(
            export_published_seed, "run_pg_dump", return_value="-- schema"
        ) as dump:
            for section in ("pre-data", "post-data"):
                export_published_seed.dump_schema_section(section)
                self.assertIn("--table=public.game_cases", dump.call_args.args)
                self.assertIn("--table=public.game_case_questions", dump.call_args.args)
                self.assertIn(f"--section={section}", dump.call_args.args)

    def test_copy_order_sequences_and_exactly_one_final_newline(self):
        for trailing in ("", "\n", "\n\n\n", "\n  \n"):
            seed = export_published_seed.compose_seed(
                "-- pre\n", "parent-data", "-- post" + trailing, "child-data"
            )
            self.assertLess(
                seed.index("parent-data"), seed.index("COPY public.game_case_questions")
            )
            self.assertLess(seed.index("child-data"), seed.index("-- post"))
            for table in ("game_cases", "game_case_questions"):
                self.assertIn(f"'public.{table}_id_seq'", seed)
                self.assertIn(
                    f"COALESCE((SELECT max(id) FROM public.{table}), 1)", seed
                )
                self.assertIn(f"EXISTS (SELECT 1 FROM public.{table})", seed)
            self.assertTrue(seed.endswith("-- post\n"))
            self.assertFalse(seed.endswith("\n\n"))

    def test_main_exports_both_copy_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "seed.sql"
            with (
                patch.object(export_published_seed, "load_env"),
                patch.object(
                    export_published_seed,
                    "published_stats",
                    return_value={"published": 1, "published_questions": 1},
                ),
                patch.object(
                    export_published_seed,
                    "dump_schema_section",
                    side_effect=["-- pre", "-- post\n\n"],
                ),
                patch.object(
                    export_published_seed,
                    "psql_copy_stdout",
                    side_effect=["parent-data\n", "child-data\n"],
                ) as copy,
                patch("sys.argv", ["export_published_seed.py", "--output", str(path)]),
                patch("builtins.print"),
            ):
                self.assertEqual(export_published_seed.main(), 0)
            self.assertEqual(copy.call_count, 2)
            seed = path.read_text()
            self.assertIn("child-data\n\\.\n", seed)
            self.assertTrue(seed.endswith("-- post\n"))

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
