import { afterEach, describe, expect, it } from "bun:test"
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router"
import { act, cleanup, render, screen } from "@testing-library/react"
import { BottomTabs } from "./BottomTabs"

afterEach(() => {
  cleanup()
})

async function renderWithRouter(path: string) {
  const rootRoute = createRootRoute({ component: () => <BottomTabs /> })
  const catchAll = createRoute({
    getParentRoute: () => rootRoute,
    path: "$",
    component: () => null,
  })
  const router = createRouter({
    routeTree: rootRoute.addChildren([catchAll]),
    history: createMemoryHistory({ initialEntries: [path] }),
  })
  await router.load()
  await act(async () => {
    render(<RouterProvider router={router} />)
  })
}

describe("<BottomTabs />", () => {
  it("renders four tabs", async () => {
    await renderWithRouter("/")
    expect(screen.getByText("首頁")).toBeTruthy()
    expect(screen.getByText("情境")).toBeTruthy()
    expect(screen.getByText("資產")).toBeTruthy()
    expect(screen.getByText("我")).toBeTruthy()
  })

  it("highlights home tab on /", async () => {
    await renderWithRouter("/")
    const homeTab = screen.getByTestId("tab-home")
    expect(homeTab.className).toContain("text-primary")
    expect(homeTab.className).toContain("font-bold")
  })

  it("highlights scenarios tab on /scenarios, not home", async () => {
    await renderWithRouter("/scenarios")
    const scen = screen.getByTestId("tab-scenarios")
    expect(scen.className).toContain("text-primary")
    const home = screen.getByTestId("tab-home")
    expect(home.className).not.toContain("text-primary")
  })
})
