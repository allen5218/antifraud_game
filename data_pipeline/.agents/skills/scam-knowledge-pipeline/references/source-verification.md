# Source Verification

Run source verification before any production ingest.

```bash
python scripts/probe_source.py --source tw_165_article_search --out data/probes/tw_165_article_search.json
```

Verification checks:

- endpoint returns a successful HTTP status,
- content type is expected,
- payload is non-empty,
- response is not truncated by the configured byte limit,
- source strategy is known,
- parser type is recorded in `references/sources.yaml`,
- public read-only access does not require login, captcha, or reporting workflows.

Unverified sources may be fetched for dry-run inspection only. They must not be ingested with `--apply`.

Store verification result with fetched/classified records as `source_verification_status: "verified"` before production apply.

新增來源在無外網 sandbox 中維持 `needs_probe`。請在可連外主機逐一執行：

```bash
cd data_pipeline/.agents/skills/scam-knowledge-pipeline
uv run python3 scripts/probe_source.py --source tw_cofacts_scam_messages --out data/probes/tw_cofacts_scam_messages.json
uv run python3 scripts/probe_source.py --source tw_cofacts_legit_lookalikes --out data/probes/tw_cofacts_legit_lookalikes.json
uv run python3 scripts/probe_source.py --source tw_fsc_antifraud_press --out data/probes/tw_fsc_antifraud_press.json
```

live capture 已確認 Cofacts 具有 edge `cursor`、`pageInfo.lastCursor` 與 `replyRequestCount`。`pageInfo.firstCursor`／`lastCursor` 是整份結果集的頭尾，不是本頁邊界；分頁只能採用本頁最後一個 edge `cursor`，若回應另有 Relay `pageInfo.endCursor` 才可優先採用。解析器在主 query schema error 時降級為不含選填欄位的單頁 query，probe 不會把 HTTP 200 的 GraphQL `errors` 或單頁 fallback 誤判成 verified。fallback 輸出只作 `candidate`／`needs_review`，並記錄只能取得前 50 筆、無 cursor 分頁，不可 production apply。FSC live capture 已確認列表為 URL-encoded POST form（`page`、`pagesize`、`keyword`），新聞稿全文 selector 為 `div.maincontent`；主機仍須確認多頁 POST 與現場內容持續相容。

Cofacts 授權邊界：使用者回報的原始訊息 `node.text` 是 CC0，作為 document 的主要 `body_text`／`clean_text`；社群查證回應屬 CC BY-SA 4.0，只能存於 `metadata.cofacts_replies` 作分類訊號與出處連結，並附 `attribution_required=true`、`verbatim_in_seed=false`。不得把 `articleReplies` 回應文字混入 document 主要 content 或遊戲題目種子檔。

For multi-endpoint sources, do not require every endpoint to be healthy unless `verification_policy` is `all_endpoints`. Use endpoint-level results to decide which records are eligible for validation and ingest.
