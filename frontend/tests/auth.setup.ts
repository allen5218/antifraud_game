import { test as setup } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"
import { markTourSeen } from "./utils/user"

const authFile = "playwright/.auth/user.json"

setup("authenticate", async ({ page }) => {
  await page.goto("/login")
  await page.getByTestId("email-input").fill(firstSuperuser)
  await page.getByTestId("password-input").fill(firstSuperuserPassword)
  await page.getByRole("button", { name: "登入" }).click()
  await page.waitForURL("/")
  // 共用的管理員在全新的資料庫還沒玩過，會先看到新手導覽；直接記成看過，之後的測試就不會被擋住
  await markTourSeen(page)
  await page.context().storageState({ path: authFile })
})
