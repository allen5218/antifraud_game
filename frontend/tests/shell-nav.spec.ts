import { expect, test } from "@playwright/test"
import { closeMascotGuide, skipEstateIntro } from "./utils/user"

test.describe("首頁與分頁", () => {
  test.use({ viewport: { width: 375, height: 667 } })

  test("首頁是練習；經營分頁進我的家，點家具進出，再用回首頁回來", async ({
    page,
  }) => {
    await page.goto("/")
    await expect(page.getByTestId("home-hero")).toBeVisible()
    await expect(page.getByTestId("continue-practice")).toBeVisible()

    await page.getByTestId("tab-room").click()
    await skipEstateIntro(page)
    await expect(page.getByTestId("estate-total")).toBeVisible()
    await page.getByTestId("estate-house").click()
    await expect(page.getByTestId("room-hero")).toBeVisible()
    await expect(page.getByTestId("hdr-cash")).toBeVisible()

    await closeMascotGuide(page)
    await page.getByTestId("hotspot-phone").click()
    await expect(page).toHaveURL(/\/scenarios/)
    await expect(page.getByRole("heading", { name: "情境對抗" })).toBeVisible()
    await expect(page.getByTestId("hdr-cash")).toBeHidden()

    await page.getByRole("link", { name: "回首頁" }).click()
    await expect(page.getByTestId("home-hero")).toBeVisible()

    await page.getByTestId("tab-room").click()
    await expect(page.getByTestId("estate-page")).toBeVisible()

    await page.getByTestId("tab-me").click()
    await expect(page).toHaveURL(/\/me/)
  })

  test("繼續練習進卡片練習，答一張看到解說", async ({ page }) => {
    await page.goto("/")
    await page.getByTestId("continue-practice").click()
    await expect(page).toHaveURL(/\/learn/)
    const card = page.getByTestId("card")
    await expect(card).toBeVisible()
    // 單選類的題型點第一個選項就送出；排順序、配對先略過，換下一輪就好
    const choices = card.getByTestId("card-choices").getByRole("button")
    if ((await choices.count()) > 0) {
      await choices.first().click()
      await expect(page.getByTestId("card-feedback")).toBeVisible()
    }
  })

  test("桌機改用側欄，底部分頁藏起來", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.goto("/")
    await expect(page.getByTestId("home-hero")).toBeVisible()

    await expect(page.getByTestId("tab-learn")).toBeHidden()
    await expect(page.getByTestId("rail-tab-learn")).toBeVisible()

    await page.getByTestId("rail-tab-room").click()
    await expect(page.getByTestId("estate-page")).toBeVisible()
    await page.getByTestId("rail-tab-learn").click()
    await expect(page.getByTestId("home-hero")).toBeVisible()
  })
})
