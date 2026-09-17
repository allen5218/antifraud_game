#!/usr/bin/env python3
"""來源抓取的分類、HTML 清理與判決內頁解析回歸測試。"""

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
FETCH = SKILL / "scripts" / "fetch_source.py"
SOURCES = SKILL / "references" / "sources.yaml"
FIXTURES = Path(__file__).parent / "fixtures"


def install_fake_curl(directory, responses):
    response_path = Path(directory) / "responses.json"
    response_path.write_text(
        json.dumps(responses, ensure_ascii=False), encoding="utf-8"
    )
    curl_path = Path(directory) / "curl"
    curl_path.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import json
            import sys
            from pathlib import Path

            args = sys.argv[1:]
            headers_path = Path(args[args.index("-D") + 1])
            body_path = Path(args[args.index("-o") + 1])
            url = args[-1]
            responses = json.loads(Path(__file__).with_name("responses.json").read_text(encoding="utf-8"))
            matched = next(((key, item) for key, item in responses.items() if key in url), None)
            response = matched[1] if matched else None
            if response is None:
                raise SystemExit(f"沒有測試回應：{url}")
            counts_path = Path(__file__).with_name("counts.json")
            counts = json.loads(counts_path.read_text(encoding="utf-8")) if counts_path.exists() else {}
            count = counts.get(matched[0], 0)
            counts[matched[0]] = count + 1
            counts_path.write_text(json.dumps(counts), encoding="utf-8")
            if response.get("expected_cursors"):
                data_arg = args[args.index("--data-binary") + 1]
                request_payload = json.loads(Path(data_arg.removeprefix("@")).read_text(encoding="utf-8"))
                actual_cursor = (request_payload.get("variables") or {}).get("cursor")
                expected_cursor = response["expected_cursors"][min(count, len(response["expected_cursors"]) - 1)]
                if actual_cursor != expected_cursor:
                    raise SystemExit(f"GraphQL cursor 錯誤：expected={expected_cursor!r}, actual={actual_cursor!r}")
            if response.get("expected_form_pages"):
                page_values = [value for value in args if value.startswith("page=")]
                actual_page = int(page_values[-1].split("=", 1)[1]) if page_values else None
                expected_page = response["expected_form_pages"][min(count, len(response["expected_form_pages"]) - 1)]
                if actual_page != expected_page:
                    raise SystemExit(f"form page 錯誤：expected={expected_page!r}, actual={actual_page!r}")
            if response.get("bodies"):
                response = {**response, "body": response["bodies"][min(count, len(response["bodies"]) - 1)]}
            for expected in response.get("expected_args", []):
                if expected not in args:
                    raise SystemExit(f"curl 缺少參數：{expected}; args={args}")
            headers_path.write_text("HTTP/1.1 200 OK\\nContent-Type: " + response["content_type"] + "\\n", encoding="utf-8")
            body_path.write_text(response["body"], encoding="utf-8")
            print("200", end="")
            """
        ),
        encoding="utf-8",
    )
    curl_path.chmod(0o755)


def run_fetch(source_name, responses, sources_path=SOURCES, extra_args=None):
    with tempfile.TemporaryDirectory() as td:
        install_fake_curl(td, responses)
        output = Path(td) / "out.jsonl"
        env = dict(os.environ, PATH=td + os.pathsep + os.environ.get("PATH", ""))
        command = [
            sys.executable,
            str(FETCH),
            "--source",
            source_name,
            "--sources",
            str(sources_path),
            "--out",
            str(output),
            "--source-verification-status",
            "verified",
            "--max-records",
            "5",
        ]
        command.extend(extra_args or [])
        proc = subprocess.run(
            command,
            text=True,
            capture_output=True,
            env=env,
        )
        rows = []
        if output.exists():
            rows = [
                json.loads(line)
                for line in output.read_text(encoding="utf-8").splitlines()
                if line
            ]
        return proc, rows


class FetchSourceTests(unittest.TestCase):
    def fixture(self, name):
        return (FIXTURES / name).read_text(encoding="utf-8")

    def test_structured_query_records_are_domain_lists(self):
        body = json.dumps(
            {"body": [{"webSiteName": "三德投資", "webUrl": "inss.sandcheap.com"}]},
            ensure_ascii=False,
        )

        proc, rows = run_fetch(
            "tw_165_structured_query",
            {"findFraudInvestment": {"content_type": "application/json", "body": body}},
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(rows[0]["content_kind"], "domain_list")

    def test_article_weekly_website_notice_is_domain_list_and_html_is_cleaned(self):
        title = "115/2/26-115/3/4民眾通報假投資(博弈)詐騙網站"
        body = json.dumps(
            [
                {
                    "title": title,
                    "content": "<p>網友不會幫你賺錢&nbsp;請勿聽信</p><p>bad.example</p>",
                    "id": "weekly-1",
                },
                {
                    "title": "最新公告",
                    "content": "<h2>民眾通報假交友詐騙網站</h2><p>romance-bad.example</p>",
                    "id": "weekly-2",
                },
            ],
            ensure_ascii=False,
        )

        proc, rows = run_fetch(
            "tw_165_article_search",
            {
                "/api/article/search/": {
                    "content_type": "application/json",
                    "body": body,
                }
            },
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(row["content_kind"], "domain_list")
            self.assertNotIn("<p>", row["clean_text"])
            self.assertNotIn("&nbsp;", row["clean_text"])
        self.assertIn("網友不會幫你賺錢 請勿聽信\nbad.example", rows[0]["clean_text"])
        self.assertIn(
            "民眾通報假交友詐騙網站\nromance-bad.example", rows[1]["clean_text"]
        )

    def test_article_weekly_ranking_is_advisory_from_configured_patterns(self):
        body = json.dumps(
            [
                {
                    "title": "114/09/27-10/03民眾通報高風險業者",
                    "content": "本週高風險業者排名彙整，提醒民眾網路購物與匯款前再次查證。",
                    "id": "ranking-1",
                },
                {
                    "title": "常見詐騙手法",
                    "content": "本月常見手法包含假投資、假交友與解除分期付款。",
                    "id": "methods-1",
                },
            ],
            ensure_ascii=False,
        )

        proc, rows = run_fetch(
            "tw_165_article_search",
            {
                "/api/article/search/": {
                    "content_type": "application/json",
                    "body": body,
                }
            },
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            [row["content_kind"] for row in rows], ["advisory"] * len(rows)
        )

    def test_article_high_risk_vendor_item_list_is_domain_list(self):
        body = json.dumps(
            [
                {
                    "title": "統計民眾通報高風險業者",
                    "content": "1、甲網站 bad-a.example\n2、乙網站 bad-b.example\n3、丙網站 bad-c.example",
                    "id": "vendor-list-1",
                }
            ],
            ensure_ascii=False,
        )

        proc, rows = run_fetch(
            "tw_165_article_search",
            {
                "/api/article/search/": {
                    "content_type": "application/json",
                    "body": body,
                }
            },
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(rows)
        self.assertTrue(all(row["content_kind"] == "domain_list" for row in rows))

    def test_article_method_explainer_is_advisory(self):
        body = json.dumps(
            [
                {
                    "title": "網路購物遇到詐騙了？社群買賣詐騙話術解析",
                    "content": "整理社群買賣風險與詐騙話術解析，提醒民眾查證。",
                    "id": "methods-explainer-1",
                }
            ],
            ensure_ascii=False,
        )

        proc, rows = run_fetch(
            "tw_165_article_search",
            {
                "/api/article/search/": {
                    "content_type": "application/json",
                    "body": body,
                }
            },
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(rows[0]["content_kind"], "advisory")

    def test_dashboard_case_study_description_becomes_advisory_text(self):
        proc, rows = run_fetch(
            "tw_165_dashboard_cases",
            {
                "FraudMethod": {"content_type": "application/json", "body": "[]"},
                "CaseStudy": {
                    "content_type": "application/json",
                    "body": self.fixture("dashboard_case_study.json"),
                },
            },
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["page_title"], "常見徵才話術")
        self.assertEqual(rows[0]["content_kind"], "advisory")
        self.assertEqual(
            rows[0]["clean_text"],
            "常見徵才話術\n1、 家庭代工\n2、 幫企業節稅\n3、 博弈徵才並要求提供銀行帳戶",
        )
        self.assertFalse(rows[0]["clean_text"].startswith("{"))

    def test_fraudbuster_keeps_summary_only_as_message_sample(self):
        proc, rows = run_fetch(
            "fraudbuster_digiat_accessibility",
            {
                "/accessibility/index": {
                    "content_type": "text/html",
                    "body": self.fixture("fraudbuster_list.html"),
                },
                "/accessibility/detail": {
                    "content_type": "text/html",
                    "body": self.fixture("fraudbuster_detail.html"),
                },
                "/accessibility/search": {
                    "content_type": "text/html",
                    "body": "<html><body>沒有結果</body></html>",
                },
            },
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["content_kind"], "message_sample")
        self.assertTrue(rows[0]["clean_text"].startswith("限時投資方案"))
        self.assertNotIn("案件詳情", rows[0]["clean_text"])
        self.assertNotIn("內容摘要", rows[0]["clean_text"])
        self.assertNotIn("展開更多內容", rows[0]["clean_text"])
        self.assertNotIn("處理進度", rows[0]["clean_text"])
        self.assertNotIn("2026/09/16", rows[0]["clean_text"])

    def test_fraudbuster_timestamp_alone_ends_message_sample(self):
        detail = """<main id="aC"><h2>內容摘要</h2>
        <p>投資老師保證獲利，要求加入 LINE 群組並立刻匯款到指定帳戶，今天截止。</p>
        <p>2026/09/16 13:30</p></main>"""
        proc, rows = run_fetch(
            "fraudbuster_digiat_accessibility",
            {
                "/accessibility/index": {
                    "content_type": "text/html",
                    "body": self.fixture("fraudbuster_list.html"),
                },
                "/accessibility/detail": {"content_type": "text/html", "body": detail},
                "/accessibility/search": {
                    "content_type": "text/html",
                    "body": "<html><body>沒有結果</body></html>",
                },
            },
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(rows), 1)
        self.assertNotIn("2026/09/16", rows[0]["clean_text"])

    def test_cofacts_scam_messages_filter_clean_dedupe_and_classify(self):
        proc, rows = run_fetch(
            "tw_cofacts_scam_messages",
            {
                "api.cofacts.tw/graphql": {
                    "content_type": "application/json",
                    "body": self.fixture("cofacts_scam_messages.json"),
                    "expected_args": ["x-app-id: RUMORS_SITE"],
                }
            },
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["content_kind"], "message_sample")
        self.assertEqual(rows[0]["case_stance"], "scam")
        self.assertEqual(
            rows[0]["source_url"], "https://cofacts.tw/article/21lg156mv9n3s"
        )
        self.assertNotIn("22:29", rows[0]["clean_text"])
        self.assertNotIn("5G", rows[0]["clean_text"])
        self.assertNotIn("已讀", rows[0]["clean_text"])
        self.assertNotIn(
            "articleReplies", rows[0]["raw_payload"]["endpoint"]["json"]["query"]
        )

    def test_cofacts_graphql_schema_error_retries_with_safe_query(self):
        graphql_error = json.dumps(
            {"errors": [{"message": "Cannot query field replyRequestCount"}]},
            ensure_ascii=False,
        )
        proc, rows = run_fetch(
            "tw_cofacts_scam_messages",
            {
                "api.cofacts.tw/graphql": {
                    "content_type": "application/json",
                    "bodies": [
                        graphql_error,
                        self.fixture("cofacts_scam_messages.json"),
                    ],
                    "body": graphql_error,
                    "expected_args": ["x-app-id: RUMORS_SITE"],
                }
            },
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["content_kind"], "message_sample")
        self.assertEqual(rows[0]["validation_status"], "needs_review")
        self.assertEqual(rows[0]["source_verification_status"], "candidate")

    def test_cofacts_uses_live_shape_and_pages_until_filtered_limit(self):
        live_page = self.fixture("live_capture/cofacts_page1.json")
        valid_edges = [
            {
                "cursor": f"accepted-{index}",
                "node": {
                    "id": f"accepted-{index}",
                    "text": f"投資老師第{index}則訊息宣稱保證獲利，要求加入群組並匯款到指定帳戶，還催促今天立刻完成操作才能領取收益。",
                    "createdAt": "2026-09-16T01:00:00.000Z",
                    "lastRequestedAt": "2026-09-16T02:00:00.000Z",
                    "replyRequestCount": 1,
                },
            }
            for index in range(5)
        ]
        second_page = json.dumps(
            {
                "data": {
                    "ListArticles": {
                        "totalCount": 8844,
                        "edges": valid_edges,
                        "pageInfo": {"lastCursor": None},
                    }
                }
            },
            ensure_ascii=False,
        )

        proc, rows = run_fetch(
            "tw_cofacts_scam_messages",
            {
                "api.cofacts.tw/graphql": {
                    "content_type": "application/json",
                    "bodies": [live_page, second_page],
                    "body": live_page,
                    "expected_cursors": [None, "WzE0ODIwOTMxMjAwMDAsNTEzNDkwXQ=="],
                }
            },
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(rows), 5)
        summary = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertEqual(summary["pages_fetched"], 2)
        self.assertEqual(
            set(summary["filter_drop_counts"]),
            {"length", "ocr_too_short", "url_heavy", "duplicate", "unclassified"},
        )

    def test_cofacts_later_invalid_json_keeps_partial_records_as_candidate(self):
        first_page = json.dumps(
            {
                "data": {
                    "ListArticles": {
                        "edges": [
                            {
                                "cursor": "cursor-one",
                                "node": {
                                    "id": "partial-one",
                                    "text": "投資老師聲稱保證獲利，要求加入群組並立即匯款到指定帳戶，還說今天錯過就不能領取高額收益。",
                                    "createdAt": "2026-09-17T01:00:00.000Z",
                                    "lastRequestedAt": "2026-09-17T02:00:00.000Z",
                                },
                            }
                        ],
                        "pageInfo": {"lastCursor": "cursor-one"},
                    }
                }
            },
            ensure_ascii=False,
        )

        proc, rows = run_fetch(
            "tw_cofacts_scam_messages",
            {
                "api.cofacts.tw/graphql": {
                    "content_type": "application/json",
                    "bodies": [first_page, "{invalid-json"],
                    "body": first_page,
                    "expected_cursors": [None, "cursor-one"],
                }
            },
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_verification_status"], "candidate")
        self.assertEqual(rows[0]["validation_status"], "needs_review")
        summary = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertTrue(summary["pagination_errors"])

    def test_cofacts_since_excludes_records_at_or_before_incremental_boundary(self):
        proc, rows = run_fetch(
            "tw_cofacts_scam_messages",
            {
                "api.cofacts.tw/graphql": {
                    "content_type": "application/json",
                    "body": self.fixture("cofacts_scam_messages.json"),
                }
            },
            extra_args=["--since", "2026-09-18T00:00:00.000Z"],
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(rows, [])

    def test_cofacts_since_keeps_equal_timestamp_for_content_deduplication(self):
        proc, rows = run_fetch(
            "tw_cofacts_scam_messages",
            {
                "api.cofacts.tw/graphql": {
                    "content_type": "application/json",
                    "body": self.fixture("cofacts_scam_messages.json"),
                }
            },
            extra_args=["--since", "2026-09-17T02:03:04.000Z"],
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0]["source_url"], "https://cofacts.tw/article/21lg156mv9n3s"
        )

    def test_cofacts_since_skips_known_id_at_equal_timestamp(self):
        proc, rows = run_fetch(
            "tw_cofacts_scam_messages",
            {
                "api.cofacts.tw/graphql": {
                    "content_type": "application/json",
                    "body": self.fixture("cofacts_scam_messages.json"),
                }
            },
            extra_args=[
                "--since",
                "2026-09-17T02:03:04.000Z",
                "--known-id",
                "21lg156mv9n3s",
            ],
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(rows, [])

    def test_cofacts_incremental_fetch_crosses_cap_until_older_than_boundary(self):
        def node(index, timestamp):
            return {
                "cursor": f"cursor-{index}",
                "node": {
                    "id": f"article-{index}",
                    "text": f"投資老師第{index}則訊息聲稱保證獲利，要求加入群組並匯款到指定帳戶才能開始操作，請立即處理。",
                    "createdAt": timestamp,
                    "lastRequestedAt": timestamp,
                },
            }

        page_one = json.dumps(
            {
                "data": {
                    "ListArticles": {
                        "edges": [
                            node(i, f"2026-09-1{9 - i}T02:03:04.000Z") for i in range(5)
                        ],
                        "pageInfo": {"lastCursor": "cursor-4"},
                    }
                }
            },
            ensure_ascii=False,
        )
        page_two = json.dumps(
            {
                "data": {
                    "ListArticles": {
                        "edges": [
                            node(5, "2026-09-13T02:03:04.000Z"),
                            node(6, "2026-09-11T02:03:04.000Z"),
                        ],
                        "pageInfo": {"lastCursor": None},
                    }
                }
            },
            ensure_ascii=False,
        )

        proc, rows = run_fetch(
            "tw_cofacts_scam_messages",
            {
                "api.cofacts.tw/graphql": {
                    "content_type": "application/json",
                    "bodies": [page_one, page_two],
                    "body": page_one,
                }
            },
            extra_args=["--since", "2026-09-12T00:00:00.000Z"],
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(rows), 6)
        self.assertNotIn(
            "https://cofacts.tw/article/article-6", {row["source_url"] for row in rows}
        )

    def test_cofacts_not_rumor_candidates_are_always_advisory_and_require_review(self):
        proc, rows = run_fetch(
            "tw_cofacts_legit_lookalikes",
            {
                "api.cofacts.tw/graphql": {
                    "content_type": "application/json",
                    "body": self.fixture("cofacts_legit_lookalikes.json"),
                    "expected_args": ["x-app-id: RUMORS_SITE"],
                }
            },
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(row["case_stance"], "advisory")
            self.assertEqual(row["content_kind"], "advisory")
            self.assertEqual(
                row["metadata"],
                {
                    "candidate_for": "legit_lookalike",
                    "review_required": True,
                },
            )

    def test_fsc_press_filters_titles_and_fetches_detail_text(self):
        proc, rows = run_fetch(
            "tw_fsc_antifraud_press",
            {
                "mcustomize=news_view.jsp": {
                    "content_type": "text/html",
                    "body": self.fixture("live_capture/fsc_press_detail.html"),
                },
                "home.jsp?id=96": {
                    "content_type": "text/html",
                    "body": self.fixture(
                        "live_capture/fsc_press_list_keyword_page1.html"
                    ),
                    "expected_args": ["POST", "pagesize=20", "keyword=詐"],
                    "expected_form_pages": [1, 2, 3],
                },
            },
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertGreaterEqual(len(rows), 1)
        row = next(row for row in rows if "2026金檢警聯防" in row["page_title"])
        self.assertEqual(row["case_stance"], "advisory")
        self.assertEqual(row["content_kind"], "advisory")
        self.assertEqual(row["validation_status"], "valid")
        self.assertIsNone(row["taxonomy_code"])
        self.assertIn("金融機構114年度臨櫃攔阻詐騙金額", row["clean_text"])
        self.assertNotIn("網站導覽", row["clean_text"])

    def test_judicial_detail_uses_configured_selector_and_keeps_crime_facts(self):
        list_html = '<a id="hlTitle" href="/LAW_Mobile_FJUD/FJUD/data.aspx?ty=JD&amp;id=fixed">判決</a>'
        detail_html = (FIXTURES / "judicial_detail_nested.html").read_text(
            encoding="utf-8"
        )

        proc, rows = run_fetch(
            "tw_judicial_fraud_judgments",
            {
                "qryresult.aspx": {"content_type": "text/html", "body": list_html},
                "data.aspx": {"content_type": "text/html", "body": detail_html},
            },
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(rows), 5)
        self.assertIn("犯罪事實", rows[0]["body_text"])
        self.assertIn("分次匯款至指定帳戶", rows[0]["clean_text"])
        self.assertNotIn("不應擷取的頁尾", rows[0]["clean_text"])
        self.assertGreaterEqual(len(rows[0]["clean_text"]), 150)
        self.assertIn("detail_html", rows[0]["raw_payload"]["record"])

    def test_long_judgment_prioritizes_crime_facts_in_bounded_clean_text(self):
        list_html = '<a id="hlTitle" href="/LAW_Mobile_FJUD/FJUD/data.aspx?ty=JD&amp;id=long">判決</a>'
        detail_html = (
            '<div class="htmlcontent"><p>臺灣某地方法院刑事判決</p>'
            + "<p>前段程序文字</p>" * 4000
            + "<p>犯罪事實</p><p>被告假冒投資老師要求被害人匯款，致被害人受有財產損失。</p>"
            + "<p>理由</p><p>證據資料</p></div>"
        )

        proc, rows = run_fetch(
            "tw_judicial_fraud_judgments",
            {
                "qryresult.aspx": {"content_type": "text/html", "body": list_html},
                "data.aspx": {"content_type": "text/html", "body": detail_html},
            },
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertGreater(len(rows[0]["body_text"]), 20000)
        self.assertLessEqual(len(rows[0]["clean_text"]), 20000)
        self.assertTrue(rows[0]["clean_text"].startswith("犯罪事實\n被告假冒投資老師"))


if __name__ == "__main__":
    unittest.main()
