import { afterEach, expect, test } from "bun:test"
import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router"
import { cleanup, render, screen } from "@testing-library/react"
import type { MenuItem } from "@/components/room/logic"
import { RailMenu } from "./RailMenu"

afterEach(cleanup)

const items: MenuItem[] = [
  {
    id: "phone",
    label: "情境對抗",
    status: "還有 2 人沒聊",
    done: false,
    to: "/scenarios",
  },
  {
    id: "calendar",
    label: "每日訓練",
    status: "今天做完了",
    done: true,
    to: "/daily",
  },
]

test("桌機側欄列出和房間選單同一份清單，連到同一頁並寫狀態", async () => {
  const router = createRouter({
    routeTree: createRootRoute({
      component: () => <RailMenu items={items} />,
    }),
    history: createMemoryHistory({ initialEntries: ["/"] }),
  })
  render(<RouterProvider router={router} />)
  const phone = await screen.findByRole("link", { name: /情境對抗/ })
  expect(phone.getAttribute("href")).toBe("/scenarios")
  expect(phone.textContent).toContain("還有 2 人沒聊")
  const daily = screen.getByRole("link", { name: /每日訓練/ })
  expect(daily.className).toContain("opacity-60")
})
