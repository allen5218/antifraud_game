import { expect, type Page } from "@playwright/test"

export async function signUpNewUser(
  page: Page,
  name: string,
  email: string,
  password: string,
) {
  await page.goto("/signup")

  await page.getByTestId("full-name-input").fill(name)
  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
  await page.getByTestId("confirm-password-input").fill(password)
  await page.getByRole("button", { name: "註冊" }).click()
  await page.goto("/login")
}

export async function logInUser(page: Page, email: string, password: string) {
  await page.goto("/login")

  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
  await page.getByRole("button", { name: "登入" }).click()
  await page.waitForURL("/")
  await expect(page.getByTestId("home-hero")).toBeVisible()
}

export async function logOutUser(page: Page) {
  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "登出" }).click()
  await page.goto("/login")
}

/**
 * 還沒玩過的帳號一進房間會先跳新手導覽，蓋住整個房間。不是在測導覽的測試先按跳過；
 * 已經看過導覽的帳號不會出現，等一下沒看到就算了。
 */
export async function skipTour(page: Page) {
  const skip = page.getByRole("button", { name: "跳過導覽" })
  try {
    await skip.waitFor({ state: "visible", timeout: 5000 })
  } catch {
    return
  }
  await skip.click()
  await expect(page.getByTestId("onboarding-tour")).toBeHidden()
}
