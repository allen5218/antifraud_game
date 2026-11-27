import { expect, type Page } from "@playwright/test"

export async function signUpNewUser(
  page: Page,
  name: string,
  email: string,
  password: string,
) {
  await page.goto("/signup")

  await page.getByTestId("full-name-input").fill(name)
  await page.getByTestId("birth-year-input").fill("1990")
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

// 直接告訴後端「看過導覽」，不等畫面出現（房間資料慢時導覽會晚於任何固定的等待時間才出現）
export async function markTourSeen(page: Page) {
  const token = await page.evaluate(() => localStorage.getItem("access_token"))
  const response = await page.request.post(
    `${process.env.VITE_API_URL}/api/v1/onboarding/tour`,
    { headers: { Authorization: `Bearer ${token}` } },
  )
  expect(response.ok()).toBeTruthy()
}

/**
 * 還沒有出生年的帳號一進來會被「你是哪一年出生的」蓋住。共用的管理員直接用 API 填好；
 * 已經填過（不管哪一年）後端回 400 birth_year_locked，也算好了。
 */
export async function markBirthYear(page: Page, birthYear = 1990) {
  const token = await page.evaluate(() => localStorage.getItem("access_token"))
  const response = await page.request.post(
    `${process.env.VITE_API_URL}/api/v1/users/me/birth-year`,
    {
      headers: { Authorization: `Bearer ${token}` },
      data: { birth_year: birthYear },
    },
  )
  expect(response.ok() || response.status() === 400).toBeTruthy()
}

/**
 * 房間的吉祥物對話框每天第一次進來會自動打開。分頁列讓房間變矮後，
 * 對話框會蓋到家具，要點家具前先按「收起」；沒打開就算了。
 */
// 第一次進經營頁會先跳玩法說明，舊帳號接著還有一次換算說明
export async function skipEstateIntro(page: Page) {
  await expect(page.getByTestId("estate-page")).toBeVisible()
  const skip = page.getByRole("button", { name: "跳過說明" })
  try {
    await skip.waitFor({ state: "visible", timeout: 3000 })
    await skip.click()
  } catch {
    // 這個瀏覽器看過說明了
  }
  const legacy = page.getByRole("button", { name: "知道了" })
  if (await legacy.isVisible()) await legacy.click()
}

export async function closeMascotGuide(page: Page) {
  const close = page.getByRole("button", { name: "收起" })
  if (await close.isVisible()) await close.click()
}
