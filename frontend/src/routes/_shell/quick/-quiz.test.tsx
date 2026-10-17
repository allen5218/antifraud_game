import { afterEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react"
import type { ExamStatus } from "@/client"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { ExamService, PracticeService, QuickService } from "@/client/sdk.gen"
import { renderWithRouter } from "@/test/renderWithRouter"
import { QuizPage } from "./quiz"

const response = <T,>(value: T) =>
  new CancelablePromise<T>((resolve) => resolve(value))
const reject = (error: unknown) =>
  new CancelablePromise((_resolve, deny) => deny(error))
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
const deck = {
  session_id: "quiz-1",
  items: [
    {
      item_id: "q1",
      type: "verdict" as const,
      fraud_type: "atm",
      title: "一則訊息",
      narrative: "請先看這份說明",
      difficulty: 1,
    },
  ],
}
afterEach(() => {
  cleanup()
  qc.clear()
  mock.restore()
})
async function mount() {
  spyOn(PracticeService, "readProfile").mockImplementation(() =>
    response({
      focus_type: null,
      focus_label: null,
      note: "還沒有作答紀錄。",
      weights: {},
      source: "none",
      answers_seen: 0,
    }),
  )
  spyOn(ExamService, "readStatus").mockImplementation(() => response(status))
  spyOn(QuickService, "quizDeck").mockImplementation(() => response(deck))
  await renderWithRouter(
    <QueryClientProvider client={qc}>
      <QuizPage />
    </QueryClientProvider>,
  )
  await screen.findByRole("button", { name: "這是詐騙" })
}
test("訊息判讀作答被檢測鎖擋下時整頁換成繼續檢測", async () => {
  spyOn(QuickService, "quizAnswer").mockImplementation(() => reject(locked))
  await mount()
  fireEvent.click(screen.getByRole("button", { name: "這是詐騙" }))
  expect((await screen.findByRole("alert")).textContent).toContain(
    "先完成檢測再回來練習",
  )
  expect(screen.queryByText("答案送出失敗，請再試一次")).toBeNull()
  expect(screen.queryByText("請先看這份說明")).toBeNull()
  await waitFor(() =>
    expect(
      screen.getByRole("link", { name: "繼續檢測" }).getAttribute("href"),
    ).toBe("/exam/attempt-1"),
  )
})
test("訊息判讀一般送出失敗仍留在題目上", async () => {
  spyOn(QuickService, "quizAnswer").mockImplementation(() =>
    reject(new Error("network")),
  )
  await mount()
  fireEvent.click(screen.getByRole("button", { name: "這是詐騙" }))
  expect(await screen.findByText("答案送出失敗，請再試一次")).toBeTruthy()
  expect(screen.getByText("請先看這份說明")).toBeTruthy()
  expect(screen.queryByText("先完成檢測再回來練習")).toBeNull()
})
