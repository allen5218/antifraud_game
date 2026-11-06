import { chromium } from "@playwright/test";
import { SQL } from "bun";
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const FRONTEND_URL = process.env.EVAL_FRONTEND_URL || "http://localhost:18173";
const API_URL = process.env.EVAL_API_URL || "http://host.docker.internal:21000";
const PHASE = process.argv[2] || "post-fix";
const OUT_DIR = process.env.EVAL_OUT_DIR || `/eval/${PHASE}`;
const SCREENSHOT_DIR = path.join(OUT_DIR, "screenshots");

fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

const db = new SQL(
  `postgres://postgres:${process.env.PGPASS}@db:5432/postgres`,
);

// ── Security / Redaction Filter ─────────────────────────────────────
const SENSITIVE_KEYS = new Set([
  "access_token",
  "refresh_token",
  "token",
  "password",
  "secret",
  "api_key",
  "apikey",
  "authorization",
]);

function sanitizePayload(obj, url = "") {
  if (url.includes("/login/access-token")) {
    return { redacted: true, token_type: "bearer" };
  }
  if (Array.isArray(obj)) return obj.map((item) => sanitizePayload(item, ""));
  if (obj && typeof obj === "object") {
    const out = {};
    for (const [k, v] of Object.entries(obj)) {
      if (SENSITIVE_KEYS.has(k.toLowerCase())) {
        out[k] = "[REDACTED]";
      } else {
        out[k] = sanitizePayload(v, "");
      }
    }
    return out;
  }
  if (typeof obj === "string") {
    let clean = obj.replace(/eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g, "[REDACTED_JWT]");
    if (process.env.PGPASS) clean = clean.replaceAll(process.env.PGPASS, "[REDACTED_SECRET]");
    return clean;
  }
  return obj;
}

// ── Hard Assertions, Checkpoints & Exact Rational Math ──────────────
const assertionsLog = [];
const checkpointState = {
  phase: PHASE,
  startedAt: new Date().toISOString(),
  lastCheckpointStage: "init",
  partA: null,
  partB: {},
  partC: null,
};

function writeCheckpoint(stageName) {
  checkpointState.lastCheckpointStage = stageName;
  checkpointState.updatedAt = new Date().toISOString();
  const payload = sanitizePayload({
    ...checkpointState,
    assertionsSummary: {
      totalAssertions: assertionsLog.length,
      passedAssertions: assertionsLog.filter((a) => a.passed).length,
      failedAssertions: assertionsLog.filter((a) => !a.passed).length,
    },
    assertionsLog,
  });
  const jsonStr = JSON.stringify(payload, null, 2);
  if (/eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/.test(jsonStr)) {
    throw new Error("SECURITY VIOLATION: Unredacted JWT detected in checkpoint JSON!");
  }
  const cpPath = path.join(OUT_DIR, `checkpoint-${PHASE}.json`);
  fs.writeFileSync(cpPath, jsonStr, "utf8");
}

function writeFailureReport(err) {
  const payload = sanitizePayload({
    status: "FAILED",
    phase: PHASE,
    failedAt: new Date().toISOString(),
    failedStage: checkpointState.lastCheckpointStage,
    errorMessage: String(err?.message || err),
    errorStack: String(err?.stack || ""),
    assertionsSummary: {
      totalAssertions: assertionsLog.length,
      passedAssertions: assertionsLog.filter((a) => a.passed).length,
      failedAssertions: assertionsLog.filter((a) => !a.passed).length,
    },
    completedData: {
      partA: checkpointState.partA,
      partB: checkpointState.partB,
      partC: checkpointState.partC,
    },
    assertionsLog,
  });
  const failPath = path.join(OUT_DIR, `evaluation-${PHASE}-failed.json`);
  fs.writeFileSync(failPath, JSON.stringify(payload, null, 2), "utf8");
  console.error(`FAILURE REPORT SAVED TO: ${failPath}`);
}

function assertCond(condition, code, message, details = {}) {
  const entry = {
    code,
    passed: Boolean(condition),
    message,
    details: sanitizePayload(details),
    timestamp: new Date().toISOString(),
  };
  assertionsLog.push(entry);
  if (!condition) {
    throw new Error(`[ASSERTION FAILED] ${code}: ${message} | ${JSON.stringify(entry.details)}`);
  }
}

const TRAINING_LEVEL_THRESHOLDS = [0, 100, 300, 600, 1000, 1500, 2200, 3000, 4000, 5500, 7500];
function computeTrainingLevel(xp) {
  let idx = 0;
  while (idx < TRAINING_LEVEL_THRESHOLDS.length && TRAINING_LEVEL_THRESHOLDS[idx] <= xp) {
    idx++;
  }
  return Math.max(1, idx);
}

function gcd(a, b) {
  let x = a < 0n ? -a : a;
  let y = b < 0n ? -b : b;
  while (y !== 0n) {
    const t = y;
    y = x % y;
    x = t;
  }
  return x === 0n ? 1n : x;
}

class BigRat {
  constructor(num, den = 1n) {
    const n = BigInt(num);
    const d = BigInt(den);
    const g = gcd(n, d);
    this.n = (d < 0n ? -n : n) / g;
    this.d = (d < 0n ? -d : d) / g;
  }
  mul(other) {
    return new BigRat(this.n * other.n, this.d * other.d);
  }
  floorMulInt(intVal) {
    const v = BigInt(intVal);
    return (v * this.n) / this.d;
  }
  static fromDecimalStr(str) {
    const s = String(str).trim();
    if (!s.includes(".")) return new BigRat(BigInt(s), 1n);
    const [intPart, fracPart] = s.split(".");
    const scale = 10n ** BigInt(fracPart.length);
    return new BigRat(BigInt(intPart + fracPart), scale);
  }
}

function computeExactRewards({
  coreLevel,
  activeItems,
  petLevel,
  bestStreak,
  baseCash,
  baseXp,
}) {
  let mCore = new BigRat(1n, 1n);
  for (let i = 0; i < coreLevel; i++) {
    mCore = mCore.mul(new BigRat(6n, 5n));
  }
  const mPet = new BigRat(BigInt(100 + Math.min(petLevel, 100)), 100n);
  const mSet =
    activeItems.length >= 6
      ? new BigRat(15n, 10n)
      : activeItems.length >= 3
        ? new BigRat(11n, 10n)
        : new BigRat(1n, 1n);

  let toolCash = new BigRat(1n, 1n);
  let toolXp = new BigRat(1n, 1n);
  let toolEnergy = new BigRat(1n, 1n);
  const seenFamilies = new Set();

  for (const item of activeItems) {
    if (seenFamilies.has(item.family)) continue;
    seenFamilies.add(item.family);
    const r = BigInt(item.rank);
    if (item.family === "save_vault") {
      toolCash = toolCash.mul(new BigRat(10n + r, 10n));
    } else if (item.family === "growth_lens") {
      toolXp = toolXp.mul(new BigRat(10n + r, 10n));
    } else if (item.family === "forge_hammer") {
      toolEnergy = toolEnergy.mul(new BigRat(10n + r, 10n));
    } else if (item.family === "balance_core") {
      const f = new BigRat(20n + r, 20n);
      toolCash = toolCash.mul(f);
      toolXp = toolXp.mul(f);
      toolEnergy = toolEnergy.mul(f);
    } else if (item.family === "streak_amplifier" && bestStreak >= 3) {
      const f = new BigRat(50n + 3n * r, 50n);
      toolCash = toolCash.mul(f);
      toolXp = toolXp.mul(f);
      toolEnergy = toolEnergy.mul(f);
    }
  }

  const totalCashFactor = mCore.mul(toolCash).mul(mPet).mul(mSet);
  const totalXpFactor = mCore.mul(toolXp).mul(mPet).mul(mSet);
  const totalEnergyFactor = mCore.mul(toolEnergy).mul(mPet).mul(mSet);

  const expectedCashTotal = totalCashFactor.floorMulInt(baseCash);
  const expectedCashBonus = expectedCashTotal - BigInt(baseCash);
  const expectedGrowthXp = totalXpFactor.floorMulInt(baseXp);
  const expectedEnergy = totalEnergyFactor.floorMulInt(baseXp);

  return {
    cashTotal: expectedCashTotal,
    cashBonus: expectedCashBonus,
    growthXp: expectedGrowthXp,
    forgeEnergy: expectedEnergy,
  };
}

function verifyExactMultiplierSettlement({
  coreLevel,
  activeItems,
  petLevel,
  bestStreak,
  baseCash,
  baseXp,
  receipt,
}) {
  const {
    cashTotal: expectedCashTotal,
    cashBonus: expectedCashBonus,
    growthXp: expectedGrowthXp,
    forgeEnergy: expectedEnergy,
  } = computeExactRewards({
    coreLevel,
    activeItems,
    petLevel,
    bestStreak,
    baseCash,
    baseXp,
  });

  assertCond(
    BigInt(receipt.final.cash_total) === expectedCashTotal,
    "MATH_CASH_TOTAL",
    "Receipt cash_total matches exact rational floor(base_cash * M_c)",
    { actual: receipt.final.cash_total, expected: expectedCashTotal.toString() },
  );
  assertCond(
    BigInt(receipt.final.cash_bonus) === expectedCashBonus,
    "MATH_CASH_BONUS",
    "Receipt cash_bonus matches exact rational cash_total - base_cash",
    { actual: receipt.final.cash_bonus, expected: expectedCashBonus.toString() },
  );
  assertCond(
    BigInt(receipt.final.growth_xp) === expectedGrowthXp,
    "MATH_GROWTH_XP",
    "Receipt growth_xp matches exact rational floor(base_xp * M_x)",
    { actual: receipt.final.growth_xp, expected: expectedGrowthXp.toString() },
  );
  assertCond(
    BigInt(receipt.final.forge_energy) === expectedEnergy,
    "MATH_FORGE_ENERGY",
    "Receipt forge_energy matches exact rational floor(base_xp * M_p)",
    { actual: receipt.final.forge_energy, expected: expectedEnergy.toString() },
  );
}

// ── Read-Only DB Helpers ────────────────────────────────────────────
async function runSql(sql) {
  const rows = await db.unsafe(sql);
  return Array.from(rows);
}

async function queryPlayerDbState(userId) {
  const userRows = await runSql(`
    SELECT id, email, cash::text AS cash, xp, streak_days
    FROM "user"
    WHERE id = '${userId}'
  `);
  const growthRows = await runSql(`
    SELECT user_id, core_level, growth_xp::text AS growth_xp, forge_energy::text AS forge_energy, lifetime_cash::text AS lifetime_cash, revision, config_version
    FROM player_growth
    WHERE user_id = '${userId}'
  `);
  const equipRows = await runSql(`
    SELECT id, definition_id, rank, rank_cap
    FROM player_equipment
    WHERE user_id = '${userId}'
    ORDER BY definition_id
  `);
  const loadoutRows = await runSql(`
    SELECT l.slot_index, l.item_id, l.family, e.rank
    FROM equipment_loadout l
    JOIN player_equipment e ON e.id = l.item_id
    WHERE l.user_id = '${userId}'
    ORDER BY l.slot_index
  `);
  const unlockRows = await runSql(`
    SELECT unlock_key, value
    FROM player_unlock
    WHERE user_id = '${userId}'
    ORDER BY unlock_key
  `);
  const collectionRows = await runSql(`
    SELECT kind, target_id, level
    FROM collection_growth
    WHERE user_id = '${userId}'
    ORDER BY kind, target_id
  `);
  const receiptRows = await runSql(`
    SELECT id, source_key, base_rewards, factors, final_rewards, core_level_before, core_level_after, state, created_at
    FROM reward_receipt
    WHERE user_id = '${userId}'
    ORDER BY created_at DESC
    LIMIT 10
  `);
  const ledgerRows = await runSql(`
    SELECT id, event_key, kind, amounts, balance_after, receipt_id, created_at
    FROM progression_ledger
    WHERE user_id = '${userId}'
    ORDER BY created_at DESC
    LIMIT 15
  `);
  const practiceProfileRows = await runSql(`
    SELECT weights, focus_type, updated_at
    FROM practice_profile
    WHERE user_id = '${userId}'
  `);
  const practiceAnswerCount = await runSql(`
    SELECT count(*)::int AS cnt
    FROM practice_answer
    WHERE user_id = '${userId}'
  `);
  const receiptCount = await runSql(`
    SELECT count(*)::int AS cnt
    FROM reward_receipt
    WHERE user_id = '${userId}'
  `);
  return {
    user: userRows[0] || null,
    growth: growthRows[0] || null,
    equipment: equipRows,
    loadout: loadoutRows,
    unlocks: unlockRows,
    collections: collectionRows,
    recent_receipts: receiptRows,
    recent_ledgers: ledgerRows,
    practice_profile: practiceProfileRows[0] || null,
    practice_answer_count: practiceAnswerCount[0]?.cnt ?? 0,
    total_receipt_count: receiptCount[0]?.cnt ?? 0,
  };
}

