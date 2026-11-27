import { afterEach, beforeEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import { ApiError } from "@/client/core/ApiError"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { EconomyService } from "@/client/sdk.gen"
import { onboardingApi } from "@/components/room/onboardingApi"
import { type MascotShopItem, mascotApi } from "./mascotApi"
import { ShopPage } from "./ShopPage"

const response = <T,>(value: T) =>
  new CancelablePromise<T>((resolve) => resolve(value))

function item(overrides: Partial<MascotShopItem> = {}): MascotShopItem {
  return {
    id: "cat",
    name: "貓",
    category: "mascot",
    cost: 3000,
    image_url: "/assets/mascot/cat/base.webp",
    owned: false,
    displayed: false,
    ...overrides,
  }
}

let items: MascotShopItem[] = []

function renderShop() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <ShopPage />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  items = [
    item({
      id: "shiba",
      name: "柴犬",
      cost: 0,
      image_url: "/assets/mascot/shiba/base.webp",
      owned: true,
      displayed: true,
    }),
    item(),
  ]
  spyOn(mascotApi, "list").mockImplementation(() => response({ items }))
  spyOn(mascotApi, "purchase").mockImplementation(() => response({}))
  spyOn(mascotApi, "display").mockImplementation(() => response({}))
  spyOn(EconomyService, "readMe").mockImplementation(() =>
    response({
      cash: 12450,
      xp: 0,
      level: 10,
      streak_days: 1,
    }),
  )
})

afterEach(() => {
  cleanup()
  mock.restore()
})

test("買貓錢不夠顯示錢不夠", async () => {
  spyOn(mascotApi, "purchase").mockImplementation(
    () =>
      new CancelablePromise((_resolve, reject) => {
        reject(
          new ApiError(
            { method: "POST", url: "/api/v1/mascot/items/cat/purchase" },
            {
              url: "/api/v1/mascot/items/cat/purchase",
              ok: false,
              status: 400,
              statusText: "Bad Request",
              body: { detail: { code: "insufficient_cash" } },
            },
            "Bad Request",
          ),
        )
      }),
  )
  renderShop()
  fireEvent.click(await screen.findByRole("button", { name: "購買" }))
  expect(await screen.findByText("錢不夠")).toBeTruthy()
})

test("展示中的按鈕停用", async () => {
  renderShop()
  const button = await screen.findByRole("button", { name: "展示中" })
  expect((button as HTMLButtonElement).disabled).toBe(true)
})

test("商店只賣吉祥物，說明可以派去當經理", async () => {
  renderShop()
  expect(await screen.findByText(/派去當經理/)).toBeTruthy()
  expect(screen.queryByRole("tab", { name: "房產" })).toBeNull()
})

test("進商店會記下看過商店（新手任務的一項）", async () => {
  const visited = spyOn(onboardingApi, "shopVisited").mockImplementation(() =>
    response(undefined),
  )
  renderShop()
  await screen.findByText("柴犬")
  expect(visited).toHaveBeenCalledTimes(1)
})
