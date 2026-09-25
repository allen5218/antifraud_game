import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router"
import { act, render } from "@testing-library/react"
import type { ReactNode } from "react"

/**
 * 把元件放進一個最小的 TanStack Router 裡渲染。
 * 元件裡有 <Link> 時,沒有 router context 會直接丟錯。
 */
export async function renderWithRouter(ui: ReactNode) {
  const rootRoute = createRootRoute({ component: () => ui })
  const catchAll = createRoute({
    getParentRoute: () => rootRoute,
    path: "$",
    component: () => null,
  })
  const router = createRouter({
    routeTree: rootRoute.addChildren([catchAll]),
    history: createMemoryHistory({ initialEntries: ["/"] }),
  })
  let result: ReturnType<typeof render> | undefined
  await act(async () => {
    result = render(<RouterProvider router={router} />)
  })
  return result as ReturnType<typeof render>
}
