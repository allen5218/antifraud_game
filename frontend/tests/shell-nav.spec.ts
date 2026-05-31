import { expect, test } from "@playwright/test"

test.describe("App shell mobile nav", () => {
  test.use({ viewport: { width: 375, height: 667 } })

  test("can navigate between the 4 tabs", async ({ page }) => {
    await page.goto("/")
    await expect(page.getByText("今日挑戰")).toBeVisible()

    await page.getByTestId("tab-assets").click()
    await expect(page.getByText("總身家")).toBeVisible()

    await page.getByTestId("tab-scenarios").click()
    await expect(page.getByText("真實情境模擬")).toBeVisible()

    await page.getByTestId("tab-me").click()
    await page.getByTestId("tab-home").click()
    await expect(page.getByText("今日挑戰")).toBeVisible()
  })

  test("claiming accrual changes the cash pill", async ({ page }) => {
    await page.goto("/")
    const before = await page.getByTestId("hdr-cash").innerText()
    await page.getByRole("button", { name: /領取/ }).click()
    const after = await page.getByTestId("hdr-cash").innerText()
    expect(after).not.toBe(before)
  })

  test("DEV trigger opens the ForcedSellModal", async ({ page }) => {
    await page.goto("/me")
    await page.getByRole("button", { name: /模擬被詐騙/ }).click()
    await expect(page.getByText(/你被詐騙了/)).toBeVisible()
  })
})
