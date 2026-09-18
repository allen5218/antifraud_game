# Source Parser Spec

Use `references/sources.yaml` as the source-of-truth registry for crawl behavior. The file is JSON-compatible YAML, so keep it valid JSON.

## Source-Level Fields

- `parser_type`: one of `json_endpoint`, `html_dataset_page`, `html_selector`, `csv_resource`, `playwright_dom`, or `playwright_network`. GraphQL JSON responses also use `json_endpoint`.
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
- `default_content_kind`: optional enum (`case_narrative` | `message_sample` | `domain_list` | `advisory` | `statute`). When specified, stamps each record's content kind; may be overwritten during classification. If absent, defaults to `case_narrative`. Follows same silent-fallback rule as `default_case_stance`.
- `headers`: optional request headers. Cofacts requires `x-app-id: RUMORS_SITE`; JSON bodies continue to receive `Content-Type: application/json` automatically.
- `form`: optional URL-encoded POST form body. Both probe and fetch use it; FSC sets `page`, `pagesize`, and `keyword` here.
- `allow_unclassified_advisory`: when true, an `advisory`/`advisory` record with no evidence for the five fraud categories remains valid with `taxonomy_code: null`. Normalization stores the document but does not create `document_categories` or `category_evidence` rows; no artificial generic taxonomy is introduced.
- `allow_unclassified_message_sample`: when true, an unclassified `scam` or `legit` `message_sample` remains valid with `taxonomy_code: null`. This is restricted by schema to `tw_cofacts_scam_messages` and `fraudbuster_digiat_accessibility`; normalization stores the document without category rows for later manual curation.
- `min_message_chars`: optional minimum `clean_text` length for `message_sample` records. The fraudbuster source sets this to 40; shorter detail text is discarded as `no_message_body` because it cannot form a usable question sample.
- `message_placeholder_patterns`: optional list of case-insensitive full-match regexes for placeholder or error-page remnants. The fraudbuster source uses this to discard values such as `Page not found.`、`商品详情`、`404` and `Not Found` as `no_message_body`; surrounding whitespace is ignored by text cleaning.
- `content_kind_patterns`: ordered, per-kind `title`／`content` regex rules. `tw_165_article_search` uses these config rules to route list/ranking/summary posts instead of hard-coded Python patterns.
- `content_kind_structure_rules`: config-driven structural rules with title regex, item regex, and minimum match count. A high-risk-vendor article with at least three list items becomes `domain_list`; a ranking/summary without a dominant list stays `advisory`.
- `title_include_patterns`: optional list-page title allowlist regexes. `tw_fsc_antifraud_press` uses it before fetching a detail page.
- `pagination`: source-specific pagination config. FSC uses `type=post_form`, configurable `page_field`, `first_page`, and bounded `max_pages`; Cofacts uses Relay `pageInfo.endCursor` when present, otherwise the current page's final edge cursor, and stops at its source-level `max_pages` (default 20). `pageInfo.lastCursor` is never a page cursor.
- `license`: human-auditable source licensing boundary. It does not grant the parser permission to fetch fields outside `fetch_scope`.

`tw_165_article_search` 的逐筆分類規則全部位於 `content_kind_patterns`：網站／網域清單是 `domain_list`；高風險業者、排名、統計、常見手法等彙整文章是 `advisory`。只有描述單一事件經過、且未命中彙整規則的內容沿用 `case_narrative`。

## Endpoint-Level Fields

Each endpoint may override source-level fields and may declare classification hints:

- `taxonomy_code`: controlled code from the five-category taxonomy.
- `source_category_label`: Traditional Chinese source label.
- `keywords`: Traditional Chinese keywords expected in the response.
- `drop_unclassified`, `min_classification_confidence`: endpoint-specific overrides for broad mixed-category resources.
- `require_taxonomy_keyword_match`: endpoint-specific override for search endpoints whose result pages may include records outside the query category.
- `expand_pdf_links`, `pdf_link_fields`, `pdf_max_pages`, `pdf_max_chars`, `pdf_timeout_seconds`: endpoint-specific overrides for bounded PDF text extraction.
- `parser_type`: endpoint-specific parser override.
- `headers`, `json`, `form`: endpoint-specific request headers, JSON body, or URL-encoded form body. Cofacts 的 GraphQL query 可讀 `articleReplies(status: NORMAL)`，但回應內容只能放在帶 CC BY-SA 4.0 授權標記的 metadata，不得混入主要 content 或題目種子。
- `fallback_json`: optional conservative GraphQL query. Cofacts 的主 query 若因 `pageInfo`／edge cursor／`replyRequestCount` schema 差異回傳 `errors`，會重試只含 `id`、`text`、`createdAt`、`lastRequestedAt` 的單頁 query；fallback 不宣稱可分頁，該批逐筆標為 `candidate`／`needs_review`，probe 也不會授予 verified。
- `timeout_seconds`, `probe_max_bytes`, `fetch_max_bytes`, `verify_tls`: endpoint-specific fetch controls.

