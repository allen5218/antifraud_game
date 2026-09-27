import { afterEach, describe, expect, it, mock } from "bun:test"
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router"
import { act, cleanup, render, screen } from "@testing-library/react"

let economyLevel = 3

mock.module("@/hooks/useEconomy", () => ({
  useEconomyMe: () => ({
    data: {
      cash: 12450,
      streak_days: 5,
      level: economyLevel,
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
    expect(unlocked.getAttribute("data-locked")).toBe("false")
    expect(locked.getAttribute("aria-disabled")).toBe("true")
    expect(locked.getAttribute("data-locked")).toBe("true")
    expect(locked.textContent).toContain("Lv.5 解鎖")
    expect(locked.querySelector("a")).toBeNull()
  })

  it("every unlocked card is a real link", async () => {
    economyLevel = 6
    await renderWithRouter()
    for (const [label, href] of [
      ["題組訓練", "/quick/quiz"],
      ["滑卡訓練", "/quick/swipe"],
      ["每日訓練", "/daily"],
      ["排行榜", "/leaderboard"],
    ]) {
      const card = screen.getByTestId(`mode-${label}`)
      expect(card.getAttribute("data-locked")).toBe("false")
      expect(card.querySelector("a")?.getAttribute("href")).toBe(href)
      expect(card.textContent).not.toContain("解鎖")
    }
    economyLevel = 3
  })
})
