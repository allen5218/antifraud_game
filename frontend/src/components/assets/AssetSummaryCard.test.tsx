import { afterAll, afterEach, describe, expect, it, mock } from "bun:test"
import { cleanup, render, screen } from "@testing-library/react"

// bun 的 mock.module 會留給之後的測試檔，只覆寫要用的 hook，其他保留真的（查詢設定等）
const actualEconomy = { ...(await import("@/hooks/useEconomy")) }

mock.module("@/hooks/useEconomy", () => ({
  ...actualEconomy,
  useAssets: () => ({
    data: {
      cash: 12450,
      property_value: 6000, // 1000 + 5000 (mock tiers)
      daily_income: 40, // 5 + 35
      total_net_worth: 18450, // 12450 + 6000
      owned_count: 2,
    },
  }),
}))

import { AssetSummaryCard } from "./AssetSummaryCard"

afterAll(() => {
  mock.module("@/hooks/useEconomy", () => actualEconomy)
})

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
