import { afterEach, describe, expect, it, mock } from "bun:test"
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router"
import { act, cleanup, render, screen, within } from "@testing-library/react"

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

const PRIMARY = [
  ["滑卡訓練", "/quick/swipe", "直覺判斷"],
  ["訊息判讀訓練", "/quick/quiz", "辨識話術、知道怎麼查證"],
  ["情境對抗訓練", "/scenarios", "臨場判斷"],
  ["檢測", "/exam", "四關考完，70 分過關"],
] as const

describe("<PlayModeGrid />", () => {
  afterEach(() => {
    cleanup()
    economyLevel = 3
  })

  it("shows four entries and locks the daily section below level 5", async () => {
    await renderWithRouter()
    const primary = screen.getByTestId("home-primary-entries")
    for (const [label, href, desc] of PRIMARY) {
      const card = within(primary).getByTestId(`mode-${label}`)
      expect(card.getAttribute("aria-disabled")).toBe("false")
      expect(card.getAttribute("data-locked")).toBe("false")
      expect(card.querySelector("a")?.getAttribute("href")).toBe(href)
      expect(card.textContent).toContain(desc)
    }
    expect(within(primary).queryByTestId("mode-每日訓練")).toBeNull()
    expect(within(primary).queryByTestId("mode-排行榜")).toBeNull()

    const secondary = screen.getByTestId("home-secondary-entries")
    const locked = within(secondary).getByTestId("mode-排行榜")
    expect(locked.getAttribute("aria-disabled")).toBe("true")
    expect(locked.getAttribute("data-locked")).toBe("true")
    expect(locked.textContent).toContain("Lv.5 解鎖")
    expect(locked.querySelector("a")).toBeNull()
    const daily = within(secondary).getByTestId("mode-每日訓練")
    expect(daily.getAttribute("data-locked")).toBe("true")
    expect(daily.querySelector("a")).toBeNull()
  })

  it("every unlocked card is a real link", async () => {
    economyLevel = 6
    await renderWithRouter()
    for (const [label, href] of [
      ...PRIMARY.map(([label, href]) => [label, href] as const),
      ["每日訓練", "/daily"] as const,
      ["排行榜", "/leaderboard"] as const,
    ]) {
      const card = screen.getByTestId(`mode-${label}`)
      expect(card.getAttribute("data-locked")).toBe("false")
      expect(card.querySelector("a")?.getAttribute("href")).toBe(href)
      expect(card.textContent).not.toContain("解鎖")
    }
    expect(screen.getByTestId("mode-每日訓練").textContent).toContain(
      "每天 10 題",
    )
    expect(screen.getByTestId("mode-排行榜").textContent).toContain(
      "今日與本週排名",
    )
  })
})
