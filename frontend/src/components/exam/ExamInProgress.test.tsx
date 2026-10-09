import { afterEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, screen, waitFor } from "@testing-library/react"
import type { ExamStatus } from "@/client"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { ExamService } from "@/client/sdk.gen"
import { renderWithRouter } from "@/test/renderWithRouter"
import { ExamInProgress } from "./ExamInProgress"

const response = <T,>(value: T) =>
  new CancelablePromise<T>((resolve) => resolve(value))
const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
const status: ExamStatus = {
  active_attempt_id: "attempt-1",
  can_start: false,
  block_reason: "exam_in_progress",
  gate: null,
  daily_used: 1,
  daily_limit: 3,
  badges: [],
}
const locked = {
  status: 400,
  body: { detail: { code: "exam_in_progress" } },
}
afterEach(() => {
  cleanup()
  qc.clear()
  mock.restore()
})
async function mount(error: unknown) {
  await renderWithRouter(
    <QueryClientProvider client={qc}>
      <ExamInProgress error={error} />
    </QueryClientProvider>,
  )
}
test("練習被檢測鎖擋下時直接連到進行中的卷", async () => {
  spyOn(ExamService, "readStatus").mockImplementation(() => response(status))
  await mount(locked)
  expect(screen.getByRole("alert").textContent).toContain(
    "先完成檢測再回來練習",
  )
  await waitFor(() =>
    expect(
      screen.getByRole("link", { name: "繼續檢測" }).getAttribute("href"),
    ).toBe("/exam/attempt-1"),
  )
})
test("讀不到進行中的卷時退回檢測入口", async () => {
  spyOn(ExamService, "readStatus").mockImplementation(
    () =>
      new CancelablePromise((_resolve, reject) => reject(new Error("offline"))),
  )
  await mount(locked)
  await waitFor(() =>
    expect(
      screen.getByRole("link", { name: "繼續檢測" }).getAttribute("href"),
    ).toBe("/exam"),
  )
})
test("一般網路錯誤不冒充檢測鎖", async () => {
  const read = spyOn(ExamService, "readStatus").mockImplementation(() =>
    response(status),
  )
  await mount(new Error("network"))
  expect(screen.queryByRole("alert")).toBeNull()
  expect(read).not.toHaveBeenCalled()
})
