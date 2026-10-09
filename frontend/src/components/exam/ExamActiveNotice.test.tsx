import { afterEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react"
import type { ExamState, ExamStatus } from "@/client"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import {
  DailyService,
  EconomyService,
  ExamService,
  PracticeService,
} from "@/client/sdk.gen"
import { Home } from "@/routes/_shell/index"
import { renderWithRouter } from "@/test/renderWithRouter"

const response = <T,>(value: T) =>
  new CancelablePromise<T>((resolve) => resolve(value))
const qc = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
})
const idle: ExamStatus = {
  active_attempt_id: null,
  can_start: true,
  block_reason: null,
  gate: null,
  daily_used: 0,
  daily_limit: 3,
  badges: [],
}
function attempt(mode: ExamState["mode"], fraudType: string | null): ExamState {
  return {
    id: "attempt-1",
    mode,
    status: "active",
    stage: mode === "comprehensive" ? "pretest" : "swipe",
    fraud_type: fraudType,
    expires_at: "2099-01-01T00:00:00Z",
    stage_items: [],
    progress: {
      stage_index: 0,
      stage_count: mode === "comprehensive" ? 4 : 3,
    },
    scenario: null,
    result: null,
  }
}
afterEach(() => {
  cleanup()
  qc.clear()
  mock.restore()
})
async function renderHome() {
  spyOn(EconomyService, "readMe").mockImplementation(() =>
    response({
      cash: 0,
      xp: 0,
      level: 1,
      streak_days: 0,
      pending_accrual: 0,
      bankruptcy_pending: false,
    }),
  )
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
  await renderWithRouter(
    <QueryClientProvider client={qc}>
      <Home />
    </QueryClientProvider>,
  )
}
test("有進行中的專項檢測時，卡在大卡之前，繼續直接進那份卷", async () => {
  const daily = spyOn(DailyService, "dailyToday").mockImplementation(
    () => new CancelablePromise(() => {}),
  )
  spyOn(ExamService, "readStatus").mockImplementation(() =>
    response({
      ...idle,
      active_attempt_id: "attempt-1",
      can_start: false,
      block_reason: "exam_in_progress",
    }),
  )
  spyOn(ExamService, "read").mockImplementation(() =>
    response(attempt("specialized", "atm")),
  )
  await renderHome()
  const heading = await screen.findByRole("heading", {
    name: "你有一份檢測還沒做完",
  })
  expect(await screen.findByText("專項檢測・解除分期")).toBeTruthy()
  expect(
    screen.getByRole("link", { name: "繼續檢測" }).getAttribute("href"),
  ).toBe("/exam/attempt-1")
  const hero = screen.getByTestId("home-hero")
  expect(
    heading.compareDocumentPosition(hero) & Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy()
  expect(daily).not.toHaveBeenCalled()
})
test("綜合檢測還在前測時只寫綜合檢測", async () => {
  spyOn(ExamService, "readStatus").mockImplementation(() =>
    response({
      ...idle,
      active_attempt_id: "attempt-1",
      can_start: false,
      block_reason: "exam_in_progress",
    }),
  )
  spyOn(ExamService, "read").mockImplementation(() =>
    response(attempt("comprehensive", null)),
  )
  await renderHome()
  expect(await screen.findByText("綜合檢測")).toBeTruthy()
  expect(screen.queryByText(/綜合檢測・/)).toBeNull()
  expect(screen.queryByText("其他類型")).toBeNull()
})
test("放棄先確認，繼續作答是主要按鈕，成功後重新讀取檢測與練習", async () => {
  let active = true
  spyOn(ExamService, "readStatus").mockImplementation(() =>
    response(
      active
        ? {
            ...idle,
            active_attempt_id: "attempt-1",
            can_start: false,
            block_reason: "exam_in_progress",
          }
        : idle,
    ),
  )
  spyOn(ExamService, "read").mockImplementation(() =>
    response(attempt("specialized", "shopping")),
  )
  const abandon = spyOn(ExamService, "abandon").mockImplementation(() => {
    active = false
    return response({
      ...attempt("specialized", "shopping"),
      status: "abandoned",
      stage: "done",
    })
  })
  const invalidate = spyOn(qc, "invalidateQueries")
  await renderHome()
  fireEvent.click(await screen.findByRole("button", { name: "放棄" }))
  expect(abandon).not.toHaveBeenCalled()
  expect(screen.getByRole("dialog").textContent).toContain("放棄算一次沒過")
  expect(screen.getByRole("dialog").textContent).toContain(
    "還沒交的關卡以零分計算",
  )
  const keep = screen.getByRole("button", { name: "繼續作答" })
  const drop = screen.getByRole("button", { name: "確定放棄" })
  expect(keep.className).toContain("bg-primary")
  expect(drop.className).not.toContain("bg-primary")
  fireEvent.click(keep)
  expect(abandon).not.toHaveBeenCalled()
  expect(screen.queryByRole("dialog")).toBeNull()
  fireEvent.click(screen.getByRole("button", { name: "放棄" }))
  fireEvent.click(screen.getByRole("button", { name: "確定放棄" }))
  await waitFor(() => expect(abandon).toHaveBeenCalledTimes(1))
  expect(abandon.mock.calls[0][0]).toEqual({ attemptId: "attempt-1" })
  await waitFor(() => {
    const keys = invalidate.mock.calls.map((call) =>
      JSON.stringify(
        (call[0] as { queryKey?: readonly unknown[] } | undefined)?.queryKey,
      ),
    )
    expect(keys).toContain(JSON.stringify(["exam"]))
    expect(keys).toContain(JSON.stringify(["practice"]))
  })
  await waitFor(() =>
    expect(
      screen.queryByRole("heading", { name: "你有一份檢測還沒做完" }),
    ).toBeNull(),
  )
})
test("沒有進行中的檢測時不顯示卡，也不讀每日訓練", async () => {
  const daily = spyOn(DailyService, "dailyToday").mockImplementation(
    () => new CancelablePromise(() => {}),
  )
  spyOn(ExamService, "readStatus").mockImplementation(() => response(idle))
  await renderHome()
  await screen.findByTestId("home-hero")
  expect(
    screen.queryByRole("heading", { name: "你有一份檢測還沒做完" }),
  ).toBeNull()
  expect(daily).not.toHaveBeenCalled()
})