Endpoint taxonomy is authoritative only for search endpoints whose query itself expresses the fraud category, such as 165 article-search endpoints. Otherwise, Codex must classify the record from fetched content and evidence.

## Script Behavior

- `probe_source.py` records endpoint success, truncation, parser type, and taxonomy hints.
- `fetch_source.py` writes classified JSONL using endpoint taxonomy first, then keyword rules.
- 所有文字欄位都經共用 `clean_text()` 移除 HTML、還原實體，並保留區塊元素的段落換行。
- 165 儀錶板的 `CaseStudy.Description` 會與標題組成純文字；多筆編號條列屬話術彙整，標為 `advisory`，不當作單一案例。
- fraudbuster 詳情只保留「內容摘要／內容摘錄」後、設定的 `detail_end_patterns` 前之詐騙貼文原文，移除「展開更多內容／處理進度／時間戳」，並標為 `message_sample`。
- fraudbuster 以清單列的案件分類圖片 `alt` 為主要 taxonomy 訊號，排除平台與裝飾圖片；案件狀態決定 `case_stance`、人工複核旗標或丟棄理由。空白、少於 `min_message_chars`、命中 `message_placeholder_patterns`，以及 Threads 個人檔案 meta description 的內容都計為 `no_message_body`，不計入 `unclassified`；有真實訊息但不屬五分類者以 nullable taxonomy 保留。`高風險訊息，請謹慎評估`、`疑似詐騙訊息` 等未經官方確認的紀錄，固定在輸出頂層 `metadata.review_required=true`，原始狀態則位於 `metadata.source_case_status`。只有已確認狀態且沒有 `review_required` 的紀錄可以直接作為詐騙題素材；所有 `review_required` 紀錄即使內容看似詐騙，也必須先人工複核。
- Cofacts 解析器以 GraphQL cursor 分頁，只把 `pageInfo.endCursor`（若存在）或本頁最後一個 edge `cursor` 當成下一頁游標，絕不使用代表整份結果集尾端的 `pageInfo.lastCursor`；容許 `pageInfo`、edge `cursor`、`replyRequestCount` 缺欄。schema 不接受選填欄位時改用保守 fallback query，只讀 `node.text`。訊息會移除常見手機 OCR 狀態列雜訊，套用 40–1500 字、OCR 清理後長度、網址密度、taxonomy 與內容雜湊過濾；`tw_cofacts_scam_messages` 已由上游 scam category 與 `RUMOR` 過濾，無法對應五分類時以 nullable taxonomy 保留。首次抓取直到過濾後達 `max_records` 或達 `max_pages`，摘要列出各丟棄原因。後續頁失敗時保留先前成功頁的資料，但整批降為 `candidate`／`needs_review`，並在 `pagination_errors` 回報錯誤，不可當成完整 verified 批次。`NOT_RUMOR` 來源全部是 `advisory`，並帶 `metadata.candidate_for='legit_lookalike'` 與 `metadata.review_required=true`，不得自動視為 legit。`plan_crawl.py` 從 staging 取該來源最新的 `lastRequestedAt`／`createdAt`，並收集該 checkpoint 時間已入庫的 article IDs，在 item 輸出 `--since` 與可重複的 `--known-id`；操作者須把整組 `fetch_args` 傳給 `fetch_source.py`。抓取器會跳過同時間已見 ID、保留同時間的新 ID，直到遇到更舊的排序結果才停止。帶 `--since` 的增量抓取為避免 burst 漏資料，會跨過舊 checkpoint 才停止，但仍受 `max_pages` 保護。
- FSC 解析器以設定的 POST form 抓列表，將 `page_field` 逐頁遞增，排除固定側欄 dataserno 後套用 `title_include_patterns`，再以 `div.maincontent` 擷取內頁全文；列表分頁受 `pagination.max_pages` 限制。無法對應五分類的新聞稿以 nullable taxonomy 保留為 advisory。
- 司法院內頁以 `selectors.detail_content` 擷取完整巢狀元素；原始內頁 HTML 存於 `raw_payload.record.detail_html`。超過 20,000 字時，`body_text` 保留全文，`clean_text` 則將「犯罪事實」移到前段後截為 20,000 字，供策展與品質閘門使用。
- A fetched record is `valid` only when HTTP succeeded, text is non-empty, the response was not truncated, and classification confidence is above zero；例外是明確設定 `allow_unclassified_advisory` 的 advisory，或來源限定的 `allow_unclassified_message_sample`，可用 `taxonomy_code: null` 與 confidence 0 保留。
- If `drop_unclassified` is true, fetched records with no five-category evidence are skipped rather than emitted as invalid rows.
- Failed, parse-error, or truncated endpoint results are written as diagnostic `needs_review` / `candidate` rows with transport/error metadata and must not be applied.
- `ingest_jsonb.py --apply` still refuses unverified sources and non-valid records.

## Production Rule

Live source content can be applied only after:

1. source probe passes under the configured verification policy,
2. fetched JSONL validates against `schemas/scam_case.schema.json`,
3. the agent confirms the records are live-crawled, not synthetic,
4. the user or runbook explicitly uses `--apply`.
