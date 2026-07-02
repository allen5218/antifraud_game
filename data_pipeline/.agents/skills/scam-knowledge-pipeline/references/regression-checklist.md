# Regression Checklist

Use this checklist after parser, taxonomy, database, or embedding changes. Run each source through `scripts/run_source_pipeline.sh` with a bounded `--max-records` where applicable. Production writes require `--apply`; dry-run first is mandatory.

Current validated smoke matrix:

| Source | Expected bounded records | Expected embedding model | Notes |
| --- | ---: | --- | --- |
| `tw_165_dashboard_cases` | 10 | `gemini-embedding-2` | Dashboard API; includes investment, purchase, romance examples. |
| `tw_165_article_search` | 24 | `gemini-embedding-2` | Five search endpoints cover all five taxonomy categories. |
| `tw_165_structured_query` | 10 | `gemini-embedding-2` | Large 165 structured JSON; investment-focused. |
| `tw_165_fraud_domains_blocked` | 10 | `gemini-embedding-2` | CSV resource; supports truncated CSV parsing for bounded rows. |
| `tw_moda_ecommerce_fraud_domains` | 20 | `gemini-embedding-2` | Two ecommerce CSV endpoints; purchase categories. |
| `tw_165_fake_investment_sites` | 10 | `gemini-embedding-2` | Large CSV; case keys must include stable row identity. |
| `tw_165_scam_rumor_busting` | 8 | `gemini-embedding-2` | Mixed rumor-busting source; non-five-category rows are skipped. |
| `fraudbuster_digiat_accessibility` | 2 | `gemini-embedding-2` | HTML detail pages; requires text evidence before endpoint taxonomy is accepted. |
| `tw_twse_tpex_anti_fraud` | 10 | `gemini-embedding-2` | TWSE/TPEX JSON; investment-focused. |
| `tw_judicial_fraud_judgments` | 25 | `gemini-embedding-2` | Five judicial search endpoints; five records per taxonomy in bounded smoke. |
| `tw_moj_anti_fraud_legal_education` | 1 | `gemini-embedding-2` | CSV metadata expands linked public PDF with bounded `pdftotext`. |
| `tw_chiayi_fraud_channel_methods` | 7 | `gemini-embedding-2` | Local open data; `假網拍` maps to fake online auction; non-five-category rows are skipped. |

Acceptance gates for every row:

- probe status is `verified`;
- fetch emits only `validation_status=valid` rows for validated output;
- `validate_cases.py` reports `rejected=0`;
- valid JSONL has no duplicate `case_key`;
- ingest dry-run reports zero unverified and zero not-valid records;
- normalize, chunk, embed, and audit are run with `--source`;
- source-scoped audit reports `unverified_staging_records=0`, `valid_unnormalized_records=0`, and `chunks_missing_embeddings=0`;
- source-scoped embedding distribution is `gemini-embedding-2` only for production vectors.
