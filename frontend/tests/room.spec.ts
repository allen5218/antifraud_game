import { expect, test } from "@playwright/test"
import { createUser } from "./utils/privateApi.ts"
import { randomEmail, randomPassword } from "./utils/random"
import {
  closeMascotGuide,
  logInUser,
  skipEstateIntro,
  skipTour,
} from "./utils/user"

// 用新帳號：共用的 superuser 會被其他測試改現金與房產，房間階段就不固定。
// 2026-11 改版後首頁是練習，分頁「經營」（/room）是放置經營；新玩家先在房間看導覽。
// 新玩家固定 1,000 元、送一間雅房；再買一間雅房 1,120、貓 1,500，所以都買不起。
test.describe("房間首頁", () => {
  test.use({
    storageState: { cookies: [], origins: [] },
    viewport: { width: 375, height: 667 },
  })

  test("新玩家在經營分頁先看導覽，房間是起家的雅房，進出手機回首頁", async ({
    page,
  }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    await logInUser(page, email, password)
    // 首頁的提醒也帶去前測
    await expect(
      page.getByTestId("home-reminder").getByRole("link", { name: "開始" }),
    ).toHaveAttribute("href", "/pretest")
    await page.getByTestId("tab-room").click()

    await expect(page.getByTestId("room-bg")).toHaveAttribute(
      "src",
      "/assets/room/1/bg.webp",
    )
    // 新玩家先看到新手導覽，跳過之後吉祥物帶去前測
    await expect(page.getByText("這是你的房間")).toBeVisible()
    await skipTour(page)
    await expect(page.getByRole("link", { name: "開始" })).toHaveAttribute(
      "href",
      "/pretest",
    )

    await closeMascotGuide(page)
    await page.getByTestId("hotspot-phone").click()
    await expect(page).toHaveURL(/\/scenarios/)
    await page.getByRole("link", { name: "回首頁" }).click()
    await expect(page.getByTestId("home-hero")).toBeVisible()
  })

  test("商店買不起貓；經營頁有起家雅房，錢不夠買第二間", async ({ page }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    await logInUser(page, email, password)
    await page.getByTestId("tab-room").click()
    await skipTour(page)
    // 看完導覽留在房間
    await expect(page).toHaveURL(/view=house/)

    await page.getByTestId("room-shop").click()
    await expect(page).toHaveURL(/\/shop/)

    // 用標題完全相符找卡片：「貓」會同時對到「小熊貓」
    const card = (name: string) =>
      page.locator("article").filter({
        has: page.getByRole("heading", { name, exact: true }),
      })
    const shiba = card("柴犬")
    await expect(shiba.getByText("免費")).toBeVisible()
    await expect(shiba.getByRole("button", { name: "展示中" })).toBeDisabled()

    const cat = card("貓")
    await cat.getByRole("button", { name: "購買" }).click()
    await expect(cat.getByText("錢不夠")).toBeVisible()

    // 商店不是分頁本身，沒有底部分頁，直接進經營
    await page.goto("/room")
    await skipEstateIntro(page)
    await expect(page.getByTestId("estate-cash")).toHaveText("1,000 元")
    const shack = page.getByTestId("industry-1")
    await expect(shack.getByText("1 間")).toBeVisible()
    await expect(page.getByTestId("manager-1")).toHaveAccessibleName(/柴犬/)
    await expect(page.getByTestId("buy-1")).toBeDisabled()
  })
})
