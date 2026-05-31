import { afterEach, describe, expect, it, mock } from "bun:test"
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router"
import { act, cleanup, render, screen } from "@testing-library/react"

// mock.module 必須在 import 元件之前呼叫
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
  useAssets: () => ({
    data: {
      cash: 12450,
      property_value: 0,
      daily_income: 0,
      total_net_worth: 12450,
      owned_count: 0,
    },
  }),
  useBuyProperty: () => ({ mutate: () => {} }),
  useLiquidate: () => ({ mutate: () => {} }),
}))

import { HeaderStatus } from "./HeaderStatus"

afterEach(() => {
  cleanup()
})

async function renderWithRouter() {
  const rootRoute = createRootRoute({ component: () => <HeaderStatus /> })
  const catchAll = createRoute({
    getParentRoute: () => rootRoute,
    path: "$",
    component: () => null,
  })
  const router = createRouter({
    routeTree: rootRoute.addChildren([catchAll]),
    history: createMemoryHistory({ initialEntries: ["/"] }),
  })
  await router.load()
  await act(async () => {
    render(<RouterProvider router={router} />)
  })
}

describe("<HeaderStatus />", () => {
  it("renders cash, streak_days, level from hook", async () => {
    await renderWithRouter()
    expect(screen.getByText(/12,450/)).toBeTruthy()
    expect(screen.getByText("5")).toBeTruthy()
    expect(screen.getByText(/Lv\.3/)).toBeTruthy()
  })

  it("renders negative cash in red when cash < 0", async () => {
    mock.module("@/hooks/useEconomy", () => ({
      useEconomyMe: () => ({
        data: {
          cash: -1550,
          streak_days: 5,
          level: 3,
          pending_accrual: 0,
          bankruptcy_pending: true,
          xp: 850,
        },
      }),
      useClaimAccrual: () => ({ mutate: () => {}, isPending: false }),
      useProperties: () => ({ data: { tiers: [], owned: [] } }),
      useAssets: () => ({
        data: {
          cash: -1550,
          property_value: 0,
          daily_income: 0,
          total_net_worth: -1550,
          owned_count: 0,
        },
      }),
      useBuyProperty: () => ({ mutate: () => {} }),
      useLiquidate: () => ({ mutate: () => {} }),
    }))
    await renderWithRouter()
    const cashEl = screen.getByTestId("hdr-cash")
    expect(cashEl.className).toMatch(/text-red/)
  })
})
