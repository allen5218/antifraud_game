import { expect, test } from "@playwright/test"
import { createUser } from "./utils/privateApi.ts"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

// 用新帳號：共用的 superuser 會被其他測試改現金與房產，房間階段就不固定。
// 新玩家固定 1,000 元，雅房剛好 1,000、貓 3,000，所以結果每次都一樣。
test.describe("房間首頁", () => {
  test.use({
    storageState: { cookies: [], origins: [] },
    viewport: { width: 375, height: 667 },
  })

  test("新玩家看到破舊房間與前測引導，進出手機回房間", async ({ page }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    await logInUser(page, email, password)

    const frame = page.getByTestId("room-frame")
    await expect(frame.locator("img").first()).toHaveAttribute(
      "src",
      /stage-0\.webp$/,
    )
    await expect(page.getByRole("link", { name: "開始" })).toHaveAttribute(
      "href",
      "/pretest",
    )

    await page.getByTestId("hotspot-phone").click()
    await expect(page).toHaveURL(/\/scenarios/)
    await page.getByRole("link", { name: "回房間" }).click()
    await expect(page.getByTestId("home-hero")).toBeVisible()
  })

  test("商店買不起貓、買雅房後房間換成雅房", async ({ page }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    await logInUser(page, email, password)

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

    await page.getByRole("tab", { name: "房產" }).click()
    const room = page.locator("div.rounded-xl", { hasText: "雅房" })
    await room.getByRole("button", { name: "購買" }).click()
    await expect(room.getByText("已有")).toBeVisible()

    await page.getByRole("link", { name: "回房間" }).click()
    await expect(
      page.getByTestId("room-frame").locator("img").first(),
    ).toHaveAttribute("src", /stage-1\.webp$/)
    await expect(page.getByTestId("hdr-cash")).toHaveText("0")
  })
})
