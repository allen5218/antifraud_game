import { afterEach, describe, expect, it } from "bun:test"
import { cleanup, screen } from "@testing-library/react"
import { renderWithRouter } from "@/test/renderWithRouter"
import { PageHeader, pageTitle } from "./PageHeader"

afterEach(() => {
  cleanup()
})

describe("<PageHeader />", () => {
  it("顯示頁名，回房間連到首頁", async () => {
    await renderWithRouter(<PageHeader title="滑卡訓練" />)
    expect(screen.getByRole("heading", { name: "滑卡訓練" })).toBeTruthy()
    expect(
      screen.getByRole("link", { name: "回房間" }).getAttribute("href"),
    ).toBe("/")
  })

  it("各頁頁名", () => {
    expect(pageTitle("/scenarios")).toBe("情境對抗")
    expect(pageTitle("/scenarios/abc")).toBe("情境對抗")
    expect(pageTitle("/quick/swipe")).toBe("滑卡訓練")
    expect(pageTitle("/quick/quiz")).toBe("訊息判讀")
    expect(pageTitle("/daily")).toBe("每日訓練")
    expect(pageTitle("/leaderboard")).toBe("排行榜")
    expect(pageTitle("/exam")).toBe("檢測")
    expect(pageTitle("/exam/attempt-1")).toBe("檢測")
    expect(pageTitle("/assets")).toBe("我的資產")
    expect(pageTitle("/shop")).toBe("商店")
    expect(pageTitle("/me")).toBe("我的")
    expect(pageTitle("/")).toBe("")
  })
})

it("班級管理與班級作業有標題", () => {
  expect(pageTitle("/classes")).toBe("班級管理")
  expect(pageTitle("/classes/abc")).toBe("班級管理")
  expect(pageTitle("/classwork")).toBe("班級作業")
})
