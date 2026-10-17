import { afterEach, beforeEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import type { PropertyTierPublic } from "@/client"
import { ApiError } from "@/client/core/ApiError"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { EconomyService } from "@/client/sdk.gen"
import { type MascotShopItem, mascotApi } from "./mascotApi"
import { ShopPage } from "./ShopPage"

const response = <T,>(value: T) =>
  new CancelablePromise<T>((resolve) => resolve(value))

const TIERS: PropertyTierPublic[] = [
  ["雅房", "tier-1", 1000, 5, 1],
  ["套房", "tier-2", 5000, 35, 1],
  ["兩房公寓", "tier-3", 25000, 250, 2],
  ["三房公寓", "tier-4", 100000, 1200, 3],
  ["別墅", "tier-5", 300000, 4200, 5],
  ["豪宅", "tier-6", 1000000, 15000, 10],
].map(([name, svg_key, price, daily_income, unlock_level], index) => ({
  id: index + 1,
  name: name as string,
  svg_key: svg_key as string,
  price: price as number,
  daily_income: daily_income as number,
  unlock_level: unlock_level as number,
}))

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
      pending_accrual: 0,
      bankruptcy_pending: false,
    }),
  )
  spyOn(EconomyService, "listProperties").mockImplementation(() =>
    response({ tiers: TIERS, owned: [] }),
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

test("房產分頁列出六級", async () => {
  renderShop()
  fireEvent.click(await screen.findByRole("tab", { name: "房產" }))
  for (const name of ["雅房", "套房", "兩房公寓", "三房公寓", "別墅", "豪宅"]) {
    expect(await screen.findByRole("heading", { name })).toBeTruthy()
  }
})
