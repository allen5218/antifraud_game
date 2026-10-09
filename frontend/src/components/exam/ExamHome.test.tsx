import { afterEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react"
import type { ExamStatus } from "@/client"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { ExamService } from "@/client/sdk.gen"
import { renderWithRouter } from "@/test/renderWithRouter"
import { ExamHome } from "./ExamHome"

const response = <T,>(value: T) =>
  new CancelablePromise<T>((resolve) => resolve(value))
const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
const status: ExamStatus = {
  active_attempt_id: null,
  can_start: true,
  block_reason: null,
  gate: null,
  daily_used: 1,
  daily_limit: 3,
  badges: [],
}
afterEach(() => {
  cleanup()
  qc.clear()
  mock.restore()
})
async function mount(value = status) {
  spyOn(ExamService, "readStatus").mockImplementation(() => response(value))
  spyOn(ExamService, "history").mockImplementation(() => response([]))
  await renderWithRouter(
    <QueryClientProvider client={qc}>
      <ExamHome />
    </QueryClientProvider>,
  )
  await screen.findByText("開始專項檢測")
}
test("每日剩餘次數與空徽章狀態，專項傳玩家選的類型", async () => {
  const start = spyOn(ExamService, "start").mockImplementation(
    () =>
      new CancelablePromise((_resolve, reject) =>
        reject({ body: { detail: { code: "exam_unavailable" } } }),
      ),
  )
  await mount()
  expect(screen.getByText(/今天還能檢測 2 次/)).toBeTruthy()
  expect(screen.getByText("還沒有徽章，檢測達七十分就能獲得。")).toBeTruthy()
  fireEvent.change(screen.getByRole("combobox", { name: "檢測類型" }), {
    target: { value: "romance" },
  })
  fireEvent.click(screen.getByRole("button", { name: "開始專項檢測" }))
  await waitFor(() => expect(start).toHaveBeenCalledTimes(1))
  expect(start.mock.calls[0][0]).toEqual({
    requestBody: { mode: "specialized", fraud_type: "romance" },
  })
  await screen.findByText("檢測題目還沒準備好，請稍後再試。")
})
test("進行中的檢測可繼續，兩種新檢測都鎖住", async () => {
  spyOn(ExamService, "read").mockImplementation(() =>
    response({
      id: "a",
      mode: "specialized",
      status: "active",
      stage: "swipe",
      fraud_type: "atm",
      expires_at: "2099-01-01T00:00:00Z",
      stage_items: [],
      progress: { stage_index: 0, stage_count: 3 },
      scenario: null,
      result: null,
    }),
  )
  await mount({
    ...status,
    active_attempt_id: "a",
    can_start: false,
    block_reason: "exam_in_progress",
  })
  expect(await screen.findByText("專項檢測・解除分期")).toBeTruthy()
  expect(screen.getByRole("link", { name: "繼續檢測" })).toBeTruthy()
  expect(
    (screen.getByRole("button", { name: "開始綜合檢測" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true)
  expect(
    (screen.getByRole("button", { name: "開始專項檢測" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true)
})
test("每日用完以白話說明，不開新檢測", async () => {
  await mount({
    ...status,
    can_start: false,
    daily_used: 3,
    block_reason: "exam_daily_limit",
  })
  expect(screen.getByRole("alert").textContent).toContain("明天再來")
})
