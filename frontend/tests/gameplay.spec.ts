import { expect, test } from "@playwright/test"
import type { QuizCompleteResponse, QuizDeckResponse } from "../src/client"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

test.use({ storageState: { cookies: [], origins: [] } })

test("原題組逐題作答揭曉，結算收據與錢包一致，配裝重新載入仍保留", async ({
  page,
  request,
}) => {
  test.setTimeout(90000)
  const email = randomEmail()
  const password = randomPassword()
  await createUser({ email, password })
  await logInUser(page, email, password)
  const token = await page.evaluate(() => localStorage.getItem("access_token"))
  const headers = {
    Authorization: `Bearer ${token}`,
    "X-ScamGym-Client-Version": "2",
  }
  const wallet = async () => {
    const response = await request.get(
      `${process.env.VITE_API_URL}/api/v1/economy/me`,
      { headers },
    )
    expect(response.ok()).toBeTruthy()
    return response.json()
  }
  // 這個流程要真的題庫。CI 的 E2E 資料庫不灌訊息判讀題庫（game_cases，
  // 見 CLAUDE.md「資料邊界」），拿不到題目就略過；灌了題庫的環境會跑完整流程。
  const probe = await request.get(
    `${process.env.VITE_API_URL}/api/v1/quick/quiz/deck`,
    { headers },
  )
  test.skip(!probe.ok(), "這個環境沒有灌訊息判讀題庫（game_cases）")
  const before = await wallet()
  const deckResponse = page.waitForResponse(
    (r) =>
      r.url().includes("/quick/quiz/deck") && r.request().method() === "GET",
  )
  await page.goto("/quick/quiz")
  const deck: QuizDeckResponse = await (await deckResponse).json()
  expect(deck.items.length).toBeGreaterThan(0)
  for (const [index, item] of deck.items.entries()) {
    if (item.type === "verdict") {
      await page.getByRole("button", { name: "這是詐騙", exact: true }).click()
    } else {
      const send = page.getByRole("button", { name: "送出答案", exact: true })
      // 話術題原本就允許「沒有話術」的空選擇，維持原有答題規則。
      if (item.type !== "tactics") await expect(send).toBeDisabled()
      if (item.type === "verification") {
        // 原生 radio 使用 sr-only；點玩家實際看見的選項文字。
        await page.getByText(item.options[0].text, { exact: true }).click()
      } else if (item.type === "tactics") {
        await page.getByRole("checkbox").first().check()
      } else if (item.type === "match") {
        for (const [i, prompt] of item.match_prompts.entries()) {
          await page
            .getByRole("button", {
              name: `${i + 1}.${prompt.text}`,
              exact: true,
            })
            .click()
          await page
            .getByRole("button", {
              name: item.match_targets[i].label,
              exact: true,
            })
            .click()
        }
      }
      await expect(send).toBeEnabled()
      await send.click()
    }
    const next = page.getByRole("button", {
      name: index === deck.items.length - 1 ? "看結算" : "下一題",
      exact: true,
    })
    await expect(next).toBeVisible()
    if (index < deck.items.length - 1) await next.click()
  }
  const completion = page.waitForResponse(
    (r) =>
      r.url().endsWith("/quick/quiz/complete") &&
      r.request().method() === "POST",
  )
  await page.getByRole("button", { name: "看結算", exact: true }).click()
  const response = await completion
  expect(response.status()).toBe(200)
  const result: QuizCompleteResponse = await response.json()
  await expect(page.getByText("倍率加成結算", { exact: true })).toBeVisible()
  expect(result.reward_receipt?.final.cash_total).toBe(result.cash_earned)
  expect(BigInt((await wallet()).cash) - BigInt(before.cash)).toBe(
    BigInt(result.cash_earned),
  )
  await page.goto("/progression")
  await page.getByRole("button", { name: "裝備", exact: true }).first().click()
  await expect(
    page.getByRole("button", { name: "卸下", exact: true }),
  ).toHaveCount(1)
  await page.reload()
  await expect(
    page.getByRole("button", { name: "卸下", exact: true }),
  ).toHaveCount(1)
})
