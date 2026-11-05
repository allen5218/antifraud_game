import { afterEach, beforeEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
  RouterProvider,
} from "@tanstack/react-router"
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react"
import type { StarterTasks } from "@/client"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { onboardingApi } from "./onboardingApi"
import { StarterTasksCard } from "./StarterTasksCard"

const response = <T,>(value: T) =>
  new CancelablePromise<T>((resolve) => resolve(value))

let qc: QueryClient

beforeEach(() => {
  localStorage.clear()
  qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
})

afterEach(() => {
  cleanup()
  localStorage.clear()
  mock.restore()
})

async function renderCard(tasks: StarterTasks) {
  const rootRoute = createRootRoute({
    component: () => (
      <QueryClientProvider client={qc}>
        <Outlet />
      </QueryClientProvider>
    ),
  })
  const home = createRoute({
    getParentRoute: () => rootRoute,
    path: "/",
    component: () => <StarterTasksCard tasks={tasks} />,
  })
  const router = createRouter({
    routeTree: rootRoute.addChildren([home]),
    history: createMemoryHistory({ initialEntries: ["/"] }),
  })
  await router.load()
  await act(async () => {
    render(<RouterProvider router={router} />)
  })
}

const NONE: StarterTasks = {
  swipe: false,
  quiz: false,
  scenario: false,
  shop: false,
}
const ALL: StarterTasks = {
  swipe: true,
  quiz: true,
  scenario: true,
  shop: true,
}

test("列出四項任務，完成的打勾，寫出進度", async () => {
  await renderCard({ ...NONE, swipe: true })
  expect(await screen.findByText("新手任務 1／4")).toBeTruthy()
  const swipe = screen.getByRole("link", { name: /滑一輪卡/ })
  expect(swipe.getAttribute("href")).toBe("/quick/swipe")
  expect(swipe.getAttribute("data-done")).toBe("true")
  expect(
    screen
      .getByRole("link", { name: /和 AI 角色聊一場/ })
      .getAttribute("data-done"),
  ).toBe("false")
  expect(screen.getByRole("link", { name: /去購物看看/ })).toBeTruthy()
  expect(screen.queryByRole("button", { name: /領 500 元/ })).toBeNull()
})

test("四項都完成才能領獎，領了會重讀房間資料", async () => {
  const claim = spyOn(onboardingApi, "claim").mockImplementation(() =>
    response({ cash: 500, xp: 100 }),
  )
  const invalidate = spyOn(qc, "invalidateQueries")
  await renderCard(ALL)
  fireEvent.click(await screen.findByRole("button", { name: /領 500 元/ }))
  await waitFor(() => expect(claim).toHaveBeenCalledTimes(1))
  await waitFor(() =>
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["home-summary"] }),
  )
})

test("可以收起，收起後只剩標題和進度", async () => {
  await renderCard(NONE)
  fireEvent.click(await screen.findByRole("button", { name: "收起新手任務" }))
  expect(screen.queryByRole("link", { name: /滑一輪卡/ })).toBeNull()
  expect(screen.getByText("新手任務 0／4")).toBeTruthy()
  fireEvent.click(screen.getByRole("button", { name: "展開新手任務" }))
  expect(screen.getByRole("link", { name: /滑一輪卡/ })).toBeTruthy()
})
