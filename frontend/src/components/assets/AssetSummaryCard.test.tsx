import { afterEach, beforeEach, describe, expect, it } from "bun:test"
import { cleanup, render, screen } from "@testing-library/react"
import { useEconomyStore } from "@/stores/economy"
import { AssetSummaryCard } from "./AssetSummaryCard"

describe("<AssetSummaryCard />", () => {
  beforeEach(() => useEconomyStore.getState().reset())
  afterEach(cleanup)

  it("shows total net worth = cash + sum(owned.price)", () => {
    render(<AssetSummaryCard />)
    // 12450 + 1000 + 5000 = 18450
    expect(screen.getByText(/18,450/)).toBeTruthy()
  })

  it("shows daily passive income from owned", () => {
    render(<AssetSummaryCard />)
    // 5 + 35 = 40
    expect(screen.getByText(/\+ \$ 40/)).toBeTruthy()
  })
})
