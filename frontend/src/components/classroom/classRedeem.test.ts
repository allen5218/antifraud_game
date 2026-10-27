import { afterEach, beforeEach, expect, mock, spyOn, test } from "bun:test"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { INVITE_SESSION_PREFIX } from "@/lib/inviteSession"
import { redeemClassOnce } from "./classRedeem"
import { classApi } from "./classroomApi"

let calls = 0

beforeEach(() => {
  localStorage.clear()
  calls = 0
  spyOn(classApi, "redeem").mockImplementation(() => {
    calls++
    return new CancelablePromise((resolve) =>
      resolve({ access_token: `token-${calls}`, token_type: "bearer" }),
    )
  })
})

afterEach(() => {
  localStorage.clear()
  mock.restore()
})

test("第一次兌換開新帳號並記下，同一個瀏覽器再掃沿用", async () => {
  expect(await redeemClassOnce("abc")).toBe("token-1")
  const saved = localStorage.getItem(`${INVITE_SESSION_PREFIX}class:abc`)
  expect(saved).toContain("token-1")
  expect(await redeemClassOnce("abc")).toBe("token-1")
  expect(calls).toBe(1)
})

test("記下的憑證過期就重新兌換", async () => {
  localStorage.setItem(
    `${INVITE_SESSION_PREFIX}class:abc`,
    JSON.stringify({ accessToken: "old", expiresAt: Date.now() - 1 }),
  )
  expect(await redeemClassOnce("abc")).toBe("token-1")
})
