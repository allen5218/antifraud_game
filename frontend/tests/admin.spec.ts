import { expect, test } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

test("Admin page is accessible and shows correct title", async ({ page }) => {
  await page.goto("/admin")
  await expect(
    page.getByRole("heading", { name: "使用者", exact: true }),
  ).toBeVisible()
  await expect(page.getByText("管理帳號與權限")).toBeVisible()
})

test("Add User button is visible", async ({ page }) => {
  await page.goto("/admin")
  await expect(page.getByRole("button", { name: "新增使用者" })).toBeVisible()
})

test.describe("Admin user management", () => {
  test("Create a new user successfully", async ({ page }) => {
    await page.goto("/admin")

    const email = randomEmail()
    const password = randomPassword()
    const fullName = "Test User Admin"

    await page.getByRole("button", { name: "新增使用者" }).click()

    await page.getByPlaceholder("電子郵件").fill(email)
    await page.getByPlaceholder("名稱").fill(fullName)
    await page.getByPlaceholder("密碼", { exact: true }).first().fill(password)
    await page.getByPlaceholder("密碼", { exact: true }).last().fill(password)

    await page.getByRole("button", { name: "儲存" }).click()

    await expect(page.getByText("已新增使用者")).toBeVisible()

    await expect(page.getByRole("dialog")).not.toBeVisible()

    const userRow = page.getByRole("row").filter({ hasText: email })
    await expect(userRow).toBeVisible()
  })

  test("Create a superuser", async ({ page }) => {
    await page.goto("/admin")

    const email = randomEmail()
    const password = randomPassword()

    await page.getByRole("button", { name: "新增使用者" }).click()

    await page.getByPlaceholder("電子郵件").fill(email)
    await page.getByPlaceholder("密碼", { exact: true }).first().fill(password)
    await page.getByPlaceholder("密碼", { exact: true }).last().fill(password)
    await page.getByLabel("管理員").check()
    await page.getByLabel("啟用").check()

    await page.getByRole("button", { name: "儲存" }).click()

    await expect(page.getByText("已新增使用者")).toBeVisible()

    await expect(page.getByRole("dialog")).not.toBeVisible()

    const userRow = page.getByRole("row").filter({ hasText: email })
    await expect(userRow.getByText("管理員")).toBeVisible()
  })

  test("Edit a user successfully", async ({ page }) => {
    await page.goto("/admin")

    const email = randomEmail()
    const password = randomPassword()
    const originalName = "Original Name"
    const updatedName = "Updated Name"

    await page.getByRole("button", { name: "新增使用者" }).click()
    await page.getByPlaceholder("電子郵件").fill(email)
    await page.getByPlaceholder("名稱").fill(originalName)
    await page.getByPlaceholder("密碼", { exact: true }).first().fill(password)
    await page.getByPlaceholder("密碼", { exact: true }).last().fill(password)
    await page.getByRole("button", { name: "儲存" }).click()

    await expect(page.getByText("已新增使用者")).toBeVisible()
    await expect(page.getByRole("dialog")).not.toBeVisible()

    const userRow = page.getByRole("row").filter({ hasText: email })
    await userRow.getByRole("button").click()

    await page.getByRole("menuitem", { name: "編輯使用者" }).click()

    await page.getByPlaceholder("名稱").fill(updatedName)
    await page.getByRole("button", { name: "儲存" }).click()

    await expect(page.getByText("已更新使用者")).toBeVisible()
    await expect(page.getByText(updatedName)).toBeVisible()
  })

  test("Delete a user successfully", async ({ page }) => {
    await page.goto("/admin")

    const email = randomEmail()
    const password = randomPassword()

    await page.getByRole("button", { name: "新增使用者" }).click()
    await page.getByPlaceholder("電子郵件").fill(email)
    await page.getByPlaceholder("密碼", { exact: true }).first().fill(password)
    await page.getByPlaceholder("密碼", { exact: true }).last().fill(password)
    await page.getByRole("button", { name: "儲存" }).click()

    await expect(page.getByText("已新增使用者")).toBeVisible()

    await expect(page.getByRole("dialog")).not.toBeVisible()

    const userRow = page.getByRole("row").filter({ hasText: email })
    await userRow.getByRole("button").click()

    await page.getByRole("menuitem", { name: "刪除使用者" }).click()

    await page.getByRole("button", { name: "刪除", exact: true }).click()

    await expect(page.getByText("已刪除使用者")).toBeVisible()

    await expect(
      page.getByRole("row").filter({ hasText: email }),
    ).not.toBeVisible()
  })

  test("Cancel user creation", async ({ page }) => {
    await page.goto("/admin")

    await page.getByRole("button", { name: "新增使用者" }).click()
    await page.getByPlaceholder("電子郵件").fill("test@example.com")

    await page.getByRole("button", { name: "取消" }).click()

    await expect(page.getByRole("dialog")).not.toBeVisible()
  })

  test("Email is required and must be valid", async ({ page }) => {
    await page.goto("/admin")

    await page.getByRole("button", { name: "新增使用者" }).click()

    await page.getByPlaceholder("電子郵件").fill("invalid-email")
    await page.getByPlaceholder("電子郵件").blur()

    await expect(page.getByText("電子郵件格式不正確")).toBeVisible()
  })

  test("密碼至少要 8 個字元", async ({ page }) => {
    await page.goto("/admin")

    await page.getByRole("button", { name: "新增使用者" }).click()

    await page.getByPlaceholder("電子郵件").fill(randomEmail())
    await page.getByPlaceholder("密碼", { exact: true }).first().fill("short")
    await page.getByPlaceholder("密碼", { exact: true }).last().fill("short")
    await page.getByRole("button", { name: "儲存" }).click()

    await expect(page.getByText("密碼至少要 8 個字元")).toBeVisible()
  })

  test("Passwords must match", async ({ page }) => {
    await page.goto("/admin")

    await page.getByRole("button", { name: "新增使用者" }).click()

    await page.getByPlaceholder("電子郵件").fill(randomEmail())
    await page
      .getByPlaceholder("密碼", { exact: true })
      .first()
      .fill(randomPassword())
    await page
      .getByPlaceholder("密碼", { exact: true })
      .last()
      .fill("different12345")
    await page.getByPlaceholder("密碼", { exact: true }).last().blur()

    await expect(page.getByText("兩次輸入的密碼不一樣")).toBeVisible()
  })
})

test.describe("Admin page access control", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Non-superuser cannot access admin page", async ({ page }) => {
    const email = randomEmail()
    const password = randomPassword()

    await createUser({ email, password })
    await logInUser(page, email, password)

    await page.goto("/admin")

    await expect(
      page.getByRole("heading", { name: "使用者", exact: true }),
    ).not.toBeVisible()
    await expect(page).not.toHaveURL(/\/admin/)
  })

  test("Superuser can access admin page", async ({ page }) => {
    await logInUser(page, firstSuperuser, firstSuperuserPassword)

    await page.goto("/admin")

    await expect(
      page.getByRole("heading", { name: "使用者", exact: true }),
    ).toBeVisible()
  })
})
