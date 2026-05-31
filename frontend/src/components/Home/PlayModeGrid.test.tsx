import { afterEach, describe, expect, it, mock } from "bun:test"
import { cleanup, render, screen } from "@testing-library/react"

mock.module("@/hooks/useEconomy", () => ({
  useEconomyMe: () => ({
    data: {
      cash: 12450,
      streak_days: 5,
      level: 3,
      pending_accrual: 840,
      bankruptcy_pending: false,
      xp: 850,
    },
  }),
  useClaimAccrual: () => ({ mutate: () => {}, isPending: false }),
  useProperties: () => ({ data: { tiers: [], owned: [] } }),
  useAssets: () => ({ data: null }),
  useBuyProperty: () => ({ mutate: () => {} }),
  useLiquidate: () => ({ mutate: () => {} }),
}))

import { PlayModeGrid } from "./PlayModeGrid"

describe("<PlayModeGrid />", () => {
  afterEach(cleanup)

  it("locks cards above current level, unlocks others", () => {
    render(<PlayModeGrid />)
    // default level 3 from mock
    const unlocked = screen.getByTestId("mode-題組訓練")
    const locked = screen.getByTestId("mode-排行榜")
    expect(unlocked.getAttribute("aria-disabled")).toBe("false")
    expect(unlocked.className).not.toContain("opacity-55")
    expect(locked.getAttribute("aria-disabled")).toBe("true")
    expect(locked.className).toContain("opacity-55")
  })
})
