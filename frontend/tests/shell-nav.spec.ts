import { expect, test } from "@playwright/test"

test.describe("房間導覽", () => {
  test.use({ viewport: { width: 375, height: 667 } })

  test("點房間物件進出，再用回房間回來", async ({ page }) => {
    await page.goto("/")
    await expect(page.getByTestId("home-hero")).toBeVisible()
    await expect(page.getByTestId("hdr-cash")).toBeVisible()

    await page.getByTestId("hotspot-phone").click()
    await expect(page).toHaveURL(/\/scenarios/)
    await expect(page.getByRole("heading", { name: "情境對抗" })).toBeVisible()
    await expect(page.getByTestId("hdr-cash")).toBeHidden()

    await page.getByRole("link", { name: "回房間" }).click()
    await expect(page.getByTestId("home-hero")).toBeVisible()

    await page.getByTestId("room-me").click()
    await expect(page).toHaveURL(/\/me/)
    await page.getByRole("link", { name: "回房間" }).click()
    await expect(page.getByTestId("home-hero")).toBeVisible()

    await page.getByTestId("room-house").click()
    await expect(page.getByText("總身家")).toBeVisible()
    await page.getByRole("link", { name: "回房間" }).click()
    await expect(page.getByTestId("home-hero")).toBeVisible()
  })

  test("桌機改用側欄，沒有底部分頁", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.goto("/")
    await expect(page.getByTestId("home-hero")).toBeVisible()

    await expect(page.getByTestId("tab-home")).toHaveCount(0)
    await expect(page.getByTestId("rail-tab-home")).toBeVisible()

    await page.getByTestId("rail-tab-assets").click()
    await expect(page.getByText("總身家")).toBeVisible()
    await page.getByRole("link", { name: "回房間" }).click()
    await expect(page.getByTestId("home-hero")).toBeVisible()
  })
})
