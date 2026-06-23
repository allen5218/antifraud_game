import { afterEach, describe, expect, it, mock } from "bun:test"
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router"
import { act, cleanup, render, screen } from "@testing-library/react"

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

async function renderWithRouter() {
  const rootRoute = createRootRoute({ component: () => <PlayModeGrid /> })
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

describe("<PlayModeGrid />", () => {
  afterEach(cleanup)

  it("locks cards above current level, unlocks others", async () => {
    await renderWithRouter()
    // default level 3 from mock
    const unlocked = screen.getByTestId("mode-題組訓練")
    const locked = screen.getByTestId("mode-排行榜")
    expect(unlocked.getAttribute("aria-disabled")).toBe("false")
    expect(unlocked.className).not.toContain("opacity-55")
    expect(locked.getAttribute("aria-disabled")).toBe("true")
    expect(locked.className).toContain("opacity-55")
  })
})
