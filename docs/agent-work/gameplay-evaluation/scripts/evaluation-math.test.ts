import { expect, test } from "bun:test";
import { computeExactRewards, computeProfileRoiFromMeasuredRounds } from "./run-gameplay-eval.mjs";

test("free rank-one equipment analysis excludes the paid rank-two upgrade", () => {
  const result = computeProfileRoiFromMeasuredRounds("sample", {
    profile: "isolated calculation fixture",
    milestones: { first_tool_upgrade_executed_round: 0 },
    rounds: [{
      round: 1, base_cash: "220", base_training_xp: 100,
      snapshot_core_level: 0, snapshot_pet_level: 0,
      snapshot_active_items: [{ family: "save_vault", rank: 2 }],
      best_streak: 5, core_level_after: 0, cumulative_cash: "1000",
    }],
  });
  expect(result.starterEquipRank1.measured10RoundCumulativeExtraCash).toBe("22");
  expect(result.saveVaultUpgradeRank1To2.measuredCumulativeExtraCashIn10Rounds).toBe("22");
});

test("rounding preserves a large integer and can erase a small pet energy bonus", () => {
  const cash = 10n ** 40n + 9n;
  const result = computeExactRewards({
    coreLevel: 0, activeItems: [{family: "save_vault", rank: 1}],
    petLevel: 0, bestStreak: 0, baseCash: cash, baseXp: 40,
  });
  expect(result.cashTotal).toBe((cash * 11n) / 10n);
  const pet = computeExactRewards({
    coreLevel: 0, activeItems: [], petLevel: 1,
    bestStreak: 0, baseCash: 80, baseXp: 40,
  });
  expect(pet.forgeEnergy).toBe(40n);
});
