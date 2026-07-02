# Playwright Crawling

Use Playwright CLI for source discovery, SPA/API inspection, dynamic-page fallback, and QA. Prefer HTTP/API/CSV/HTML ingestion when stable endpoints are available.

## Routing

This is the pipeline-specific Playwright guide. For the full command catalog, read `playwright-cli.md`.

Read these detailed Playwright CLI references only when the task needs them:

- `playwright-cli-running-code.md` for `run-code` extraction and page evaluation.
- `playwright-cli-element-attributes.md` for inspecting IDs, classes, ARIA labels, and computed styles.
- `playwright-cli-session-management.md` for named sessions and cleanup.
- `playwright-cli-storage-state.md` only when user-authorized state handling is required.
- `playwright-cli-tracing.md` and `playwright-cli-video-recording.md` for QA evidence.
- `playwright-cli-playwright-tests.md`, `playwright-cli-test-generation.md`, `playwright-cli-spec-driven-testing.md`, and `playwright-cli-request-mocking.md` only for test authoring; do not use request mocking for production crawl.

## Availability

Try:

```bash
playwright-cli --version
npx --no-install playwright-cli --version
```

Use the available command consistently. If both work, prefer `playwright-cli`.

## Minimal Inspection Flow

```bash
playwright-cli list
playwright-cli -s=scam-<source> open "https://example.com/"
playwright-cli -s=scam-<source> snapshot --filename=source-snapshot.yml
playwright-cli -s=scam-<source> --raw eval "document.title"
playwright-cli -s=scam-<source> --raw eval "location.href"
playwright-cli -s=scam-<source> --raw eval "el => el.innerText" "body"
playwright-cli -s=scam-<source> close
```

Use named sessions. Do not use `close-all` unless you first checked `playwright-cli list` and it is safe to close every session.

## SPA/API Discovery

For SPA sources such as `165.npa.gov.tw`, `165dashboard.tw`, and TPEX anti-fraud sites:

```bash
playwright-cli -s=scam-165 open "https://165.npa.gov.tw/#/"
playwright-cli -s=scam-165 requests
playwright-cli -s=scam-165 console
playwright-cli -s=scam-165 snapshot --depth=4
```

Prefer discovered API endpoints for repeatable ingest. Use Playwright fallback only when API/CSV/HTML fetch fails or page-only content is required.

## Extraction Fallback

Prefer scoped text over full body:

```bash
playwright-cli -s=scam-src --raw eval "el => el.innerText" "main"
playwright-cli -s=scam-src --raw eval "el => el.innerText" "article"
playwright-cli -s=scam-src run-code "async page => { await page.waitForLoadState('networkidle'); return await page.locator('article, main, body').first().innerText(); }"
```

Record fallback use in `extraction_notes`.

## Safety

- Quote all URLs.
- Avoid persistent profiles unless the user explicitly authorizes them.
- Do not save auth state into the skill package.
- Do not bypass captcha/login/rate limits.
- Do not use request mocking for production crawl.
