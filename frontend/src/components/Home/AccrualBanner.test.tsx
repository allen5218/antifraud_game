import { afterEach, describe, expect, it, mock } from "bun:test"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"

const mockClaim = mock(() => {})

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
  useClaimAccrual: () => ({ mutate: mockClaim, isPending: false }),
  useProperties: () => ({ data: { tiers: [], owned: [] } }),
  useAssets: () => ({ data: null }),
  useBuyProperty: () => ({ mutate: () => {} }),
  useLiquidate: () => ({ mutate: () => {} }),
}))

import { AccrualBanner } from "./AccrualBanner"

afterEach(() => {
  cleanup()
  mockClaim.mockClear()
})

describe("<AccrualBanner />", () => {
  it("shows pending amount and claim button when pending > 0", () => {
    render(<AccrualBanner />)
    expect(screen.getByText(/\+\$840/)).toBeTruthy()
    expect(screen.getByRole("button", { name: /領取/ })).toBeTruthy()
  })

  it("clicking 領取 calls claimAccrual mutate", () => {
    render(<AccrualBanner />)
    fireEvent.click(screen.getByRole("button", { name: /領取/ }))
    expect(mockClaim).toHaveBeenCalledTimes(1)
  })

  it("hides when pending_accrual is 0", () => {
    mock.module("@/hooks/useEconomy", () => ({
      useEconomyMe: () => ({
        data: {
          cash: 12450,
          streak_days: 5,
          level: 3,
          pending_accrual: 0,
          bankruptcy_pending: false,
          xp: 850,
        },
      }),
      useClaimAccrual: () => ({ mutate: mockClaim, isPending: false }),
      useProperties: () => ({ data: { tiers: [], owned: [] } }),
      useAssets: () => ({ data: null }),
      useBuyProperty: () => ({ mutate: () => {} }),
      useLiquidate: () => ({ mutate: () => {} }),
    }))
    const { container } = render(<AccrualBanner />)
    expect(container.firstChild).toBeNull()
  })
})
