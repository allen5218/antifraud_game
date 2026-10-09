import { afterEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react"
import type { ExamStatus } from "@/client"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { DailyService, ExamService, QuickService } from "@/client/sdk.gen"
import { renderWithRouter } from "@/test/renderWithRouter"
import { DailyPage } from "./daily"

const response = <T,>(value: T) =>
  new CancelablePromise<T>((resolve) => resolve(value))
const qc = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
})
const locked = {
  status: 400,
  body: { detail: { code: "exam_in_progress" } },
}
const status: ExamStatus = {
  active_attempt_id: "attempt-1",
  can_start: false,
  block_reason: "exam_in_progress",
  gate: null,
  daily_used: 0,
  daily_limit: 3,
  badges: [],
}
afterEach(() => {
  cleanup()
  qc.clear()
  mock.restore()
})
test("每日訓練作答被檢測鎖擋下時整頁換成繼續檢測", async () => {
  spyOn(ExamService, "readStatus").mockImplementation(() => response(status))
  spyOn(DailyService, "dailyToday").mockImplementation(() =>
    response({
      day: "2026-10-09",
      status: "ready",
      session_id: "daily-1",
      answered_item_ids: [],
      result: null,
      items: [
        {
          item_id: "q1",
          type: "verdict" as const,
          fraud_type: "shopping",
          title: "今日一則",
          narrative: "請先看今天的說明",
          difficulty: 1,
        },
      ],
    }),
  )
  spyOn(QuickService, "quizAnswer").mockImplementation(
    () => new CancelablePromise((_resolve, reject) => reject(locked)),
  )
  await renderWithRouter(
    <QueryClientProvider client={qc}>
      <DailyPage />
    </QueryClientProvider>,
  )
  fireEvent.click(await screen.findByRole("button", { name: "這是詐騙" }))
  expect((await screen.findByRole("alert")).textContent).toContain(
    "先完成檢測再回來練習",
  )
  expect(screen.queryByText("答案送出失敗，請再試一次")).toBeNull()
  expect(screen.queryByText("請先看今天的說明")).toBeNull()
  await waitFor(() =>
    expect(
      screen.getByRole("link", { name: "繼續檢測" }).getAttribute("href"),
    ).toBe("/exam/attempt-1"),
  )
})
