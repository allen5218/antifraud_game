import { afterEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, render, screen } from "@testing-library/react"
import type { ClassMemberDetail } from "@/client"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { classApi } from "./classroomApi"
import { StudentDetail } from "./StudentDetail"

afterEach(() => {
  cleanup()
  mock.restore()
})

test("作業狀態不重複寫「還沒做」，有進度才補在後面", async () => {
  const detail: ClassMemberDetail = {
    user_id: "u1",
    student_number: "S2",
    student_name: "陳小華",
    joined_at: "2026-10-28T00:00:00Z",
    last_active_at: null,
    exams: [],
    practice: [],
    assignments: [
      {
        id: "a1",
        title: "入門前測",
        kind: "pretest",
        params: {},
        due_at: "2026-10-27T15:59:59Z",
        status: "overdue",
        progress_text: "還沒做",
        completed_at: null,
      },
      {
        id: "a2",
        title: "練習",
        kind: "practice",
        params: {},
        due_at: "2026-11-02T15:59:59Z",
        status: "todo",
        progress_text: "訊息判讀 1／3",
        completed_at: null,
      },
    ],
  }
  spyOn(classApi, "member").mockImplementation(
    () => new CancelablePromise((resolve) => resolve(detail)),
  )
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={qc}>
      <StudentDetail
        classId="c1"
        member={{
          user_id: "u1",
          student_number: "S2",
          student_name: "陳小華",
          joined_at: "2026-10-28T00:00:00Z",
          last_active_at: null,
          latest_exam_score: null,
        }}
        onClose={() => {}}
      />
    </QueryClientProvider>,
  )
  expect(await screen.findByText("已過期，還沒做")).toBeTruthy()
  expect(screen.getByText("還沒做・訊息判讀 1／3")).toBeTruthy()
})
