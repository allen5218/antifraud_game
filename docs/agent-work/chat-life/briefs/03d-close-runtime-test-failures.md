# Close runtime repair: exact independently observed failures

Continue implement-mu9b41qz-6ddb118b. Last worker ended network ERROR, no report. Read-only connectivity diagnosis just succeeded (OK); no auth changes needed. Retain current application changes and finish this small test/build repair before any04 gameplay work. Same repo and uv/bun/isolatedPG/noDocker/noDevDB/noCommit constraints.

Codex independently ran shared-event-loop probe after your sync endpoint change: now200/409, one persisted turn, pause200 cash0 XP0 hidden role, wrong-contact finale400. Preserve these gains.

Actual command `uv run pytest tests/integration/test_chat_life_pg.py -q` with explicit isolatedPG env: **6 failed,4 passed**. Fix exactly:
1. Missing imports ThreadPoolExecutor, asyncio, ScenarioReply in test file (NameError). Run the tests; don't just add assertions and claim success.
2. Fixture test_user comes from a closed Session; pg_session.refresh(test_user) fails InvalidRequestError. Fetch row by ID in the inspecting session (do not weaken wallet assertions or restore shared transaction lock problems). Applies purchase, judgment and pause cycle tests.
3. Fresh migration proof fails UndefinedTable user. Alembic env uses settings URL, ignoring cfg sqlalchemy.url; it migrates acceptanceDB while empty temporaryDB remains untouched. Provide explicit safe connection override handling in env.py or test scoped settings, verify exact target DB and NEVER default dev/prod. Test fresh upgrade+legacy row+upgrade head+downgrade/upgrade. Populate all required legacy columns. Dispose engine in finally before dropping only the explicit chat_life_mig_proof_* temporary DB. Don't mask original failure with cleanup ObjectInUse.
4. Frontend `npm exec --yes --package=bun -- bun run build` fails only line-channel.tsx58: sendMessage used before declaration (TS2448/2454). Inspect minimal declaration/use ordering fix; preserve latest user styling and other work, no global format. This is necessary build unblock, not redesign LINE. No real LINE calls.
5. New `_run_coroutine_sync` catches ANY exception and calls model again via asyncio.run. That duplicates generation on provider failure. Only bridge missing-context specifically if necessary, or use one supported bridge for sync endpoint; model exception must propagate once with rollback. Add focused call-count/failure test.

Also finish actual concurrent verify/judge idempotency and frontend request/retry/pause/result tests required by03; don't call sequential tests concurrent. New API/migration fields must be regenerated into SDK. Run full relevant backend unit/integration and frontend build/related tests. Record baseline unrelated failures honestly. Set PYTHONUTF8=1 for readable output. Python uses C:\Users\kun\Documents\ComfyUI\.venv\Scripts\uv.exe, bun via npm exec --yes --package=bun -- bun (do not scan whole drives).

Native PG17.11 127.0.0.1:55437 userchat_test databasechat_life_acceptance_20260919 verified active. Explicit POSTGRES_* env before imports, GOOGLE_API_KEY=your-gemini-api-key-here and no GEMINI_API_KEY for tests, router-only app no main lifespan. Existing migration test may have left an empty disposable DB; no need broad cleanup.

Write docs/agent-work/chat-life/runtime-repair-report.md with exact counts and commands when done; awaited test results, no pending background jobs. Clearly say branch/content/model hardening remains separate04 and unfinished. No blanket A1-A8 complete claim. Codex will rerun proof and inspect.
