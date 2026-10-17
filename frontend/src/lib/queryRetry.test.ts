import { expect, test } from "bun:test"
import { ApiError } from "@/client"
import { shouldRetryQuery } from "./queryRetry"

function apiError(status: number): ApiError {
  return new ApiError(
    { method: "GET", url: "/api/v1/pretest/questions" },
    {
      url: "/api/v1/pretest/questions",
      ok: false,
      status,
      statusText: "",
      body: {},
    },
    "failed",
  )
}

test("伺服器明確拒絕（4xx）不重試，檢測中的鎖定提示要馬上出現", () => {
  expect(shouldRetryQuery(0, apiError(400))).toBe(false)
  expect(shouldRetryQuery(0, apiError(404))).toBe(false)
})

test("斷線與 5xx 照舊最多重試三次", () => {
  expect(shouldRetryQuery(0, apiError(502))).toBe(true)
  expect(shouldRetryQuery(2, new TypeError("Failed to fetch"))).toBe(true)
  expect(shouldRetryQuery(3, apiError(500))).toBe(false)
})
