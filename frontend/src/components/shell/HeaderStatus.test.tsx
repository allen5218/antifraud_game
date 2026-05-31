import { afterEach, beforeEach, describe, expect, it } from "bun:test"
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router"
import { act, cleanup, render, screen } from "@testing-library/react"
import { useEconomyStore } from "@/stores/economy"
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
  beforeEach(() => useEconomyStore.getState().reset())

  it("renders cash, streak, level from store", async () => {
    await renderWithRouter()
    expect(screen.getByText(/12,450/)).toBeTruthy()
    expect(screen.getByText("5")).toBeTruthy()
    expect(screen.getByText(/Lv\.3/)).toBeTruthy()
  })

  it("renders negative cash in red", async () => {
    useEconomyStore.getState().triggerBankruptcy(50000)
    await renderWithRouter()
    const cashEl = screen.getByTestId("hdr-cash")
    expect(cashEl.className).toMatch(/text-red/)
  })
})