async function queryQuizStoredItems(sessionId) {
  const rows = await runSql(`
    SELECT id, user_id, completed, items, answers
    FROM quiz_session
    WHERE id = '${sessionId}'
  `);
  const ctxRows = await runSql(`
    SELECT id, source_kind, source_id, core_level, equipment_snapshot, factor_snapshot, config_version
    FROM reward_context
    WHERE source_kind = 'quiz' AND source_id = '${sessionId}'
  `);
  return {
    quiz_session: rows[0] || null,
    reward_context: ctxRows[0] || null,
  };
}

async function createNormalUser(tag) {
  const rand = crypto.randomBytes(4).toString("hex");
  const email = `eval-${PHASE}-${tag}-${rand}@example.com`;
  const password = `EvalPass!${rand}99`;
  const res = await fetch(`${API_URL}/api/v1/private/users/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      password,
      full_name: `Eval_${tag}`,
      is_verified: true,
    }),
  });
  if (!res.ok) {
    throw new Error(`Failed to create user: ${res.status} ${await res.text()}`);
  }
  const user = await res.json();
  return { id: user.id, email, password, full_name: `Eval_${tag}` };
}

function countQuestionChars(item) {
  let text = (item.title || "") + (item.narrative || "") + (item.question || "");
  if (item.options) {
    for (const o of item.options) text += o.text || o.label || "";
  }
  if (item.match_prompts) {
    for (const p of item.match_prompts) text += p.text || "";
  }
  if (item.match_targets) {
    for (const t of item.match_targets) text += t.label || "";
  }
  return text.length;
}

/**
 * Answer a single quiz question via real Playwright UI clicks, measuring pure API latency vs UI action time.
 */
async function requestDurationMs(response) {
  await response.finished();
  const timing = response.request().timing();
  return Math.max(0, timing.responseEnd >= 0 ? timing.responseEnd : timing.responseStart);
}

async function answerQuestionOnPage(page, publicItem, storedItem, wantCorrect) {
  const type = publicItem.type;
  const uiStart = performance.now();

  if (type === "verdict") {
    const isScam = Boolean(storedItem.is_scam);
    const chooseScam = wantCorrect ? isScam : !isScam;
    const btnName = chooseScam ? "這是詐騙" : "這是正常的";
    const ansPromise = page.waitForResponse(
      (r) => r.url().includes("/api/v1/quick/quiz/answer") && r.request().method() === "POST",
    );
    await page.getByRole("button", { name: btnName, exact: true }).click();
    const res = await ansPromise;
    const apiMs = await requestDurationMs(res);
    assertCond(res.status() === 200, "QUIZ_ANSWER_STATUS", "Quiz answer returned 200", {
      status: res.status(),
      type,
    });
    return { uiMs: Math.max(0, performance.now() - uiStart - apiMs), apiMs };
  }

  const sendBtn = page.getByRole("button", { name: "送出答案", exact: true });

  if (type === "verification") {
    await sendBtn.waitFor({ state: "visible" });
    const correctKey = storedItem.correct_key;
    const targetOption = wantCorrect
      ? publicItem.options.find((o) => o.key === correctKey)
      : publicItem.options.find((o) => o.key !== correctKey);
    await page.getByText(targetOption.text, { exact: true }).click();
  } else if (type === "tactics") {
    await sendBtn.waitFor({ state: "visible" });
    const correctTags = new Set(storedItem.correct_tags || []);
    if (wantCorrect) {
      for (const opt of publicItem.options) {
        if (correctTags.has(opt.tag)) {
          await page.getByRole("checkbox", { name: opt.label, exact: true }).check();
        }
      }
    } else {
      const wrongOpt = publicItem.options.find((o) => !correctTags.has(o.tag));
      if (wrongOpt) {
        await page.getByRole("checkbox", { name: wrongOpt.label, exact: true }).check();
      } else if (publicItem.options.length > 0 && correctTags.size > 1) {
        await page
          .getByRole("checkbox", { name: publicItem.options[0].label, exact: true })
          .check();
      }
    }
  } else if (type === "match") {
    await sendBtn.waitFor({ state: "visible" });
    const correctMap = new Map(
      (storedItem.pairs || []).map((p) => [p.pair_id, p.tag]),
    );
    const targetLabelByTag = new Map(
      publicItem.match_targets.map((t) => [t.tag, t.label]),
    );
    const prompts = publicItem.match_prompts;
    for (let i = 0; i < prompts.length; i++) {
      const p = prompts[i];
      await page
        .getByRole("button", { name: `${i + 1}.${p.text}`, exact: true })
        .click();
      let tagToPick = correctMap.get(p.pair_id);
      if (!wantCorrect) {
        const nextPrompt = prompts[(i + 1) % prompts.length];
        tagToPick = correctMap.get(nextPrompt.pair_id);
      }
      const label = targetLabelByTag.get(tagToPick);
      await page.getByRole("button", { name: label, exact: true }).click();
    }
  }

  const ansPromise = page.waitForResponse(
    (r) => r.url().includes("/api/v1/quick/quiz/answer") && r.request().method() === "POST",
  );
  await sendBtn.click();
  const res = await ansPromise;
  const apiMs = await requestDurationMs(res);
  assertCond(res.status() === 200, "QUIZ_ANSWER_STATUS", "Quiz answer returned 200", {
    status: res.status(),
    type,
  });
  return { uiMs: Math.max(0, performance.now() - uiStart - apiMs), apiMs };
}

/**
 * Validated progression actions: waits for real HTTP response, asserts 200 status,
 * verifies DB state & resource delta, and verifies updated UI text without fixed sleep.
 */
async function performValidatedToolUpgrade(page, userId, expectedRankAfter, expectedCost) {
  const dbBefore = await queryPlayerDbState(userId);
  const cashBefore = BigInt(dbBefore.user.cash);

  const upgBtn = page.getByRole("button", { name: /強化/ }).first();
  const isEnabled = await upgBtn.isEnabled();
  assertCond(isEnabled, "UPGRADE_BTN_ENABLED", "Upgrade button is enabled when affordable", {
    cashBefore: cashBefore.toString(),
    expectedCost: expectedCost.toString(),
  });

  const resPromise = page.waitForResponse(
    (r) => r.url().includes("/api/v1/equipment/") && r.url().includes("/upgrade") && r.request().method() === "POST",
  );
  await upgBtn.click();
  const res = await resPromise;
  assertCond(res.status() === 200, "UPGRADE_HTTP_200", "Equipment upgrade API returned 200", {
    status: res.status(),
  });
  const resBody = await res.json();
  assertCond(
    resBody.rank === expectedRankAfter,
    "UPGRADE_RESPONSE_RANK",
    `Upgrade response rank is ${expectedRankAfter}`,
    { rank: resBody.rank },
  );

  // Wait for UI to reflect new rank
  await page
    .getByText(`階級 ${expectedRankAfter} / 5`)
    .first()
    .waitFor({ state: "visible" });

  const dbAfter = await queryPlayerDbState(userId);
  const cashAfter = BigInt(dbAfter.user.cash);
  assertCond(
    cashBefore - cashAfter === BigInt(expectedCost),
    "UPGRADE_DB_CASH_DELTA",
    `DB cash decreased by exact upgrade cost ${expectedCost}`,
    { cashBefore: cashBefore.toString(), cashAfter: cashAfter.toString() },
  );
  const vaultRow = dbAfter.equipment.find((e) => e.definition_id === "save_vault");
  assertCond(
    vaultRow && vaultRow.rank === expectedRankAfter,
    "UPGRADE_DB_RANK",
    `DB save_vault rank is ${expectedRankAfter}`,
    { vaultRow },
  );
}

async function performValidatedUnlockAndEquipSecondTool(page, userId, familyKey, costEnergy) {
  const dbBefore = await queryPlayerDbState(userId);
  const energyBefore = BigInt(dbBefore.growth.forge_energy);

  const unlockBtn = page
    .getByRole("button", { name: new RegExp(`解鎖 \\(${costEnergy} 能量\\)`) })
    .first();
  const isEnabled = await unlockBtn.isEnabled();
  assertCond(isEnabled, "UNLOCK_BTN_ENABLED", "Unlock tool family button is enabled when energy >= cost", {
    energyBefore: energyBefore.toString(),
    costEnergy: costEnergy.toString(),
  });

  const unlockPromise = page.waitForResponse(
    (r) => r.url().includes(`/api/v1/progression/unlocks/${familyKey}`) && r.request().method() === "POST",
  );
  await unlockBtn.click();
  const unlockRes = await unlockPromise;
  assertCond(unlockRes.status() === 200, "UNLOCK_HTTP_200", "Unlock tool family API returned 200", {
    status: unlockRes.status(),
  });

  // Wait for the newly unlocked tool's "裝備" button to appear in inventory
  const equipNewBtn = page.getByRole("button", { name: "裝備", exact: true }).first();
  await equipNewBtn.waitFor({ state: "visible" });

  const dbAfterUnlock = await queryPlayerDbState(userId);
  const energyAfter = BigInt(dbAfterUnlock.growth.forge_energy);
  assertCond(
    energyBefore - energyAfter === BigInt(costEnergy),
    "UNLOCK_DB_ENERGY_DELTA",
    `DB forge_energy decreased by ${costEnergy}`,
    { energyBefore: energyBefore.toString(), energyAfter: energyAfter.toString() },
  );
  assertCond(
    dbAfterUnlock.equipment.some((e) => e.definition_id === familyKey),
    "UNLOCK_DB_EQUIPMENT_ROW",
    `DB player_equipment has ${familyKey}`,
    { equipment: dbAfterUnlock.equipment },
  );

  // Now equip into Slot #2
  const loadoutPromise = page.waitForResponse(
    (r) => r.url().includes("/api/v1/equipment/loadout") && r.request().method() === "PUT",
  );
  await equipNewBtn.click();
  const loadoutRes = await loadoutPromise;
  assertCond(loadoutRes.status() === 200, "EQUIP_SLOT2_HTTP_200", "Loadout update for slot 2 returned 200", {
    status: loadoutRes.status(),
  });
  await page.getByText("容量 2 / 2 槽").waitFor({ state: "visible" });

  const dbAfterEquip = await queryPlayerDbState(userId);
  assertCond(
    dbAfterEquip.loadout.length === 2,
    "EQUIP_SLOT2_DB_COUNT",
    "DB equipment_loadout has 2 active items",
    { loadout: dbAfterEquip.loadout },
  );
}

async function performValidatedPetUpgrade(page, userId, expectedLevelAfter, cashCost, energyCost) {
  const dbBefore = await queryPlayerDbState(userId);
  const cashBefore = BigInt(dbBefore.user.cash);
  const energyBefore = BigInt(dbBefore.growth.forge_energy);

  const petBtn = page.getByRole("button", { name: /培養羈絆/ }).first();
  await petBtn.waitFor({ state: "visible" });
  const isEnabled = await petBtn.isEnabled();
  assertCond(isEnabled, "PET_UPGRADE_BTN_ENABLED", "Pet bond button is enabled when affordable", {
    cashBefore: cashBefore.toString(),
    energyBefore: energyBefore.toString(),
  });

  const petPromise = page.waitForResponse(
    (r) => r.url().includes("/api/v1/collections/pet/") && r.url().includes("/upgrade") && r.request().method() === "POST",
  );
  await petBtn.click();
  const petRes = await petPromise;
  assertCond(petRes.status() === 200, "PET_UPGRADE_HTTP_200", "Pet upgrade API returned 200", {
    status: petRes.status(),
  });

  await page.getByText(`${expectedLevelAfter} 級`).first().waitFor({ state: "visible" });

  const dbAfter = await queryPlayerDbState(userId);
  const cashAfter = BigInt(dbAfter.user.cash);
  const energyAfter = BigInt(dbAfter.growth.forge_energy);
  assertCond(
    cashBefore - cashAfter === BigInt(cashCost),
    "PET_UPGRADE_DB_CASH_DELTA",
    `DB cash decreased by ${cashCost}`,
    { cashBefore: cashBefore.toString(), cashAfter: cashAfter.toString() },
  );
  assertCond(
    energyBefore - energyAfter === BigInt(energyCost),
    "PET_UPGRADE_DB_ENERGY_DELTA",
    `DB forge_energy decreased by ${energyCost}`,
    { energyBefore: energyBefore.toString(), energyAfter: energyAfter.toString() },
  );
  assertCond(
    dbAfter.collections.some((c) => c.kind === "pet" && c.level === expectedLevelAfter),
    "PET_UPGRADE_DB_LEVEL",
    `DB collection_growth pet level is ${expectedLevelAfter}`,
    { collections: dbAfter.collections },
  );
}

// ── Part A: UI-to-Code Trace, Negative Probes & Dual-Viewport Screenshots ──
async function runPartAUiToCodeTrace(browser) {
  console.log("=== Running Part A: UI-to-Code Evidence Chain & Dual-Viewport Screenshots ===");
  const user = await createNormalUser("trace");
  const unexpectedConsoleErrors = [];
  const intentionalNegativeProbes = [];
  const pageErrors = [];
  const networkLog = [];
  let inNegativeProbe = false;

  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
  });
  const page = await context.newPage();

  page.on("console", (msg) => {
    if (msg.type() === "error" && !inNegativeProbe) {
      unexpectedConsoleErrors.push({ text: msg.text(), location: msg.location() });
    }
  });
  page.on("pageerror", (err) => {
    pageErrors.push(String(err));
  });
  page.on("response", async (res) => {
    const url = res.url();
    if (url.includes("/api/v1/")) {
      const cleanUrl = url.replace(/^https?:\/\/[^/]+/, "");
      let body = null;
      if (cleanUrl.includes("/login/access-token")) {
        body = { redacted: true, token_type: "bearer" };
      } else {
        try {
          const rawJson = await res.json();
          body = sanitizePayload(rawJson, cleanUrl);
        } catch {
          body = null;
        }
      }
      networkLog.push({
        timestamp: new Date().toISOString(),
        method: res.request().method(),
        url: cleanUrl,
        status: res.status(),
        body,
      });
    }
  });

  const steps = [];

  // Step 1: Login & Room
  await page.goto(`${FRONTEND_URL}/login`);
  await page.getByTestId("email-input").fill(user.email);
  await page.getByTestId("password-input").fill(user.password);
  await page.getByRole("button", { name: "登入" }).click();
  await page.waitForURL(`${FRONTEND_URL}/`);
  await page.getByTestId("home-hero").waitFor({ state: "visible" });
  await page.getByTestId("hdr-cash").filter({ hasText: "1,000" }).waitFor({ state: "visible" });

  const closeGuideBtn = page.getByRole("button", { name: /關閉|知道|開始/i }).first();
  if (await closeGuideBtn.isVisible().catch(() => false)) {
    await closeGuideBtn.click().catch(() => {});
  }

  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "01-room-mobile-390x844.png"),
  });
  const roomCashText = (await page.getByTestId("hdr-cash").innerText()).trim();
  const hasProgressionBtn = await page.getByTestId("room-progression").isVisible();

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "01-room-desktop-1280x900.png"),
  });
  await page.setViewportSize({ width: 390, height: 844 });

  const step1Db = await queryPlayerDbState(user.id);
  assertCond(step1Db.user.cash === "1000", "INIT_USER_CASH_1000", "New player starts with 1000 cash", {
    cash: step1Db.user.cash,
  });
  assertCond(step1Db.user.xp === 0, "INIT_USER_XP_0", "New player starts with 0 training XP", {
    xp: step1Db.user.xp,
  });
  assertCond(roomCashText === "1,000", "INIT_UI_CASH_1000", "Room header displays 1,000 cash", {
    roomCashText,
  });
  assertCond(hasProgressionBtn, "ROOM_HAS_PROGRESSION_BTN", "Room displays progression entry button");

  steps.push({
    step: "1_room_initial",
    ui: { url: page.url(), roomCashText, hasProgressionBtn },
    db: step1Db,
  });

  // Step 2: Navigate to /progression via room button (New player initial state & AC1 / AC4 checks)
  const progResponsePromise = page.waitForResponse(
    (r) => r.url().includes("/api/v1/progression/me") && r.request().method() === "GET",
  );
  await page.getByTestId("room-progression").click();
  await page.waitForURL(`${FRONTEND_URL}/progression`);
  await progResponsePromise;
  await page.getByText("核心養成階級").waitFor({ state: "visible" });
  await page.getByText("長期養成與榮譽").waitFor({ state: "visible" });

  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "02-progression-initial-mobile-390x844.png"),
  });
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "02-progression-initial-desktop-1280x900.png"),
  });
  await page.setViewportSize({ width: 390, height: 844 });

  const initialProgText = await page.locator("main").innerText();
  const equipBtn = page.getByRole("button", { name: "裝備", exact: true }).first();
  const equipBtnEnabled = await equipBtn.isEnabled();

  // AC1 Assertion: New player sees concrete near-term objective (equip starter tool / upgrade with $200 / XP gap to Lv.1), not ONLY distant Lv.10!
  assertCond(
    initialProgText.includes("近期目標") &&
      (initialProgText.includes("裝備初始工具") || initialProgText.includes("防禦金庫")) &&
      initialProgText.includes("Lv.1"),
    "AC1_NEAR_TERM_GOAL_VISIBLE",
    "Progression page shows actionable near-term goal (equip/upgrade starter tool + gap to Core Lv.1)",
    { excerpt: initialProgText.slice(0, 450) },
  );

  // AC4 Assertion: Unaffordable unlock & pet buttons are disabled upfront and show exact resource gap!
  const unlockLensBtn = page.getByRole("button", { name: /解鎖 \(100 能量\)/ }).first();
  const unlockLensDisabled = await unlockLensBtn.isDisabled();
  const petBondBtn = page.getByRole("button", { name: /培養羈絆/ }).first();
  const petBondDisabled = await petBondBtn.isDisabled();
  assertCond(
    unlockLensDisabled && initialProgText.includes("還差 100 能量"),
    "AC4_UNLOCK_DISABLED_WITH_GAP",
    "Second tool family unlock button is disabled at 0 energy and shows '還差 100 能量'",
    { unlockLensDisabled },
  );
  assertCond(
    petBondDisabled && initialProgText.includes("10 能量"),
    "AC4_PET_DISABLED_WITH_GAP",
    "Pet bond button is disabled at 0 energy and shows exact energy gap",
    { petBondDisabled },
  );

  const step2Db = await queryPlayerDbState(user.id);
  assertCond(
    step2Db.growth.core_level === 0 &&
      step2Db.growth.growth_xp === "0" &&
      step2Db.growth.forge_energy === "0",
    "INIT_GROWTH_DB_ZERO",
    "New player PlayerGrowth initialized at Lv.0, 0 GXP, 0 energy",
    { growth: step2Db.growth },
  );
  assertCond(
    step2Db.equipment.length === 1 &&
      step2Db.equipment[0].definition_id === "save_vault" &&
      step2Db.equipment[0].rank === 1,
    "INIT_STARTER_TOOL_DB",
    "New player owns Rank 1 save_vault in DB",
    { equipment: step2Db.equipment },
  );

  steps.push({
    step: "2_progression_initial",
    ui: {
      url: page.url(),
      equipBtnEnabled,
      unlockLensDisabled,
      petBondDisabled,
      pageTextExcerpt: initialProgText.slice(0, 900),
    },
    db: step2Db,
  });

  // Step 3: Equip starter tool & Upgrade starter tool from Rank 1 -> 2 ($200)
  const loadoutPromise = page.waitForResponse(
    (r) => r.url().includes("/api/v1/equipment/loadout") && r.request().method() === "PUT",
  );
  await equipBtn.click();
  const loadoutRes = await loadoutPromise;
  assertCond(loadoutRes.status() === 200, "EQUIP_STARTER_HTTP_200", "Equip starter tool returned 200");
  await page.getByRole("button", { name: "卸下", exact: true }).waitFor({ state: "visible" });

  const afterEquipDb = await queryPlayerDbState(user.id);
  assertCond(
    afterEquipDb.loadout.length === 1 && afterEquipDb.loadout[0].family === "save_vault",
    "EQUIP_STARTER_DB_SAVED",
    "Starter tool equipped in slot 0 in DB",
    { loadout: afterEquipDb.loadout },
  );

  await performValidatedToolUpgrade(page, user.id, 2, 200);

  // After upgrading to Rank 2, next upgrade to Rank 3 costs $1,200, while user has $800 cash -> button must now be disabled and show "還差 $400"!
  const upgradeRank3Btn = page.getByRole("button", { name: /強化 \(\$1,200\)/ }).first();
  await upgradeRank3Btn.waitFor({ state: "visible" });
  const upgradeRank3Disabled = await upgradeRank3Btn.isDisabled();
  const postUpgradeText = await page.locator("main").innerText();
  assertCond(
    upgradeRank3Disabled && postUpgradeText.includes("還差 $400"),
    "AC4_UPGRADE_RANK3_DISABLED_WITH_GAP",
    "Rank 2->3 upgrade button ($1,200) is disabled when cash is $800 and displays '還差 $400'",
    { upgradeRank3Disabled },
  );

  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "03-progression-equipped-upgraded-mobile-390x844.png"),
  });
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "03-progression-equipped-upgraded-desktop-1280x900.png"),
  });
  await page.setViewportSize({ width: 390, height: 844 });

  // Reload to verify persistence
  await page.reload();
  await page.getByText("核心養成階級").waitFor({ state: "visible" });
  const unequipCountAfterReload = await page.getByRole("button", { name: "卸下", exact: true }).count();
  const postEquipProgText = await page.locator("main").innerText();
  const afterUpgradeAndReloadDb = await queryPlayerDbState(user.id);

  assertCond(
    unequipCountAfterReload === 1 && postEquipProgText.includes("1.2x"),
    "RELOAD_PRESERVES_LOADOUT_AND_FACTOR",
    "Page reload preserves equipped Rank 2 tool and 1.2x cash multiplier",
    { unequipCountAfterReload },
  );

  steps.push({
    step: "3_equip_and_upgrade_starter_tool",
    ui: {
      unequipCountAfterReload,
      upgradeRank3Disabled,
      pageTextExcerpt: postEquipProgText.slice(0, 900),
    },
    afterEquipDb,
    afterUpgradeAndReloadDb,
  });

  // Step 4: Navigate to /quick/quiz via CTA on progression page & answer 5 questions
  const deckPromise = page.waitForResponse(
    (r) => r.url().includes("/api/v1/quick/quiz/deck") && r.request().method() === "GET",
  );
  await page.getByRole("link", { name: /繼續訓練/ }).click();
  await page.waitForURL(`${FRONTEND_URL}/quick/quiz`);
  const deckRes = await deckPromise;
  const deckData = await deckRes.json();
  const quizDbBefore = await queryQuizStoredItems(deckData.session_id);

  assertCond(
    quizDbBefore.reward_context?.factor_snapshot?.cash === "1.2",
    "REWARD_CONTEXT_FROZEN_AT_DEAL",
    "RewardContext froze 1.2x cash multiplier when quiz deck was dealt",
    { factor_snapshot: quizDbBefore.reward_context?.factor_snapshot },
  );

  // Verify public deck response does NOT leak answer keys (is_scam, correct_key, correct_tags)
  for (const pubItem of deckData.items) {
    assertCond(
      !("is_scam" in pubItem) && !("correct_key" in pubItem) && !("correct_tags" in pubItem),
      "PUBLIC_DECK_NO_ANSWER_LEAK",
      "Public quiz deck item does not leak answer fields before submission",
      { item_id: pubItem.item_id, type: pubItem.type },
    );
  }

  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "04-quiz-question-before-answer-mobile-390x844.png"),
  });
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "04-quiz-question-before-answer-desktop-1280x900.png"),
  });
  await page.setViewportSize({ width: 390, height: 844 });

  // Intentional Negative Probe #1: Mid-round loadout tampering
  // Unequip tool while session is open; settlement must STILL use the frozen 1.2x snapshot!
  const token = await page.evaluate(() => localStorage.getItem("access_token"));
  inNegativeProbe = true;
  await fetch(`${API_URL}/api/v1/equipment/loadout`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "X-ScamGym-Client-Version": "2",
    },
    body: JSON.stringify({ items: [] }),
  });
  inNegativeProbe = false;

  const storedByItemId = new Map(
    (quizDbBefore.quiz_session?.items || []).map((it) => [it.item_id, it]),
  );

  for (let i = 0; i < deckData.items.length; i++) {
    const pubItem = deckData.items[i];
    const stItem = storedByItemId.get(pubItem.item_id);
    await answerQuestionOnPage(page, pubItem, stItem, true);

    const nextBtnName = i === deckData.items.length - 1 ? "看結算" : "下一題";
    const nextBtn = page.getByRole("button", { name: nextBtnName, exact: true });
    await nextBtn.waitFor({ state: "visible" });

    if (i === 0) {
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, "05-quiz-reveal-mobile-390x844.png"),
      });
      await page.setViewportSize({ width: 1280, height: 900 });
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, "05-quiz-reveal-desktop-1280x900.png"),
      });
      await page.setViewportSize({ width: 390, height: 844 });
    }

    if (i < deckData.items.length - 1) {
      await nextBtn.click();
    }
  }

  // Step 5: Settlement screen & AC3 / AC5 / AC8 assertions
  const completePromise = page.waitForResponse(
    (r) => r.url().includes("/api/v1/quick/quiz/complete") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "看結算", exact: true }).click();
  const completeRes = await completePromise;
  assertCond(completeRes.status() === 200, "QUIZ_COMPLETE_200", "Quiz complete returned 200");
  const completeData = await completeRes.json();
  await page.getByText("倍率加成結算").waitFor({ state: "visible" });

  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "06-quiz-settlement-mobile-390x844.png"),
  });
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "06-quiz-settlement-desktop-1280x900.png"),
  });
  await page.setViewportSize({ width: 390, height: 844 });

  // Verify mid-round snapshot immutability
  assertCond(
    completeData.reward_receipt?.factors?.cash === "1.2" &&
      completeData.cash_earned === "264",
    "MID_ROUND_SNAPSHOT_IMMUTABLE",
    "Mid-round loadout change did NOT alter active session's frozen 1.2x multiplier",
    {
      factors: completeData.reward_receipt?.factors,
      cash_earned: completeData.cash_earned,
    },
  );
  intentionalNegativeProbes.push({
    probe: "mid_round_loadout_unequip",
    expected: "Active quiz session keeps frozen 1.2x cash multiplier",
    actualFactorUsed: completeData.reward_receipt?.factors?.cash,
    passed: true,
  });

  // Re-equip starter tool after probe
  const starterItemId = afterEquipDb.equipment[0]?.id;
  await fetch(`${API_URL}/api/v1/equipment/loadout`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "X-ScamGym-Client-Version": "2",
    },
    body: JSON.stringify({ items: [{ slot_index: 0, item_id: starterItemId }] }),
  });

  const receiptToggle = page.getByRole("button", { name: /收據 #/ });
  if (await receiptToggle.isVisible().catch(() => false)) {
    await receiptToggle.click();
  }
  const settlementText = await page.locator("main").innerText();
  const settlementLinks = await page.locator("main a, main button").allInnerTexts();

  // AC3 Assertion: Settlement screen displays this round's growth AND a working progression next-step entry!
  const progLinkOnSettlement = page.getByRole("link", { name: /前往養成與配裝/ });
  const progLinkVisible = await progLinkOnSettlement.isVisible();
  assertCond(
    progLinkVisible &&
      settlementText.includes("+100 養成經驗") &&
      settlementText.includes("+100 能量"),
    "AC3_SETTLEMENT_NEXT_STEP_VISIBLE",
    "Settlement screen shows earned growth XP/energy and a direct link to /progression",
    { settlementLinks },
  );

  // Intentional Negative Probe #2: Replay /quick/quiz/complete with same session_id
  const dbBeforeReplay = await queryPlayerDbState(user.id);
  inNegativeProbe = true;
  const replayRes = await fetch(`${API_URL}/api/v1/quick/quiz/complete`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "X-ScamGym-Client-Version": "2",
    },
    body: JSON.stringify({ session_id: deckData.session_id }),
  });
  const replayBody = await replayRes.json().catch(() => null);
  inNegativeProbe = false;
  const dbAfterReplay = await queryPlayerDbState(user.id);

  assertCond(
    replayRes.status === 400 &&
      replayBody?.detail?.code === "quiz_already_completed" &&
      dbAfterReplay.user.cash === dbBeforeReplay.user.cash &&
      dbAfterReplay.growth.growth_xp === dbBeforeReplay.growth.growth_xp &&
      dbAfterReplay.total_receipt_count === 1,
    "REPLAY_COMPLETE_REJECTED_NO_DOUBLE_PAY",
    "Re-submitting quiz/complete returns 400 quiz_already_completed, leaves balances unchanged, and creates only 1 receipt",
    {
      status: replayRes.status,
      code: replayBody?.detail?.code,
      cashBefore: dbBeforeReplay.user.cash,
      cashAfter: dbAfterReplay.user.cash,
      receiptCount: dbAfterReplay.total_receipt_count,
    },
  );
  intentionalNegativeProbes.push({
    probe: "replay_quiz_complete",
    status: replayRes.status,
    code: replayBody?.detail?.code,
    cashUnchanged: dbAfterReplay.user.cash === dbBeforeReplay.user.cash,
    receiptCount: dbAfterReplay.total_receipt_count,
    passed: true,
  });

  // Intentional Negative Probe #3: Insufficient resource API calls (upgrade rank 2->3 costs $1200 when cash=$1064; unlock forge_hammer costs 300 energy when energy=100)
  inNegativeProbe = true;
  const insuffUpgRes = await fetch(
    `${API_URL}/api/v1/equipment/${starterItemId}/upgrade`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        "X-ScamGym-Client-Version": "2",
        "X-Idempotency-Key": crypto.randomUUID(),
      },
    },
  );
  const insuffUpgBody = await insuffUpgRes.json().catch(() => null);

  const insuffUnlockRes = await fetch(
    `${API_URL}/api/v1/progression/unlocks/forge_hammer`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        "X-ScamGym-Client-Version": "2",
      },
    },
  );
  const insuffUnlockBody = await insuffUnlockRes.json().catch(() => null);
  inNegativeProbe = false;

  const dbAfterInsuff = await queryPlayerDbState(user.id);
  assertCond(
    insuffUpgRes.status === 400 &&
      insuffUpgBody?.detail?.code === "insufficient_cash" &&
      insuffUnlockRes.status === 400 &&
      insuffUnlockBody?.detail?.code === "insufficient_energy" &&
      dbAfterInsuff.user.cash === dbBeforeReplay.user.cash &&
      dbAfterInsuff.growth.forge_energy === dbBeforeReplay.growth.forge_energy,
    "INSUFFICIENT_RESOURCE_REJECTED_CLEANLY",
    "Insufficient cash/energy API probes return 400 with exact error codes and zero resource mutation",
    {
      insuffUpgCode: insuffUpgBody?.detail?.code,
      insuffUnlockCode: insuffUnlockBody?.detail?.code,
    },
  );
  intentionalNegativeProbes.push({
    probe: "insufficient_cash_and_energy_api",
    upgradeStatus: insuffUpgRes.status,
    upgradeCode: insuffUpgBody?.detail?.code,
    unlockStatus: insuffUnlockRes.status,
    unlockCode: insuffUnlockBody?.detail?.code,
    balancesUnchanged: true,
    passed: true,
  });

  steps.push({
    step: "4_and_5_quiz_round_and_settlement",
    sessionId: deckData.session_id,
    quizDbBefore,
    completeResponse: completeData,
    ui: { settlementText, settlementLinks },
    dbAfterSettlement: dbAfterInsuff,
  });

  // Step 6: Play Again ("再來一輪") button verification
  const nextDeckPromise = page.waitForResponse(
    (r) => r.url().includes("/api/v1/quick/quiz/deck") && r.request().method() === "GET",
  );
  await page.getByRole("button", { name: "再來一輪" }).click();
  const nextDeckRes = await nextDeckPromise;
  const nextDeckData = await nextDeckRes.json();

  assertCond(
    nextDeckData.session_id !== deckData.session_id,
    "PLAY_AGAIN_NEW_SESSION_ID",
    "Clicking '再來一輪' issues a brand-new quiz session_id",
    { old: deckData.session_id, new: nextDeckData.session_id },
  );

  steps.push({
    step: "6_play_again_new_session",
    previousSessionId: deckData.session_id,
    newSessionId: nextDeckData.session_id,
    isDifferentSession: deckData.session_id !== nextDeckData.session_id,
  });

  // Step 7: Check Leaderboard (Daily / 14-day Season / Permanent Boards) & AC7 / AC8 assertions
  await page.goto(`${FRONTEND_URL}/leaderboard`);
  await page.getByText("競技排行榜").waitFor({ state: "visible" });
  await page.getByText("去訊息判讀升等").first().waitFor({ state: "visible" });
  const dailyTabText = await page.locator("main").innerText();
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "07-leaderboard-daily-mobile-390x844.png"),
  });

  await page.getByRole("tab", { name: "14天競技賽季" }).click();
  await page.getByText("參賽進度").waitFor({ state: "visible" });
  const seasonTabText = await page.locator("main").innerText();
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "08-leaderboard-season-mobile-390x844.png"),
  });
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "08-leaderboard-season-desktop-1280x900.png"),
  });
  await page.setViewportSize({ width: 390, height: 844 });

  await page.getByRole("tab", { name: "永久養成榜" }).click();
  await page.getByText("累積所得").waitFor({ state: "visible" });
  await page.getByText(/我的位置：第 \d+ 名 · 264 分/).waitFor({ state: "visible" });
  const permanentTabText = await page.locator("main").innerText();
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "09-leaderboard-permanent-mobile-390x844.png"),
  });
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "09-leaderboard-permanent-desktop-1280x900.png"),
  });
  await page.setViewportSize({ width: 390, height: 844 });

  assertCond(
    dailyTabText.includes("Lv.5 解鎖") &&
      dailyTabText.includes("還差 900 訓練 XP") &&
      dailyTabText.includes("去訊息判讀升等"),
    "AC7_DAILY_LOCKED_GUIDANCE",
    "Daily leaderboard tab explains Lv.5 requirement and exact 900 XP gap (1,000 - 100) with direct link to /quick/quiz",
    { dailyTabText },
  );
  assertCond(
    seasonTabText.includes("0／5 天") &&
      seasonTabText.includes("未入榜") &&
      seasonTabText.includes("去訊息判讀升等"),
    "AC7_SEASON_UNQUALIFIED_GUIDANCE",
    "Season leaderboard tab shows 0/5 days, '未入榜' (never Rank #1), and direct next-step link",
    { seasonTabText },
  );
  assertCond(
    /我的位置：第 \d+ 名 · 264 分/.test(permanentTabText),
    "AC7_PERMANENT_BOARD_SEPARATE",
    "Permanent wealth board tracks lifetime_cash (264) separately from season competition board",
    { permanentTabText },
  );

  // AC8 Assertion: Zero unexpected console errors or page errors across the entire normal user flow!
  assertCond(
    unexpectedConsoleErrors.length === 0 && pageErrors.length === 0,
    "AC8_ZERO_CONSOLE_OR_PAGE_ERRORS",
    "Zero unexpected console.error or unhandled pageerror events across normal gameplay flow",
    { unexpectedConsoleErrors, pageErrors },
  );

  steps.push({
    step: "7_leaderboard_views",
    ui: { dailyTabText, seasonTabText, permanentTabText },
  });

  await context.close();
  const partAResult = {
    user: { id: user.id, email: user.email },
    unexpectedConsoleErrors,
    pageErrors,
    intentionalNegativeProbes,
    steps,
    networkLogCount: networkLog.length,
    networkSample: networkLog.slice(0, 40),
  };
  checkpointState.partA = partAResult;
  writeCheckpoint("partA_complete");
  return partAResult;
}

// ── Part B: 3 Normal Players Growth Curve & Validated Milestones (10 rounds each) ──
async function runPartBThreePlayers(browser, maxRounds = 10) {
  console.log(`=== Running Part B: 3 Normal Players Growth Measurement (${maxRounds} rounds each) ===`);
  const profiles = [
    { key: "all_correct", label: "全對玩家 (100%)", pattern: (_r) => [true, true, true, true, true] },
    {
      key: "acc_70",
      label: "七成正確玩家 (70%)",
      pattern: (r) =>
        r % 2 === 1
          ? [true, true, true, true, false]
          : [true, true, true, false, false],
    },
    {
      key: "acc_40",
      label: "四成正確玩家 (40%)",
      pattern: (_r) => [true, true, false, false, false],
    },
  ];

  const results = {};

  for (const prof of profiles) {
    console.log(`  -> Starting profile: ${prof.label}`);
    const user = await createNormalUser(prof.key);
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await context.newPage();

    const consoleErrors = [];
    const pageErrors = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });
    page.on("pageerror", (err) => pageErrors.push(String(err)));

    await page.goto(`${FRONTEND_URL}/login`);
    await page.getByTestId("email-input").fill(user.email);
    await page.getByTestId("password-input").fill(user.password);
    await page.getByRole("button", { name: "登入" }).click();
    await page.waitForURL(`${FRONTEND_URL}/`);

    // Equip starter save_vault before Round 1 (verified via HTTP response + UI)
    await page.goto(`${FRONTEND_URL}/progression`);
    await page.getByText("核心養成階級").waitFor({ state: "visible" });
    const equipBtn = page.getByRole("button", { name: "裝備", exact: true }).first();
    const eqLoadoutPromise = page.waitForResponse(
      (r) => r.url().includes("/api/v1/equipment/loadout") && r.request().method() === "PUT",
    );
    await equipBtn.click();
    const eqRes = await eqLoadoutPromise;
    assertCond(eqRes.status() === 200, "PARTB_INIT_EQUIP_200", "Equipped starter save_vault before Round 1");
    await page.getByRole("button", { name: "卸下", exact: true }).waitFor({ state: "visible" });

    let expectedCash = 1000n;
    let expectedLifetimeCash = 0n;
    let expectedTrainingXp = 0;
    let expectedGrowthXp = 0n;
    let expectedEnergy = 0n;

    const roundsData = [];
    const milestones = {
      first_equip_round: 0,
      first_tool_upgrade_affordable_round: 0, // Starting $1,000 cash already affords $200 upgrade before Round 1
      first_tool_upgrade_executed_round: null,
      first_core_level_up_round: null,
      second_tool_unlock_round: null,
      third_tool_affordable_round: null,
      first_pet_upgrade_round: null,
      daily_unlocked_round: null,
    };

    for (let round = 1; round <= maxRounds; round++) {
      const roundStartMs = performance.now();
      let pureApiMs = 0;
      let uiActionMs = 0;
      let totalChars = 0;

      const dbStartRound = await queryPlayerDbState(user.id);
      const snapshotCoreLevel = dbStartRound.growth.core_level;
      const snapshotActiveItems = dbStartRound.loadout;
      const snapshotPetLevel =
        dbStartRound.collections.find((c) => c.kind === "pet")?.level ?? 0;

      const deckStart = performance.now();
      const deckPromise = page.waitForResponse(
        (r) => r.url().includes("/api/v1/quick/quiz/deck") && r.request().method() === "GET",
      );
      if (round === 1 || !page.url().includes("/quick/quiz")) {
        await page.goto(`${FRONTEND_URL}/quick/quiz`);
      } else {
        await page.getByRole("button", { name: "再來一輪" }).click();
      }
      const deckRes = await deckPromise;
      const deckApiMs = await requestDurationMs(deckRes);
      pureApiMs += deckApiMs;
      uiActionMs += Math.max(0, performance.now() - deckStart - deckApiMs);
      const deckData = await deckRes.json();

      const quizDb = await queryQuizStoredItems(deckData.session_id);
      const storedByItemId = new Map(
        (quizDb.quiz_session?.items || []).map((it) => [it.item_id, it]),
      );

      const wantFlags = prof.pattern(round);
      for (let i = 0; i < deckData.items.length; i++) {
        const pubItem = deckData.items[i];
        totalChars += countQuestionChars(pubItem);
        const stItem = storedByItemId.get(pubItem.item_id);
        const timing = await answerQuestionOnPage(
          page,
          pubItem,
          stItem,
          wantFlags[i] ?? false,
        );
        pureApiMs += timing.apiMs;
        uiActionMs += timing.uiMs;

        const nextBtnName = i === deckData.items.length - 1 ? "看結算" : "下一題";
        const nextBtn = page.getByRole("button", { name: nextBtnName, exact: true });
        await nextBtn.waitFor({ state: "visible" });
        if (i < deckData.items.length - 1) {
          await nextBtn.click();
        }
      }

      const compStart = performance.now();
      const completePromise = page.waitForResponse(
        (r) => r.url().includes("/api/v1/quick/quiz/complete") && r.request().method() === "POST",
      );
      await page.getByRole("button", { name: "看結算", exact: true }).click();
      const compRes = await completePromise;
      const completeApiMs = await requestDurationMs(compRes);
      pureApiMs += completeApiMs;
      uiActionMs += Math.max(0, performance.now() - compStart - completeApiMs);
      assertCond(compRes.status() === 200, "PARTB_COMPLETE_200", `Round ${round} complete 200`);
      const compData = await compRes.json();
      await page.getByText("倍率加成結算").waitFor({ state: "visible" });

      const roundTotalMs = performance.now() - roundStartMs;
      const receipt = compData.reward_receipt;

      // Exact rational verification of this round's multiplier settlement!
      const expectedBaseCash = Math.floor(
        40 * compData.correct_count * (1 + 0.1 * Math.floor(compData.best_streak / 3)),
      );
      const expectedBaseXp = 20 * compData.correct_count;
      assertCond(
        Number(receipt.base.cash) === expectedBaseCash &&
          Number(receipt.base.training_xp) === expectedBaseXp,
        "PARTB_BASE_REWARD_MATCH",
        `Round ${round} base cash/xp match formula`,
        { actualBase: receipt.base, expectedBaseCash, expectedBaseXp },
      );

      verifyExactMultiplierSettlement({
        coreLevel: snapshotCoreLevel,
        activeItems: snapshotActiveItems,
        petLevel: snapshotPetLevel,
        bestStreak: compData.best_streak,
        baseCash: expectedBaseCash,
        baseXp: expectedBaseXp,
        receipt,
      });

      expectedCash += BigInt(compData.cash_earned);
      expectedLifetimeCash += BigInt(compData.cash_earned);
      expectedTrainingXp += compData.xp_earned;
      expectedGrowthXp += BigInt(receipt.final.growth_xp);
      expectedEnergy += BigInt(receipt.final.forge_energy);

      const dbBeforeAction = await queryPlayerDbState(user.id);
      assertCond(
        BigInt(dbBeforeAction.user.cash) === expectedCash &&
          BigInt(dbBeforeAction.growth.lifetime_cash) === expectedLifetimeCash &&
          dbBeforeAction.user.xp === expectedTrainingXp &&
          BigInt(dbBeforeAction.growth.growth_xp) === expectedGrowthXp &&
          BigInt(dbBeforeAction.growth.forge_energy) === expectedEnergy,
        "PARTB_DB_RECONCILIATION_PRE_ACTION",
        `Round ${round} DB balances match exact cumulative ledger before actions`,
        {
          dbCash: dbBeforeAction.user.cash,
          expectedCash: expectedCash.toString(),
          dbGxp: dbBeforeAction.growth.growth_xp,
          expectedGxp: expectedGrowthXp.toString(),
          dbEnergy: dbBeforeAction.growth.forge_energy,
          expectedEnergy: expectedEnergy.toString(),
        },
      );

      const trainingLevelNow = computeTrainingLevel(dbBeforeAction.user.xp);
      const actionsTaken = [];
      const coreLevelNow = dbBeforeAction.growth.core_level;

      if (milestones.first_core_level_up_round === null && coreLevelNow >= 1) {
        milestones.first_core_level_up_round = round;
      }
      // Daily training unlocks strictly when training level >= 5 (1,000 training XP)
      if (milestones.daily_unlocked_round === null && trainingLevelNow >= 5) {
        milestones.daily_unlocked_round = round;
      }

      const needFirstUpgrade =
        milestones.first_tool_upgrade_executed_round === null && expectedCash >= 200n;
      const needSecondTool =
        milestones.second_tool_unlock_round === null && expectedEnergy >= 100n;
      const needFirstPet =
        milestones.first_pet_upgrade_round === null &&
        milestones.first_tool_upgrade_executed_round !== null &&
        expectedCash >= 500n &&
        expectedEnergy >= 10n;

      if (needFirstUpgrade || needSecondTool || needFirstPet) {
        // Navigate to /progression via the new settlement CTA link!
        await page.getByRole("link", { name: /前往養成與配裝/ }).click();
        await page.waitForURL(`${FRONTEND_URL}/progression`);
        await page.getByText("核心養成階級").waitFor({ state: "visible" });
        await page.getByText("長期養成與榮譽").waitFor({ state: "visible" });

        if (needFirstUpgrade) {
          await performValidatedToolUpgrade(page, user.id, 2, 200);
          expectedCash -= 200n;
          milestones.first_tool_upgrade_executed_round = round;
          actionsTaken.push("upgrade_save_vault_rank_2");
        }

        if (needSecondTool && expectedEnergy >= 100n) {
          await performValidatedUnlockAndEquipSecondTool(
            page,
            user.id,
            "growth_lens",
            100,
          );
          expectedEnergy -= 100n;
          milestones.second_tool_unlock_round = round;
          actionsTaken.push("unlock_growth_lens");
          actionsTaken.push("equip_growth_lens_slot_2");
        }

        if (
          milestones.first_pet_upgrade_round === null &&
          expectedCash >= 500n &&
          expectedEnergy >= 10n
        ) {
          await performValidatedPetUpgrade(page, user.id, 1, 500, 10);
          expectedCash -= 500n;
          expectedEnergy -= 10n;
          milestones.first_pet_upgrade_round = round;
          actionsTaken.push("upgrade_shiba_pet_level_1");
        }
      }

      if (milestones.third_tool_affordable_round === null && expectedEnergy >= 300n) {
        milestones.third_tool_affordable_round = round;
      }

      const dbAfter = await queryPlayerDbState(user.id);
      assertCond(
        BigInt(dbAfter.user.cash) === expectedCash &&
          BigInt(dbAfter.growth.forge_energy) === expectedEnergy &&
          dbAfter.total_receipt_count === round,
        "PARTB_DB_RECONCILIATION_POST_ACTION",
        `Round ${round} DB balances and receipt count (${round}) match after actions`,
        {
          dbCash: dbAfter.user.cash,
          expectedCash: expectedCash.toString(),
          dbEnergy: dbAfter.growth.forge_energy,
          expectedEnergy: expectedEnergy.toString(),
          receiptCount: dbAfter.total_receipt_count,
        },
      );

      // Human reading time estimation under 3 explicit assumptions:
      // Fast reader (18 chars/sec + 3s decision/item), Medium reader (12 chars/sec + 4s/item), Careful reader (8 chars/sec + 6s/item)
      const nItems = deckData.items.length;
      const humanReadEstFastSec = Math.round(totalChars / 18 + nItems * 3);
      const humanReadEstMedSec = Math.round(totalChars / 12 + nItems * 4);
      const humanReadEstCarefulSec = Math.round(totalChars / 8 + nItems * 6);

      roundsData.push({
        round,
        session_id: deckData.session_id,
        correct_count: compData.correct_count,
        total: compData.total,
        best_streak: compData.best_streak,
        base_cash: receipt?.base?.cash ?? "0",
        base_training_xp: expectedBaseXp,
        cash_bonus: receipt?.final?.cash_bonus ?? "0",
        cash_earned: compData.cash_earned,
        training_xp_earned: compData.xp_earned,
        training_level_after: trainingLevelNow,
        growth_xp_earned: receipt?.final?.growth_xp ?? "0",
        forge_energy_earned: receipt?.final?.forge_energy ?? "0",
        factors_used: receipt?.factors ?? {},
        snapshot_core_level: snapshotCoreLevel,
        snapshot_active_items: snapshotActiveItems,
        snapshot_pet_level: snapshotPetLevel,
        core_level_before: receipt?.core_level_before ?? 0,
        core_level_after: dbAfter.growth.core_level,
        cumulative_cash: dbAfter.user.cash,
        cumulative_lifetime_cash: dbAfter.growth.lifetime_cash,
        cumulative_training_xp: dbAfter.user.xp,
        cumulative_growth_xp: dbAfter.growth.growth_xp,
        cumulative_forge_energy: dbAfter.growth.forge_energy,
        equipped_items: dbAfter.loadout,
        equipment_ranks: dbAfter.equipment,
        collections: dbAfter.collections,
        actions_taken: actionsTaken,
        question_chars: totalChars,
        human_read_est_fast_sec: humanReadEstFastSec,
        human_read_est_med_sec: humanReadEstMedSec,
        human_read_est_careful_sec: humanReadEstCarefulSec,
        script_round_ms: Math.round(roundTotalMs),
        ui_action_ms: Math.round(uiActionMs),
        pure_api_ms: Math.round(pureApiMs),
      });

      checkpointState.partB[prof.key] = {
        profile: prof.label,
        user: { id: user.id, email: user.email },
        milestones,
        completedRounds: round,
        rounds: roundsData,
      };
      writeCheckpoint(`partB_${prof.key}_round_${round}`);

      console.log(
        `    Round ${round}: ${compData.correct_count}/${compData.total} | +$${compData.cash_earned} | Cash=${dbAfter.user.cash} | TXP=${dbAfter.user.xp} (TLv.${trainingLevelNow}) | GXP=${dbAfter.growth.growth_xp} (CLv.${dbAfter.growth.core_level}) | Energy=${dbAfter.growth.forge_energy} | API=${Math.round(pureApiMs)}ms | Actions=${actionsTaken.join(",") || "none"}`,
      );
    }

    assertCond(
      consoleErrors.length === 0 && pageErrors.length === 0,
      `PARTB_NO_ERRORS_${prof.key.toUpperCase()}`,
      `Profile ${prof.key} completed ${maxRounds} rounds with zero console/page errors`,
      { consoleErrors, pageErrors },
    );

    await context.close();
    results[prof.key] = {
      profile: prof.label,
      user: { id: user.id, email: user.email },
      _credentialsForPartC: prof.key === "all_correct" ? user : undefined,
      milestones,
      consoleErrors,
      pageErrors,
      rounds: roundsData,
    };
  }

  return results;
}

// ── Part C: Data-Driven ROI Payback & Live Slot Tradeoff + Daily Qualification ──
function computeProfileRoiFromMeasuredRounds(profKey, profData) {
  const rounds = profData.rounds;
  // 1) Starter save_vault equip (Rank 1 vs unequipped), cost $0
  const equipPerRound = [];
  let equipCumDelta = 0n;
  for (const r of rounds) {
    const baseCash = Number(r.base_cash);
    const baseXp = Number(r.base_training_xp);
    const withVault = computeExactRewards({
      coreLevel: r.snapshot_core_level,
      activeItems: r.snapshot_active_items.map((item) =>
        item.family === "save_vault" ? { ...item, rank: 1 } : item,
      ),
      petLevel: r.snapshot_pet_level,
      bestStreak: r.best_streak,
      baseCash,
      baseXp,
    }).cashTotal;
    const withoutVault = computeExactRewards({
      coreLevel: r.snapshot_core_level,
      activeItems: r.snapshot_active_items.filter((it) => it.family !== "save_vault"),
      petLevel: r.snapshot_pet_level,
      bestStreak: r.best_streak,
      baseCash,
      baseXp,
    }).cashTotal;
    const delta = withVault - withoutVault;
    equipCumDelta += delta;
    equipPerRound.push({
      round: r.round,
      baseCash,
      coreLevel: r.snapshot_core_level,
      petLevel: r.snapshot_pet_level,
      withAction: withVault.toString(),
      withoutAction: withoutVault.toString(),
      deltaCash: delta.toString(),
      cumulativeDeltaCash: equipCumDelta.toString(),
    });
  }

  // 2) save_vault Rank 1 -> Rank 2 upgrade (cost $200, executed after Round 1, takes effect from Round 2)
  const upg1to2Cost = 200n;
  const upg1to2PerRound = [];
  let upg1to2CumDelta = 0n;
  let upg1to2PaybackRound = null;
  let upg1to2RoundsAfterUpgrade = 0;
  for (const r of rounds) {
    const hasRank2 = r.snapshot_active_items.some(
      (it) => it.family === "save_vault" && it.rank === 2,
    );
    if (!hasRank2) {
      upg1to2PerRound.push({
        round: r.round,
        activeInSnapshot: false,
        deltaCash: "0",
        cumulativeDeltaCash: upg1to2CumDelta.toString(),
      });
      continue;
    }
    upg1to2RoundsAfterUpgrade++;
    const baseCash = Number(r.base_cash);
    const baseXp = Number(r.base_training_xp);
    const withRank2 = computeExactRewards({
      coreLevel: r.snapshot_core_level,
      activeItems: r.snapshot_active_items,
      petLevel: r.snapshot_pet_level,
      bestStreak: r.best_streak,
      baseCash,
      baseXp,
    }).cashTotal;
    const withRank1 = computeExactRewards({
      coreLevel: r.snapshot_core_level,
      activeItems: r.snapshot_active_items.map((it) =>
        it.family === "save_vault" ? { ...it, rank: 1 } : it,
      ),
      petLevel: r.snapshot_pet_level,
      bestStreak: r.best_streak,
      baseCash,
      baseXp,
    }).cashTotal;
    const delta = withRank2 - withRank1;
    upg1to2CumDelta += delta;
    if (upg1to2PaybackRound === null && upg1to2CumDelta >= upg1to2Cost) {
      upg1to2PaybackRound = {
        absoluteRound: r.round,
        roundsSinceUpgrade: upg1to2RoundsAfterUpgrade,
        cumulativeExtraCash: upg1to2CumDelta.toString(),
      };
    }
    upg1to2PerRound.push({
      round: r.round,
      activeInSnapshot: true,
      baseCash,
      coreLevel: r.snapshot_core_level,
      petLevel: r.snapshot_pet_level,
      withRank2Cash: withRank2.toString(),
      withRank1Cash: withRank1.toString(),
      deltaCash: delta.toString(),
      cumulativeDeltaCash: upg1to2CumDelta.toString(),
    });
  }

  // Steady-state projection for Rank 1 -> 2 if not paid back within 10 rounds
  const lastRound = rounds[rounds.length - 1];
  const lastTwoDeltas = upg1to2PerRound
    .slice(-2)
    .map((x) => Number(x.deltaCash));
  const avgSteadyDelta1to2 =
    lastTwoDeltas.reduce((a, b) => a + b, 0) / Math.max(1, lastTwoDeltas.length);
  const remainingCost1to2 = Math.max(0, Number(upg1to2Cost - upg1to2CumDelta));
  const additionalProjectedRounds1to2 =
    remainingCost1to2 > 0 && avgSteadyDelta1to2 > 0
      ? Math.ceil(remainingCost1to2 / avgSteadyDelta1to2)
      : 0;

  // 3) Counterfactual save_vault Rank 2 -> Rank 3 upgrade ($1,200 cost) evaluated against Round 9-10 steady-state snapshot
  const upg2to3Cost = 1200n;
  const steadyDeltas2to3 = [];
  for (const r of rounds.slice(-2)) {
    const baseCash = Number(r.base_cash);
    const baseXp = Number(r.base_training_xp);
    const withRank3 = computeExactRewards({
      coreLevel: r.snapshot_core_level,
      activeItems: r.snapshot_active_items.map((it) =>
        it.family === "save_vault" ? { ...it, rank: 3 } : it,
      ),
      petLevel: r.snapshot_pet_level,
      bestStreak: r.best_streak,
      baseCash,
      baseXp,
    }).cashTotal;
    const withRank2 = computeExactRewards({
      coreLevel: r.snapshot_core_level,
      activeItems: r.snapshot_active_items,
      petLevel: r.snapshot_pet_level,
      bestStreak: r.best_streak,
      baseCash,
      baseXp,
    }).cashTotal;
    steadyDeltas2to3.push({
      round: r.round,
      baseCash,
      coreLevel: r.snapshot_core_level,
      petLevel: r.snapshot_pet_level,
      withRank3Cash: withRank3.toString(),
      withRank2Cash: withRank2.toString(),
      deltaCash: (withRank3 - withRank2).toString(),
    });
  }
  const avgSteadyDelta2to3 =
    steadyDeltas2to3.reduce((s, x) => s + Number(x.deltaCash), 0) /
    Math.max(1, steadyDeltas2to3.length);
  const projectedRounds2to3 =
    avgSteadyDelta2to3 > 0 ? Math.ceil(Number(upg2to3Cost) / avgSteadyDelta2to3) : null;

  // 4) Second tool family unlock: growth_lens (cost 100 forge_energy) -> measured Growth XP delta per round
  const lensPerRound = [];
  let lensCumGxpDelta = 0n;
  for (const r of rounds) {
    const hasLens = r.snapshot_active_items.some((it) => it.family === "growth_lens");
    if (!hasLens) {
      lensPerRound.push({
        round: r.round,
        activeInSnapshot: false,
        deltaGrowthXp: "0",
        cumulativeDeltaGrowthXp: lensCumGxpDelta.toString(),
      });
      continue;
    }
    const baseCash = Number(r.base_cash);
    const baseXp = Number(r.base_training_xp);
    const withLens = computeExactRewards({
      coreLevel: r.snapshot_core_level,
      activeItems: r.snapshot_active_items,
      petLevel: r.snapshot_pet_level,
      bestStreak: r.best_streak,
      baseCash,
      baseXp,
    }).growthXp;
    const withoutLens = computeExactRewards({
      coreLevel: r.snapshot_core_level,
      activeItems: r.snapshot_active_items.filter((it) => it.family !== "growth_lens"),
      petLevel: r.snapshot_pet_level,
      bestStreak: r.best_streak,
      baseCash,
      baseXp,
    }).growthXp;
    const delta = withLens - withoutLens;
    lensCumGxpDelta += delta;
    lensPerRound.push({
      round: r.round,
      activeInSnapshot: true,
      baseXp,
      coreLevel: r.snapshot_core_level,
      petLevel: r.snapshot_pet_level,
      withLensGrowthXp: withLens.toString(),
      withoutLensGrowthXp: withoutLens.toString(),
      deltaGrowthXp: delta.toString(),
      cumulativeDeltaGrowthXp: lensCumGxpDelta.toString(),
    });
  }

  // 5) Shiba Pet Bond Lv.0 -> Lv.1 (cost $500 cash + 10 energy) -> measured Cash / GrowthXP / Energy delta per round
  const petPerRound = [];
  let petCumCashDelta = 0n;
  let petCumGxpDelta = 0n;
  let petCumEnergyDelta = 0n;
  let petEnergyPaybackRound = null;
  let petRoundsActive = 0;
  for (const r of rounds) {
    if (r.snapshot_pet_level < 1) {
      petPerRound.push({
        round: r.round,
        activeInSnapshot: false,
        deltaCash: "0",
        deltaGrowthXp: "0",
        deltaEnergy: "0",
      });
      continue;
    }
    petRoundsActive++;
    const baseCash = Number(r.base_cash);
    const baseXp = Number(r.base_training_xp);
    const withPet = computeExactRewards({
      coreLevel: r.snapshot_core_level,
      activeItems: r.snapshot_active_items,
      petLevel: r.snapshot_pet_level,
      bestStreak: r.best_streak,
      baseCash,
      baseXp,
    });
    const withoutPet = computeExactRewards({
      coreLevel: r.snapshot_core_level,
      activeItems: r.snapshot_active_items,
      petLevel: 0,
      bestStreak: r.best_streak,
      baseCash,
      baseXp,
    });
    const dCash = withPet.cashTotal - withoutPet.cashTotal;
    const dGxp = withPet.growthXp - withoutPet.growthXp;
    const dEnergy = withPet.forgeEnergy - withoutPet.forgeEnergy;
    petCumCashDelta += dCash;
    petCumGxpDelta += dGxp;
    petCumEnergyDelta += dEnergy;
    if (petEnergyPaybackRound === null && petCumEnergyDelta >= 10n) {
      petEnergyPaybackRound = {
        absoluteRound: r.round,
        roundsSinceUpgrade: petRoundsActive,
      };
    }
    petPerRound.push({
      round: r.round,
      activeInSnapshot: true,
      coreLevel: r.snapshot_core_level,
      deltaCash: dCash.toString(),
      deltaGrowthXp: dGxp.toString(),
      deltaEnergy: dEnergy.toString(),
      cumulativeDeltaCash: petCumCashDelta.toString(),
      cumulativeDeltaGrowthXp: petCumGxpDelta.toString(),
      cumulativeDeltaEnergy: petCumEnergyDelta.toString(),
    });
  }

  return {
    profileKey: profKey,
    profileLabel: profData.profile,
    starterEquipRank1: {
      costCash: "0",
      measured10RoundCumulativeExtraCash: equipCumDelta.toString(),
      measuredPaybackStatus: "0 輪（免費裝備，第 1 輪起立即生效）",
      perRoundDeltas: equipPerRound,
    },
    saveVaultUpgradeRank1To2: {
      costCash: "200",
      executedAtRound: profData.milestones.first_tool_upgrade_executed_round,
      measuredActiveRoundsIn10: upg1to2RoundsAfterUpgrade,
      measuredCumulativeExtraCashIn10Rounds: upg1to2CumDelta.toString(),
      paidBackWithin10Rounds: upg1to2PaybackRound !== null,
      measuredPayback: upg1to2PaybackRound
        ? `固定實測快照驗算：第 ${upg1to2PaybackRound.absoluteRound} 輪跨過成本（強化後第 ${upg1to2PaybackRound.roundsSinceUpgrade} 輪，當時累計差額 $${upg1to2PaybackRound.cumulativeExtraCash}；十輪合計 $${upg1to2CumDelta}）`
        : `10 輪內尚未回本（強化後實測 ${upg1to2RoundsAfterUpgrade} 輪累計多賺 $${upg1to2CumDelta} / $200，尚差 $${remainingCost1to2}）`,
      measuredPaybackDetails: upg1to2PaybackRound,
      steadyStateProjectionIfUnpaid:
        upg1to2PaybackRound !== null
          ? null
          : {
              assumption: `沿用第 9–10 輪各自開局快照的平均差額 +$${avgSteadyDelta1to2.toFixed(1)}，不另推核心與寵物繼續成長`,
              additionalRoundsNeeded: additionalProjectedRounds1to2,
              projectedTotalRoundsSinceUpgrade:
                upg1to2RoundsAfterUpgrade + additionalProjectedRounds1to2,
              projectedAbsoluteRound: 10 + additionalProjectedRounds1to2,
            },
      perRoundDeltas: upg1to2PerRound,
    },
    saveVaultUpgradeRank2To3Projection: {
      costCash: "1200",
      affordableAtRound10: BigInt(lastRound.cumulative_cash) >= 1200n,
      measuredStatusIn10Rounds: "10 輪觀測期內未執行（屬於中後期進階強化）",
      steadyStateProjection: {
        assumption: `固定第 9–10 輪快照狀態（核心 Lv.${lastRound.snapshot_core_level}、寵物 Lv.${lastRound.snapshot_pet_level}、單輪平均差額 +$${avgSteadyDelta2to3.toFixed(1)}）`,
        avgExtraCashPerRound: avgSteadyDelta2to3,
        projectedPaybackRoundsAfterUpgrade: projectedRounds2to3,
        sampleRounds: steadyDeltas2to3,
      },
    },
    growthLensUnlockRank1: {
      costEnergy: "100",
      unlockedAtRound: profData.milestones.second_tool_unlock_round,
      measuredCumulativeExtraGrowthXpIn10Rounds: lensCumGxpDelta.toString(),
      perRoundDeltas: lensPerRound,
    },
    shibaPetBondLevel1: {
      costCash: "500",
      costEnergy: "10",
      upgradedAtRound: profData.milestones.first_pet_upgrade_round,
      measuredActiveRoundsIn10: petRoundsActive,
      measuredCumulativeExtraCashIn10Rounds: petCumCashDelta.toString(),
      measuredCumulativeExtraGrowthXpIn10Rounds: petCumGxpDelta.toString(),
      measuredCumulativeExtraEnergyIn10Rounds: petCumEnergyDelta.toString(),
      energyPaybackWithin10Rounds: petEnergyPaybackRound !== null,
      measuredEnergyPayback: petEnergyPaybackRound
        ? `10 點能量成本於第 ${petEnergyPaybackRound.absoluteRound} 輪實測回本（升級後第 ${petEnergyPaybackRound.roundsSinceUpgrade} 輪）`
        : `10 輪內能量累計差額 +${petCumEnergyDelta} / 10 點（現金累計差額 +$${petCumCashDelta} / $500；既有柴犬羈絆 0→1 級使收藏分數從 100 增至 110，增加 10 分）`,
      perRoundDeltas: petPerRound,
    },
  };
}

async function runPartCTradeoffAndSeasonQualification(browser, partBResults) {
  console.log("=== Running Part C: Data-Driven ROI Analysis from Measured Rounds ===");
  const byProfile = {};
  for (const [profKey, profData] of Object.entries(partBResults)) {
    byProfile[profKey] = computeProfileRoiFromMeasuredRounds(profKey, profData);
  }
  return {
    roiAnalysisByProfile: byProfile,
  };
}

async function runLiveSlotSwapAndDailyQualificationProbe(browser, user) {
  writeCheckpoint("partC_live_start");
  console.log("=== Running Live Slot Capacity Tradeoff (Unequip/Swap/Reload/Next-Round) & Daily/Season Qualification Probe ===");
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  let page = await context.newPage();

  const consoleErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("pageerror", (error) => consoleErrors.push(String(error)));

  await page.goto(`${FRONTEND_URL}/login`);
  await page.getByTestId("email-input").fill(user.email);
  await page.getByTestId("password-input").fill(user.password);
  const econPromise = page.waitForResponse(
    (res) => res.url().includes("/api/v1/economy/me") && res.request().method() === "GET",
  );
  await page.getByRole("button", { name: "登入" }).click();
  await page.waitForURL(`${FRONTEND_URL}/`);
  const econRes = await econPromise;
  const econBody = await econRes.json();

  // Verify Economy Me API confirms Training Lv.5 (xp === 1000, level === 5) after 10 all-correct rounds!
  assertCond(
    econRes.status() === 200 && econBody.xp === 1000 && econBody.level === 5,
    "PARTC_ECONOMY_LV5_AT_1000XP",
    "All-correct player reached_1000_XP and economy.level === 5 after 10 rounds",
    { xp: econBody.xp, level: econBody.level },
  );

  // Navigate to /progression: 2/2 slots are currently equipped (save_vault Rank 2 + growth_lens Rank 1)
  await page.goto(`${FRONTEND_URL}/progression`);
  await page.getByText("核心養成階級").waitFor({ state: "visible" });
  await page.getByText("容量 2 / 2 槽").waitFor({ state: "visible" });

  // 1) Unlock 3rd tool family: forge_hammer (300 energy) while 2/2 slots are full!
  const unlockHammerBtn = page.getByRole("button", { name: /解鎖 \(300 能量\)/ }).first();
  const unlockHammerPromise = page.waitForResponse(
    (res) => res.url().includes("/api/v1/progression/unlocks/forge_hammer") && res.request().method() === "POST",
  );
  await unlockHammerBtn.click();
  const hammerRes = await unlockHammerPromise;
  assertCond(hammerRes.status() === 200, "UNLOCK_HAMMER_200", "Unlocked 3rd tool family forge_hammer (300 energy)");

  // 2) Verify that while 2/2 slots are full, the unequipped forge_hammer button shows disabled "槽位已滿"
  const slotFullBtn = page.getByRole("button", { name: "槽位已滿", exact: true });
  await slotFullBtn.waitFor({ state: "visible" });
  const isSlotFullDisabled = await slotFullBtn.isDisabled();
  assertCond(
    isSlotFullDisabled,
    "SLOT_CAPACITY_FULL_BLOCKS_3RD_TOOL",
    "When 2/2 slots are full, the 3rd owned tool shows disabled '槽位已滿' button",
    { isSlotFullDisabled },
  );

  // 3a) Deal a quick quiz session (`preSwapSessionId`) while loadout is `[save_vault, growth_lens]`!
  // Keep the original React deck mounted while a second tab changes equipment.
  // Revisiting /quick/quiz would deal a different session, not resume this one.
  const oldQuizPage = await context.newPage();
  oldQuizPage.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  oldQuizPage.on("pageerror", (error) => consoleErrors.push(String(error)));
  const preSwapDeckPromise = oldQuizPage.waitForResponse(
    (res) => res.url().includes("/api/v1/quick/quiz/deck") && res.request().method() === "GET",
  );
  await oldQuizPage.goto(`${FRONTEND_URL}/quick/quiz`);
  const preSwapDeck = await (await preSwapDeckPromise).json();
  const preSwapCtx = await queryQuizStoredItems(preSwapDeck.session_id);
  const preSwapFamilies = preSwapCtx.reward_context.equipment_snapshot.map((i) => i.family);
  assertCond(
    preSwapFamilies.includes("save_vault") &&
      preSwapFamilies.includes("growth_lens") &&
      !preSwapFamilies.includes("forge_hammer"),
    "SLOT_SWAP_OLD_SESSION_FROZEN_BEFORE",
    "Pre-swap dealt session froze [save_vault, growth_lens]",
    { preSwapFamilies },
  );

  // 3b) Go back to /progression, unequip `growth_lens` (2nd slot "卸下" button), and equip `forge_hammer`!
  await page.goto(`${FRONTEND_URL}/progression`);
  await page.getByText("容量 2 / 2 槽").waitFor({ state: "visible" });
  const unequipBtns = page.getByRole("button", { name: "卸下", exact: true });
  assertCond((await unequipBtns.count()) === 2, "TWO_UNEQUIP_BTNS_VISIBLE", "Two unequip buttons visible for 2/2 slots");

  const unequipLensPromise = page.waitForResponse(
    (res) => res.url().includes("/api/v1/equipment/loadout") && res.request().method() === "PUT",
  );
  await unequipBtns.nth(1).click();
  const unequipLensRes = await unequipLensPromise;
  assertCond(unequipLensRes.status() === 200, "UNEQUIP_SLOT2_HTTP_200", "Unequipping slot 2 returned 200");
  await page.getByText("容量 1 / 2 槽").waitFor({ state: "visible" });

  // Filter by "鍛造神錘" tab in inventory to click its exact "裝備" button!
  await page.getByRole("button", { name: "鍛造神錘", exact: true }).click();
  const equipHammerBtn = page.getByRole("button", { name: "裝備", exact: true }).first();
  await equipHammerBtn.waitFor({ state: "visible" });
  const equipHammerPromise = page.waitForResponse(
    (res) => res.url().includes("/api/v1/equipment/loadout") && res.request().method() === "PUT",
  );
  await equipHammerBtn.click();
  const equipHammerRes = await equipHammerPromise;
  assertCond(equipHammerRes.status() === 200, "EQUIP_HAMMER_HTTP_200", "Equipping forge_hammer into slot 2 returned 200");
  await page.getByText("容量 2 / 2 槽").waitFor({ state: "visible" });
  await page.getByRole("button", { name: "全部", exact: true }).click();

  // Reload page and verify persistence in UI and DB
  await page.reload();
  await page.getByText("容量 2 / 2 槽").waitFor({ state: "visible" });
  const dbAfterSwap = await queryPlayerDbState(user.id);
  const swappedFamilies = dbAfterSwap.loadout.map((l) => l.family);
  assertCond(
    dbAfterSwap.loadout.length === 2 &&
      swappedFamilies.includes("save_vault") &&
      swappedFamilies.includes("forge_hammer") &&
      !swappedFamilies.includes("growth_lens"),
    "SLOT_SWAP_DB_AND_RELOAD_VERIFIED",
    "After unequip + swap + reload, active loadout in DB and UI is [save_vault, forge_hammer] (2/2 slots)",
    { loadout: dbAfterSwap.loadout },
  );
  writeCheckpoint("partC_swap_saved");

  // Verify the old pre-swap session STILL kept its frozen snapshot `[save_vault, growth_lens]`, and complete it first!
  const preSwapCtxAfterSwap = await queryQuizStoredItems(preSwapDeck.session_id);
  const preSwapFamiliesAfterSwap = preSwapCtxAfterSwap.reward_context.equipment_snapshot.map(
    (i) => i.family,
  );
  assertCond(
    JSON.stringify(preSwapFamiliesAfterSwap) === JSON.stringify(preSwapFamilies),
    "SLOT_SWAP_OLD_SESSION_IMMUTABLE",
    "Old session dealt before slot swap preserved its original [save_vault, growth_lens] snapshot",
    { preSwapFamiliesAfterSwap },
  );

  // Finish the old pre-swap session (Round 11) so we can deal a brand-new post-swap session (Round 12) and verify new snapshot & energy multiplier!
  page = oldQuizPage;
  const r11StoredById = new Map(
    (preSwapCtx.quiz_session?.items || []).map((it) => [it.item_id, it]),
  );
  for (let i = 0; i < preSwapDeck.items.length; i++) {
    await answerQuestionOnPage(
      page,
      preSwapDeck.items[i],
      r11StoredById.get(preSwapDeck.items[i].item_id),
      true,
    );
    const nextBtnName = i === preSwapDeck.items.length - 1 ? "看結算" : "下一題";
    const nextBtn = page.getByRole("button", { name: nextBtnName, exact: true });
    await nextBtn.waitFor({ state: "visible" });
    if (i < preSwapDeck.items.length - 1) await nextBtn.click();
  }
  const r11CompPromise = page.waitForResponse(
    (res) => res.url().includes("/api/v1/quick/quiz/complete") && res.request().method() === "POST",
  );
  await page.getByRole("button", { name: "看結算", exact: true }).click();
  const r11CompData = await (await r11CompPromise).json();
  await page.getByText("倍率加成結算").waitFor({ state: "visible" });

  // Verify Round 11 settled with old snapshot (`growth_lens` active, `forge_hammer` not active)
  verifyExactMultiplierSettlement({
    coreLevel: preSwapCtx.reward_context.core_level,
    activeItems: preSwapCtx.reward_context.equipment_snapshot,
    petLevel: 1,
    bestStreak: r11CompData.best_streak,
    baseCash: Number(r11CompData.reward_receipt.base.cash),
    baseXp: Number(r11CompData.reward_receipt.base.training_xp),
    receipt: r11CompData.reward_receipt,
  });

  // Now click "再來一輪" to start Round 12 with the NEW swapped loadout `[save_vault, forge_hammer]`!
  const r12DeckPromise = page.waitForResponse(
    (res) => res.url().includes("/api/v1/quick/quiz/deck") && res.request().method() === "GET",
  );
  await page.getByRole("button", { name: "再來一輪" }).click();
  const r12Deck = await (await r12DeckPromise).json();
  const r12Ctx = await queryQuizStoredItems(r12Deck.session_id);
  const r12Families = r12Ctx.reward_context.equipment_snapshot.map((i) => i.family);
  assertCond(
    r12Families.includes("save_vault") &&
      r12Families.includes("forge_hammer") &&
      !r12Families.includes("growth_lens"),
    "SLOT_SWAP_NEW_SESSION_SNAPSHOT_VERIFIED",
    "Next round (Round 12) froze the newly swapped loadout [save_vault, forge_hammer]",
    { r12Families, activeItems: r12Ctx.reward_context.equipment_snapshot },
  );

  const r12StoredById = new Map(
    (r12Ctx.quiz_session?.items || []).map((it) => [it.item_id, it]),
  );
  for (let i = 0; i < r12Deck.items.length; i++) {
    await answerQuestionOnPage(
      page,
      r12Deck.items[i],
      r12StoredById.get(r12Deck.items[i].item_id),
      true,
    );
    const nextBtnName = i === r12Deck.items.length - 1 ? "看結算" : "下一題";
    const nextBtn = page.getByRole("button", { name: nextBtnName, exact: true });
    await nextBtn.waitFor({ state: "visible" });
    if (i < r12Deck.items.length - 1) await nextBtn.click();
  }
  const r12CompPromise = page.waitForResponse(
    (res) => res.url().includes("/api/v1/quick/quiz/complete") && res.request().method() === "POST",
  );
  await page.getByRole("button", { name: "看結算", exact: true }).click();
  const r12CompData = await (await r12CompPromise).json();
  await page.getByText("倍率加成結算").waitFor({ state: "visible" });

  // Verify Round 12 settled with new snapshot (`forge_hammer` boosted forge_energy, while `growth_xp` reverted to non-lens multiplier)!
  verifyExactMultiplierSettlement({
    coreLevel: r12Ctx.reward_context.core_level,
    activeItems: r12Ctx.reward_context.equipment_snapshot,
    petLevel: 1,
    bestStreak: r12CompData.best_streak,
    baseCash: Number(r12CompData.reward_receipt.base.cash),
    baseXp: Number(r12CompData.reward_receipt.base.training_xp),
    receipt: r12CompData.reward_receipt,
  });
  assertCond(
    BigInt(r12CompData.reward_receipt.final.forge_energy) >
      BigInt(r12CompData.reward_receipt.final.growth_xp),
    "SLOT_SWAP_ENERGY_BOOST_ACTIVE",
    "After swapping growth_lens -> forge_hammer, Round 12 forge_energy reward exceeds growth_xp reward",
    {
      round12GrowthXp: r12CompData.reward_receipt.final.growth_xp,
      round12ForgeEnergy: r12CompData.reward_receipt.final.forge_energy,
      factors: r12CompData.reward_receipt.factors,
    },
  );

  // Now complete today's Daily Challenge (/daily, 10 questions) and verify Season & Daily Leaderboard!
  const dailyPromise = page.waitForResponse(
    (res) => res.url().includes("/api/v1/daily/today") && res.request().method() === "GET",
  );
  await page.goto(`${FRONTEND_URL}/daily`);
  const dailyData = await (await dailyPromise).json();
  assertCond(
    dailyData.status === "ready" && Array.isArray(dailyData.items) && dailyData.items.length === 10,
    "DAILY_UNLOCKED_AT_LV5",
    "Daily challenge unlocked at Training Lv.5 (>= 1,000 XP) and dealt 10 questions",
    { status: dailyData.status, itemCount: dailyData.items?.length },
  );

  const dailyQuizDb = await queryQuizStoredItems(dailyData.session_id);
  const dailyStoredById = new Map(
    (dailyQuizDb.quiz_session?.items || []).map((it) => [it.item_id, it]),
  );
  for (let i = 0; i < dailyData.items.length; i++) {
    await answerQuestionOnPage(
      page,
      dailyData.items[i],
      dailyStoredById.get(dailyData.items[i].item_id),
      true,
    );
    const nextBtnName = i === dailyData.items.length - 1 ? "看結算" : "下一題";
    const nextBtn = page.getByRole("button", { name: nextBtnName, exact: true });
    await nextBtn.waitFor({ state: "visible" });
    if (i < dailyData.items.length - 1) await nextBtn.click();
  }

  const dailyCompPromise = page.waitForResponse(
    (res) => res.url().includes("/api/v1/quick/quiz/complete") && res.request().method() === "POST",
  );
  await page.getByRole("button", { name: "看結算", exact: true }).click();
  const dailyCompRes = await dailyCompPromise;
  assertCond(dailyCompRes.status() === 200, "DAILY_COMPLETE_200", "Daily challenge complete returned 200");
  await page.getByText("倍率加成結算").waitFor({ state: "visible" });

  // Verify that on Daily settlement, "再來一輪" is NOT shown (daily limit = 1 per day), and "看今天的排名" + "前往養成與配裝" are shown!
  const restartBtnCountOnDaily = await page.getByRole("button", { name: "再來一輪" }).count();
  assertCond(
    restartBtnCountOnDaily === 0,
    "AC3_DAILY_ONE_PER_DAY_LIMIT",
    "Daily training settlement does not show '再來一輪' (preserves 1/day limit)",
    { restartBtnCountOnDaily },
  );
  writeCheckpoint("partC_daily_completed");

  const seasonBoardPromise = page.waitForResponse(
    (res) =>
      res.url().includes("/api/v1/seasons/") &&
      res.url().includes("/boards/accuracy") &&
      res.request().method() === "GET",
  );
  await page.getByRole("link", { name: "看今天的排名" }).click();
  await page.waitForURL(`${FRONTEND_URL}/leaderboard`);
  await page.getByTestId("leaderboard-me").waitFor({ state: "visible" });
  await page.getByRole("tab", { name: "14天競技賽季" }).click();
  const seasonBoardRes = await seasonBoardPromise;
  const seasonBoardJson = await seasonBoardRes.json();
  const mySeasonEntry = seasonBoardJson.my_entry;
  await page.getByText("1／5 天 · 10／50 題").waitFor({ state: "visible" });
  const seasonAfterDailyText = await page.locator("main").innerText();

  // AC7 Assertion: Verify against actual API rank (`mySeasonEntry.rank`) and unqualified status (`mySeasonEntry.qualified === false`), never hardcoding Rank #1!
  assertCond(
    mySeasonEntry &&
      mySeasonEntry.is_qualified === false &&
      typeof mySeasonEntry.rank === "number" &&
      seasonAfterDailyText.includes("1／5 天 · 10／50 題") &&
      seasonAfterDailyText.includes("暫列（未滿資格）") &&
      seasonAfterDailyText.includes(`暫${mySeasonEntry.rank}`),
    "AC7_PROVISIONAL_RANK_DISTINGUISHED",
    `After 1 day (10 questions) of daily training, player is unqualified (qualified=false) and UI displays '暫列（未滿資格）' and actual provisional position '暫${mySeasonEntry?.rank}'`,
    { mySeasonEntry, seasonAfterDailyText },
  );

  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "10-leaderboard-season-provisional-mobile-390x844.png"),
  });
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "10-leaderboard-season-provisional-desktop-1280x900.png"),
  });

  assertCond(
    consoleErrors.length === 0,
    "PARTC_ZERO_CONSOLE_ERRORS",
    "Slot tradeoff and daily qualification flow had zero console errors",
    { consoleErrors },
  );

  await context.close();
  return {
    user: { id: user.id, email: user.email },
    slotCapacityTradeoffVerified: true,
    slotSwapVerification: {
      preSwapSessionId: preSwapDeck.session_id,
      preSwapSnapshotFamilies: preSwapFamilies,
      preSwapRound11Factors: r11CompData.reward_receipt.factors,
      preSwapRound11Final: r11CompData.reward_receipt.final,
      postSwapSessionId: r12Deck.session_id,
      postSwapSnapshotFamilies: r12Families,
      postSwapRound12Factors: r12CompData.reward_receipt.factors,
      postSwapRound12Final: r12CompData.reward_receipt.final,
    },
    dailyUnlockedAtRound: 10,
    dailyUnlockedAtTrainingXp: 1000,
    seasonProvisionalDisplayVerified: true,
    mySeasonEntry,
    seasonAfterDailyText,
  };
}

async function runRealScenarioProbe(user) {
  writeCheckpoint("partD_real_scenario_start");
  const login = await fetch(`${API_URL}/api/v1/login/access-token`, {
    method: "POST", headers: {"Content-Type": "application/x-www-form-urlencoded"},
    body: new URLSearchParams({username:user.email, password:user.password}),
  });
  assertCond(login.status === 200, "SCENARIO_LOGIN", "Normal earned-progress account can sign in");
  const auth = await login.json();
  const headers = {Authorization:`Bearer ${auth.access_token}`, "X-ScamGym-Client-Version":"2", "Content-Type":"application/json"};
  const inboxResponse = await fetch(`${API_URL}/api/v1/scenario/inbox`, {headers});
  assertCond(inboxResponse.status === 200, "SCENARIO_INBOX", "Real scenario inbox is available");
  const inbox = await inboxResponse.json();
  const item = inbox.find(item => item.fraud_type === "investment" && item.status === "active");
  assertCond(Boolean(item), "SCENARIO_ACTIVE", "Original scenario exists without seeding a test outcome");
  const before = (await runSql(`SELECT persona_role, player_turns, conversation_history FROM scenario_session WHERE id='${item.id}' AND user_id='${user.id}'`))[0];
  const messageResponse = await fetch(`${API_URL}/api/v1/scenario/${item.id}/message`, {
    method:"POST",headers,body:JSON.stringify({text:"請問這件事要怎麼查證？我會自己找官方客服確認，不會提供密碼。"}),
  });
  const reply = await messageResponse.json();
  assertCond(messageResponse.status === 200 && reply.messages?.some(text => text.trim()), "SCENARIO_REAL_PROVIDER_REPLY", "Real provider returned a nonempty reply; no mock response", {status:messageResponse.status});
  const after = (await runSql(`SELECT player_turns, conversation_history FROM scenario_session WHERE id='${item.id}'`))[0];
  assertCond(after.player_turns === before.player_turns + 1 && after.conversation_history.length > before.conversation_history.length, "SCENARIO_TURN_PERSISTED", "Player turn and real NPC response were persisted once");
  const stateBefore = await queryPlayerDbState(user.id);
  const judgment = {action:before.persona_role === "scam" ? "report" : "comply"};
  const judged = await fetch(`${API_URL}/api/v1/scenario/${item.id}/judge`, {method:"POST",headers,body:JSON.stringify(judgment)});
  const outcome = await judged.json();
  const stateAfter = await queryPlayerDbState(user.id);
  assertCond(judged.status === 200 && ["win_report","win_trust"].includes(outcome.outcome), "SCENARIO_RULE_JUDGMENT", "Original role-based deterministic judgment returned success");
  assertCond(BigInt(stateAfter.user.cash)-BigInt(stateBefore.user.cash) === BigInt(outcome.cash_delta) && outcome.reward_receipt.final.cash_total === outcome.cash_delta && outcome.reward_receipt.final.cash_bonus === "0" && BigInt(stateAfter.growth.lifetime_cash)-BigInt(stateBefore.growth.lifetime_cash) === BigInt(outcome.cash_delta), "SCENARIO_CASH_RECEIPT_AND_INCOME", "Original cash payout matches receipt and lifetime income, without cash multiplication or duplicate payout");
  const replay = await fetch(`${API_URL}/api/v1/scenario/${item.id}/judge`, {method:"POST",headers,body:JSON.stringify(judgment)});
  const stateReplay = await queryPlayerDbState(user.id);
  assertCond(replay.status === 400 && stateReplay.user.cash === stateAfter.user.cash && stateReplay.growth.lifetime_cash === stateAfter.growth.lifetime_cash, "SCENARIO_REPLAY_REJECTED", "Repeated judgment cannot award cash or lifetime income again");
  return {scenarioId:item.id, realProvider:true, replyMessageCount:reply.messages.length, persistedPlayerTurns:after.player_turns, deterministicOutcome:outcome.outcome, cashDelta:outcome.cash_delta, receiptId:outcome.reward_receipt.receipt_id, cashBonus:outcome.reward_receipt.final.cash_bonus, replayStatus:replay.status};
}

async function main() {
  const browser = await chromium.launch({
    headless: true,
    args: ["--host-resolver-rules=MAP localhost host.docker.internal"],
  });
  try {
    const partA = await runPartAUiToCodeTrace(browser);
    const partB = await runPartBThreePlayers(browser, 10);
    const allCorrectCreds = partB.all_correct._credentialsForPartC;
    delete partB.all_correct._credentialsForPartC;
    const partCAnalysis = await runPartCTradeoffAndSeasonQualification(browser, partB);
    checkpointState.partC = partCAnalysis;
    writeCheckpoint("partC_analysis_complete");
    const partCLive = await runLiveSlotSwapAndDailyQualificationProbe(browser, allCorrectCreds);
    checkpointState.partC = {
      ...partCAnalysis,
      liveVerification: partCLive,
    };
    writeCheckpoint("partC_complete");
    checkpointState.partD = await runRealScenarioProbe(allCorrectCreds);
    writeCheckpoint("partD_complete");

    const summary = sanitizePayload({
      status: "PASSED",
      phase: PHASE,
      evaluatedAt: new Date().toISOString(),
      environment: {
        frontendUrl: FRONTEND_URL,
        apiUrl: API_URL,
      },
      assertionsSummary: {
        totalAssertions: assertionsLog.length,
        passedAssertions: assertionsLog.filter((a) => a.passed).length,
        failedAssertions: assertionsLog.filter((a) => !a.passed).length,
      },
      partA,
      partB,
      partC: checkpointState.partC,
      partD: checkpointState.partD,
      assertionsLog,
    });

    const jsonString = JSON.stringify(summary, null, 2);
    // Final safety scan: ensure no JWT or access_token leaked into JSON output
    if (/eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/.test(jsonString)) {
      throw new Error("SECURITY VIOLATION: Unredacted JWT detected in output JSON!");
    }

    const jsonPath = path.join(OUT_DIR, `evaluation-${PHASE}.json`);
    fs.writeFileSync(jsonPath, jsonString, "utf8");

    const csvLines = [
      "profile,round,correct,total,best_streak,base_cash,cash_bonus,cash_earned,training_xp_earned,training_level_after,growth_xp_earned,forge_energy_earned,cash_factor,growth_xp_factor,energy_factor,core_level_after,cumulative_cash,cumulative_training_xp,cumulative_growth_xp,cumulative_forge_energy,question_chars,human_read_est_fast_sec,human_read_est_med_sec,human_read_est_careful_sec,script_round_ms,ui_action_ms,pure_api_ms,actions_taken",
    ];
    for (const [profKey, profData] of Object.entries(partB)) {
      for (const r of profData.rounds) {
        csvLines.push(
          [
            profKey,
            r.round,
            r.correct_count,
            r.total,
            r.best_streak,
            r.base_cash,
            r.cash_bonus,
            r.cash_earned,
            r.training_xp_earned,
            r.training_level_after,
            r.growth_xp_earned,
            r.forge_energy_earned,
            r.factors_used.cash || "1.0",
            r.factors_used.growth_xp || "1.0",
            r.factors_used.energy || "1.0",
            r.core_level_after,
            r.cumulative_cash,
            r.cumulative_training_xp,
            r.cumulative_growth_xp,
            r.cumulative_forge_energy,
            r.question_chars,
            r.human_read_est_fast_sec,
            r.human_read_est_med_sec,
            r.human_read_est_careful_sec,
            r.script_round_ms,
            r.ui_action_ms,
            r.pure_api_ms,
            `"${(r.actions_taken || []).join(";")}"`,
          ].join(","),
        );
      }
    }
    const csvPath = path.join(OUT_DIR, `rounds-${PHASE}.csv`);
    fs.writeFileSync(csvPath, csvLines.join("\n"), "utf8");

    console.log(
      `SUCCESS: ${assertionsLog.length}/${assertionsLog.length} assertions passed. Saved ${jsonPath} and ${csvPath}`,
    );
  } catch (err) {
    writeFailureReport(err);
    throw err;
  } finally {
    await browser.close();
    await db.close();
  }
}

export { computeExactRewards, computeProfileRoiFromMeasuredRounds };

if (import.meta.main) {
  main().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}
