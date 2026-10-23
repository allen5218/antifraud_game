import { afterEach, expect, test } from "bun:test"
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
  RouterProvider,
} from "@tanstack/react-router"
import { act, cleanup, render, screen } from "@testing-library/react"
import { Logo } from "./Logo"

afterEach(cleanup)

test("側欄的商標連回房間首頁，不是前測", async () => {
  const rootRoute = createRootRoute({ component: () => <Outlet /> })
  const admin = createRoute({
    getParentRoute: () => rootRoute,
    path: "/settings",
    component: () => <Logo variant="responsive" />,
  })
  const router = createRouter({
    routeTree: rootRoute.addChildren([admin]),
    history: createMemoryHistory({ initialEntries: ["/settings"] }),
  })
  await router.load()
  await act(async () => {
    render(<RouterProvider router={router} />)
  })
  const link = screen
    .getByRole("img", { name: "ScamGym 識詐練習場" })
    .closest("a")
  expect(link?.getAttribute("href")).toBe("/")
})
