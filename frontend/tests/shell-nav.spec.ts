import { expect, test } from "@playwright/test"

test.describe("App shell mobile nav", () => {
  test.use({ viewport: { width: 375, height: 667 } })

  test("can navigate between the 4 tabs", async ({ page }) => {
    await page.goto("/")
    await expect(page.getByText("今日挑戰")).toBeVisible()

    await page.getByTestId("tab-assets").click()
    await expect(page.getByText("總身家")).toBeVisible()

    await page.getByTestId("tab-scenarios").click()
    // 這是導覽測試:只驗證切到情境分頁(URL 變更),不綁 inbox API 的內容渲染。
    // 情境頁內容依賴 /scenario/inbox,CI 首次會 bootstrap 5 個 fraud_type 的
    // session(檔案讀取 + DB 寫入),可能超過 5s toBeVisible 逾時;內容渲染另
    // 由該頁專屬測試/單元測試覆蓋,導覽測試以 URL 為穩定判準。
    await expect(page).toHaveURL(/\/scenarios/)

    await page.getByTestId("tab-me").click()
    await page.getByTestId("tab-home").click()
    await expect(page.getByText("今日挑戰")).toBeVisible()
  })

  test("header shows the cash pill on every tab", async ({ page }) => {
    // hdr-cash 位於 _shell 的固定 header(HeaderStatus),各分頁共用。
    // 註:真正的「領取待領收益改變現金」流程需要「已擁有房產 + 至少一個
    // accrual tick(ACCRUAL_TICK_SECONDS = 86400 秒 = 1 天)」才會出現領取
    // 按鈕;新登入的 superuser 兩者皆無,無法在 E2E 決定性觸發。該行為改由
    // 單元測試 frontend/src/components/Home/AccrualBanner.test.tsx 覆蓋。
    await page.goto("/")
    await expect(page.getByTestId("hdr-cash")).toBeVisible()

    await page.getByTestId("tab-assets").click()
    await expect(page.getByTestId("hdr-cash")).toBeVisible()
  })

  // 已移除 "DEV trigger opens the ForcedSellModal":產品 UI 沒有觸發破產彈窗的
  // DEV 按鈕(ForcedSellModal 僅在後端回傳 bankruptcy_pending=true 時渲染,需
  // 在「真實情境」對話中實際匯款觸發,無法在 E2E 決定性觸發)。該彈窗行為由
  // 單元測試 frontend/src/components/shell/ForcedSellModal.test.tsx 覆蓋。
})
