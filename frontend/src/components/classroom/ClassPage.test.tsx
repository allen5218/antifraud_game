import { afterEach, beforeEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react"
import type { ClassMemberPublic, ClassOverview } from "@/client"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { AssignmentForm } from "./AssignmentForm"
import { AssignmentList } from "./AssignmentList"
import { ClassOverviewCard } from "./ClassOverviewCard"
import { classApi } from "./classroomApi"
import { RosterTable } from "./RosterTable"

const response = <T,>(value: T) =>
  new CancelablePromise<T>((resolve) => resolve(value))

const accuracy = [
  { fraud_type: "investment", accuracy: 0.8, n: 10 },
  { fraud_type: "fake-sale", accuracy: 0.7, n: 10 },
  { fraud_type: "shopping", accuracy: 0.6, n: 10 },
  { fraud_type: "romance", accuracy: 0.333, n: 9 },
  { fraud_type: "atm", accuracy: null, n: 0 },
]

function overview(overrides: Partial<ClassOverview> = {}): ClassOverview {
  return {
    member_count: 3,
    type_accuracy: accuracy,
    accuracy_n: 2,
    weakest: ["romance"],
    assignments: [
      {
        id: "a1",
        kind: "pretest",
        title: "入門前測",
        params: {},
        due_at: "2026-11-02T15:59:59Z",
        created_at: "2026-10-27T00:00:00Z",
        done: 1,
        late: 1,
        pending: [
          {
            user_id: "u3",
            student_number: "3",
            student_name: "丙",
            status: "overdue",
            progress_text: "還沒做",
          },
        ],
        late_students: [
          {
            user_id: "u2",
            student_number: "2",
            student_name: "乙",
            status: "late",
            progress_text: "完成",
          },
        ],
      },
    ],
    ...overrides,
  }
}

const members: ClassMemberPublic[] = [
  {
    user_id: "u1",
    student_number: "S1",
    student_name: "王小明",
    joined_at: "2026-10-27T00:00:00Z",
    last_active_at: null,
    latest_exam_score: 72,
  },
]

function wrap(node: React.ReactNode) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(<QueryClientProvider client={qc}>{node}</QueryClientProvider>)
}

beforeEach(() => {
  spyOn(classApi, "createAssignment").mockImplementation(() =>
    response({} as never),
  )
  spyOn(classApi, "removeMember").mockImplementation(() =>
    response({ message: "removed" }),
  )
})

afterEach(() => {
  cleanup()
  mock.restore()
})

test("最弱一類寫成一句話，並寫用了幾位學生", () => {
  wrap(<ClassOverviewCard data={overview()} />)
  expect(screen.getByText("全班最弱：假交友（答對 33%）")).toBeTruthy()
  expect(screen.getByText("依 2 位學生最近一次的前測")).toBeTruthy()
})

test("沒有人做過前測時說明", () => {
  wrap(
    <ClassOverviewCard
      data={overview({ weakest: [], accuracy_n: 0, type_accuracy: [] })}
    />,
  )
  expect(screen.getByText(/還沒有學生做過前測/)).toBeTruthy()
})

test("作業卡寫完成人數，展開看還沒完成與遲交名單", () => {
  wrap(<AssignmentList classId="c1" data={overview()} />)
  const card = screen.getByTestId("assignment-a1")
  expect(within(card).getByText("完成 1／3・遲交 1")).toBeTruthy()
  fireEvent.click(within(card).getByRole("button", { name: /還沒完成 1 人/ }))
  expect(within(card).getByText(/丙/)).toBeTruthy()
  expect(within(card).getByText("已過期，還沒做")).toBeTruthy()
  expect(within(card).getByText(/乙/)).toBeTruthy()
})

test("新增練習量作業送出的內容", async () => {
  wrap(<AssignmentForm classId="c1" onDone={() => {}} />)
  fireEvent.change(screen.getByLabelText("種類"), {
    target: { value: "practice" },
  })
  fireEvent.change(screen.getByLabelText("滑卡（張）"), {
    target: { value: "10" },
  })
  fireEvent.change(screen.getByLabelText("訊息判讀（題）"), {
    target: { value: "20" },
  })
  fireEvent.change(screen.getByLabelText("最後一天"), {
    target: { value: "2026-11-02" },
  })
  fireEvent.click(screen.getByRole("button", { name: "新增作業" }))
  await waitFor(() => expect(classApi.createAssignment).toHaveBeenCalled())
  const [classId, body] = (
    classApi.createAssignment as unknown as { mock: { calls: unknown[][] } }
  ).mock.calls[0]
  expect(classId).toBe("c1")
  expect(body).toEqual({
    kind: "practice",
    title: null,
    params: { swipe: 10, quiz: 20, scenario: 0, fraud_type: null },
    due_at: "2026-11-02T23:59:59+08:00",
  })
})

test("新增要過關的專項檢測", async () => {
  wrap(<AssignmentForm classId="c1" onDone={() => {}} />)
  fireEvent.change(screen.getByLabelText("種類"), {
    target: { value: "specialized" },
  })
  fireEvent.change(screen.getByLabelText("類型"), {
    target: { value: "romance" },
  })
  fireEvent.click(screen.getByLabelText("要過關（70 分）"))
  fireEvent.change(screen.getByLabelText("最後一天"), {
    target: { value: "2026-11-02" },
  })
  fireEvent.click(screen.getByRole("button", { name: "新增作業" }))
  await waitFor(() => expect(classApi.createAssignment).toHaveBeenCalled())
  const body = (
    classApi.createAssignment as unknown as { mock: { calls: unknown[][] } }
  ).mock.calls[0][1]
  expect(body).toMatchObject({
    kind: "specialized",
    params: { fraud_type: "romance", require_pass: true },
  })
})

test("移出學生要再按一次確定", async () => {
  wrap(<RosterTable classId="c1" members={members} onOpen={() => {}} />)
  fireEvent.click(screen.getAllByRole("button", { name: "移出" })[0])
  expect(classApi.removeMember).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole("button", { name: "確定移出王小明" }))
  await waitFor(() =>
    expect(classApi.removeMember).toHaveBeenCalledWith("c1", "u1"),
  )
})
