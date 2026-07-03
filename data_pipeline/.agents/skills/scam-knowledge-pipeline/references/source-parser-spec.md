# Source Parser Spec

Use `references/sources.yaml` as the source-of-truth registry for crawl behavior. The file is JSON-compatible YAML, so keep it valid JSON.

## Source-Level Fields

- `parser_type`: one of `json_endpoint`, `html_dataset_page`, `html_selector`, `csv_resource`, `playwright_dom`, or `playwright_network`.
- `verification_policy`: `any_success`, `all_endpoints`, or `min_successful_endpoints`.
- `min_successful_endpoints`: required when `verification_policy` is `min_successful_endpoints`.
- `timeout_seconds`: default HTTP timeout for the source.
- `probe_max_bytes`: maximum bytes read during probe.
- `fetch_max_bytes`: maximum bytes read during fetch.
- `drop_unclassified`: optional boolean. When `true`, `fetch_source.py` skips parsed records that cannot be classified into one of the five controlled taxonomy categories with confidence above `min_classification_confidence`. Use this for broad education or rumor-busting sources that contain many public-safety items outside the five-category scope.
- `min_classification_confidence`: optional number used with `drop_unclassified`; default is `0.01`.
- `require_taxonomy_keyword_match`: optional boolean. When `true`, endpoint-level `taxonomy_code` is accepted only if the fetched record text contains one of that endpoint's `keywords`; otherwise keyword rules decide or the record is skipped when `drop_unclassified` is enabled.
- `expand_pdf_links`: optional boolean for CSV resources whose rows point to public PDF files. When `true`, `fetch_source.py` downloads the linked PDF to a temporary file, extracts bounded text with `pdftotext`, and stores the extracted text in `raw_payload.record.pdf_text` for classification and JSONB ingest.
- `pdf_link_fields`: optional list of CSV fields that may contain PDF URLs; default is `["檔案連結", "file_url", "url"]`.
- `pdf_max_pages`, `pdf_max_chars`, `pdf_timeout_seconds`: optional controls for bounded PDF extraction.
- `verify_tls`: optional. Use `false` only for a documented public source with a known certificate-chain problem; such sources should remain candidate until manually reviewed.
- `default_case_stance`: optional enum (`scam` | `legit` | `advisory`). When specified, `fetch_source.py` stamps each fetched record with this stance during ingest; may be overwritten during classification phase. If absent, defaults to `scam`. **Warning:** legit or advisory sources that omit this field will be silently stamped as scam cases, adding them to the fraud example pool.
- `default_content_kind`: optional enum (`case_narrative` | `domain_list` | `advisory` | `statute`). When specified, stamps each record's content kind; may be overwritten during classification. If absent, defaults to `case_narrative`. Follows same silent-fallback rule as `default_case_stance`.

## Endpoint-Level Fields

Each endpoint may override source-level fields and may declare classification hints:

- `taxonomy_code`: controlled code from the five-category taxonomy.
- `source_category_label`: Traditional Chinese source label.
- `keywords`: Traditional Chinese keywords expected in the response.
- `drop_unclassified`, `min_classification_confidence`: endpoint-specific overrides for broad mixed-category resources.
- `require_taxonomy_keyword_match`: endpoint-specific override for search endpoints whose result pages may include records outside the query category.
- `expand_pdf_links`, `pdf_link_fields`, `pdf_max_pages`, `pdf_max_chars`, `pdf_timeout_seconds`: endpoint-specific overrides for bounded PDF text extraction.
- `parser_type`: endpoint-specific parser override.
- `timeout_seconds`, `probe_max_bytes`, `fetch_max_bytes`, `verify_tls`: endpoint-specific fetch controls.

Endpoint taxonomy is authoritative only for search endpoints whose query itself expresses the fraud category, such as 165 article-search endpoints. Otherwise, Codex must classify the record from fetched content and evidence.

## Script Behavior

- `probe_source.py` records endpoint success, truncation, parser type, and taxonomy hints.
- `fetch_source.py` writes classified JSONL using endpoint taxonomy first, then keyword rules.
- A fetched record is `valid` only when HTTP succeeded, text is non-empty, the response was not truncated, and classification confidence is above zero.
- If `drop_unclassified` is true, fetched records with no five-category evidence are skipped rather than emitted as invalid rows.
- Failed, parse-error, or truncated endpoint results are written as diagnostic `needs_review` / `candidate` rows with transport/error metadata and must not be applied.
- `ingest_jsonb.py --apply` still refuses unverified sources and non-valid records.

## Production Rule

Live source content can be applied only after:

1. source probe passes under the configured verification policy,
2. fetched JSONL validates against `schemas/scam_case.schema.json`,
3. the agent confirms the records are live-crawled, not synthetic,
4. the user or runbook explicitly uses `--apply`.
