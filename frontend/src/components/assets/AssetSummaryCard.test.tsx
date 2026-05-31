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
  useAssets: () => ({
    data: {
      cash: 12450,
      property_value: 6000, // 1000 + 5000 (mock tiers)
      daily_income: 40, // 5 + 35
      total_net_worth: 18450, // 12450 + 6000
      owned_count: 2,
    },
  }),
  useClaimAccrual: () => ({ mutate: () => {}, isPending: false }),
  useProperties: () => ({ data: { tiers: [], owned: [] } }),
  useBuyProperty: () => ({ mutate: () => {} }),
  useLiquidate: () => ({ mutate: () => {} }),
}))

import { AssetSummaryCard } from "./AssetSummaryCard"

describe("<AssetSummaryCard />", () => {
  afterEach(cleanup)

  it("shows total net worth from useAssets", () => {
    render(<AssetSummaryCard />)
    expect(screen.getByText(/18,450/)).toBeTruthy()
  })

  it("shows daily passive income from useAssets", () => {
    render(<AssetSummaryCard />)
    expect(screen.getByText(/\+ \$ 40/)).toBeTruthy()
  })
})
