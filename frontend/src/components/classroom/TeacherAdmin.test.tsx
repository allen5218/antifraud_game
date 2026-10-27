import { afterEach, beforeEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react"
import type { TeacherPublic } from "@/client"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { teacherApi } from "./classroomApi"
import { TeacherAdmin } from "./TeacherAdmin"

const response = <T,>(value: T) =>
  new CancelablePromise<T>((resolve) => resolve(value))

function teacher(overrides: Partial<TeacherPublic>): TeacherPublic {
  return {
    id: "t1",
    email: "t@example.com",
    full_name: "林老師",
    school: "範例國中",
    subject: "公民",
    status: "pending",
    applied_at: "2026-10-27T10:00:00Z",
    class_count: 0,
    student_count: 0,
    ...overrides,
  }
}

let rows: TeacherPublic[] = []

beforeEach(() => {
  rows = [
    teacher({}),
    teacher({
      id: "t2",
      full_name: "陳老師",
      status: "approved",
      class_count: 2,
      student_count: 30,
    }),
  ]
  spyOn(teacherApi, "list").mockImplementation((status) =>
    response(rows.filter((r) => r.status === status)),
  )
  spyOn(teacherApi, "change").mockImplementation((userId, action) => {
    const row = rows.find((r) => r.id === userId)!
    row.status = {
      approve: "approved",
      reject: "rejected",
      suspend: "suspended",
      restore: "approved",
    }[action]
    return response(row)
  })
})

afterEach(() => {
  cleanup()
  mock.restore()
})

function renderAdmin() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={qc}>
      <TeacherAdmin />
    </QueryClientProvider>,
  )
}

test("審核中列出申請，按核准後從列表消失", async () => {
  renderAdmin()
  expect(await screen.findByText("林老師")).toBeTruthy()
  expect(screen.getByText(/範例國中・公民/)).toBeTruthy()
  fireEvent.click(screen.getByRole("button", { name: "核准" }))
  await waitFor(() =>
    expect(teacherApi.change).toHaveBeenCalledWith("t1", "approve"),
  )
  await waitFor(() => expect(screen.queryByText("林老師")).toBeNull())
})

test("切到已核准看班級數，可以停權", async () => {
  renderAdmin()
  fireEvent.click(await screen.findByRole("tab", { name: /已核准/ }))
  expect(await screen.findByText("陳老師")).toBeTruthy()
  expect(screen.getByText(/2 個班・30 位學生/)).toBeTruthy()
  fireEvent.click(screen.getByRole("button", { name: "停權" }))
  await waitFor(() =>
    expect(teacherApi.change).toHaveBeenCalledWith("t2", "suspend"),
  )
})
