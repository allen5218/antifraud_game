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

For multi-endpoint sources, do not require every endpoint to be healthy unless `verification_policy` is `all_endpoints`. Use endpoint-level results to decide which records are eligible for validation and ingest.
