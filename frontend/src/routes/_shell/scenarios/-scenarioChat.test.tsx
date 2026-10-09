import { afterEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react"
import type { ExamStatus, ScenarioDetail } from "@/client"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { ExamService, PracticeService, ScenarioService } from "@/client/sdk.gen"
import { renderWithRouter } from "@/test/renderWithRouter"
import { ScenarioChatPage } from "./$scenarioId"

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
const detail: ScenarioDetail = {
  id: "s1",
  fraud_type: "romance",
  display_name: "聯絡人",
  avatar: "romance-1",
  status: "active",
  outcome: null,
  player_turns: 0,
  max_turns: 8,
  history: [
    { role: "npc", messages: ["你好，請先看說明。"], decision_point: null },
  ],
}
afterEach(() => {
  cleanup()
  qc.clear()
  mock.restore()
})
async function mount() {
  spyOn(ExamService, "readStatus").mockImplementation(() => response(status))
  spyOn(ScenarioService, "readScenario").mockImplementation(() =>
    response(detail),
  )
  spyOn(ScenarioService, "inbox").mockImplementation(() => response([]))
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
      <ScenarioChatPage scenarioId="s1" />
    </QueryClientProvider>,
  )
  await screen.findByRole("button", { name: "送出" })
}
test("練習情境送訊息被檢測鎖擋下時整頁換成繼續檢測", async () => {
  spyOn(ScenarioService, "sendMessage").mockImplementation(() => reject(locked))
  await mount()
  fireEvent.change(screen.getByRole("textbox"), {
    target: { value: "請先說明來源" },
  })
  fireEvent.click(screen.getByRole("button", { name: "送出" }))
  expect((await screen.findByRole("alert")).textContent).toContain(
    "先完成檢測再回來練習",
  )
  expect(screen.queryByText("訊息沒送出，請再試一次")).toBeNull()
  expect(screen.queryByRole("button", { name: "送出" })).toBeNull()
  await waitFor(() =>
    expect(
      screen.getByRole("link", { name: "繼續檢測" }).getAttribute("href"),
    ).toBe("/exam/attempt-1"),
  )
})
test("練習情境下判斷被檢測鎖擋下時整頁換成繼續檢測", async () => {
  spyOn(ScenarioService, "judgeScenario").mockImplementation(() =>
    reject(locked),
  )
  await mount()
  fireEvent.click(screen.getByRole("button", { name: "下判斷" }))
  fireEvent.click(
    screen.getByRole("button", { name: "這是詐騙（檢舉並封鎖）" }),
  )
  expect((await screen.findByRole("alert")).textContent).toContain(
    "先完成檢測再回來練習",
  )
  expect(screen.queryByRole("button", { name: "下判斷" })).toBeNull()
  await waitFor(() =>
    expect(
      screen.getByRole("link", { name: "繼續檢測" }).getAttribute("href"),
    ).toBe("/exam/attempt-1"),
  )
})
