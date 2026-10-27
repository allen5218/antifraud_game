import { afterEach, beforeEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router"
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react"
import type { MyClassPublic } from "@/client"
import { ApiError } from "@/client/core/ApiError"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { Classwork } from "./Classwork"
import { classApi } from "./classroomApi"

const response = <T,>(value: T) =>
  new CancelablePromise<T>((resolve) => resolve(value))

let mine: MyClassPublic[] = []

function assignment(id: string, kind: string, status: string, extra = {}) {
  return {
    id,
    title: `作業${id}`,
    kind,
    params: {},
    due_at: "2026-11-02T15:59:59Z",
    status,
    progress_text: status === "done" ? "完成" : "還沒做",
    completed_at: null,
    ...extra,
  }
}

beforeEach(() => {
  mine = [
    {
      id: "c1",
      name: "三年二班",
      teacher_name: "林老師",
      student_number: null,
      student_name: null,
      assignments: [],
    },
    {
      id: "c2",
      name: "公民課",
      teacher_name: "王老師",
      student_number: "S1",
      student_name: "小明",
      assignments: [
        assignment("1", "comprehensive", "todo"),
        assignment("2", "pretest", "done"),
        assignment("3", "practice", "overdue", {
          params: { swipe: 0, quiz: 20, scenario: 0, fraud_type: null },
          progress_text: "訊息判讀 3／20",
        }),
        assignment("4", "specialized", "late"),
      ],
    },
  ]
  spyOn(classApi, "mine").mockImplementation(() => response(mine))
  spyOn(classApi, "claim").mockImplementation(() => response(mine[0]))
  spyOn(classApi, "join").mockImplementation(
    () =>
      new CancelablePromise((_, reject) =>
        reject(
          new ApiError(
            { method: "POST", url: "/classes/join" },
            {
              url: "/classes/join",
              ok: false,
              status: 404,
              statusText: "x",
              body: { detail: { code: "invalid_invite" } },
            },
            "x",
          ),
        ),
      ),
  )
})

afterEach(() => {
  cleanup()
  mock.restore()
})

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const router = createRouter({
    routeTree: createRootRoute({
      component: () => (
        <QueryClientProvider client={qc}>
          <Classwork />
        </QueryClientProvider>
      ),
    }),
    history: createMemoryHistory({ initialEntries: ["/classwork"] }),
  })
  render(<RouterProvider router={router} />)
}

test("還沒填學號名字的班只看到認領表單", async () => {
  renderPage()
  const section = await screen.findByTestId("class-c1")
  expect(within(section).getByText(/先填學號和名字/)).toBeTruthy()
  fireEvent.change(within(section).getByLabelText("學號"), {
    target: { value: "A01" },
  })
  fireEvent.change(within(section).getByLabelText("名字"), {
    target: { value: "王小明" },
  })
  fireEvent.click(within(section).getByRole("button", { name: "送出" }))
  await waitFor(() =>
    expect(classApi.claim).toHaveBeenCalledWith("c1", {
      student_number: "A01",
      student_name: "王小明",
    }),
  )
})

test("作業的四種狀態與去做的連結", async () => {
  renderPage()
  const section = await screen.findByTestId("class-c2")
  expect(within(section).getByText("還沒做")).toBeTruthy()
  expect(within(section).getByText("完成")).toBeTruthy()
  expect(within(section).getByText(/已過期，還沒做/)).toBeTruthy()
  expect(within(section).getByText("遲交完成")).toBeTruthy()
  expect(within(section).getByText(/訊息判讀 3／20/)).toBeTruthy()
  const links = within(section).getAllByRole("link", { name: "去做" })
  expect(links.map((l) => l.getAttribute("href"))).toEqual([
    "/exam",
    "/quick/quiz",
  ])
})

test("代碼找不到時的訊息", async () => {
  renderPage()
  fireEvent.change(await screen.findByLabelText("班級代碼"), {
    target: { value: "zzzzzz" },
  })
  fireEvent.click(screen.getByRole("button", { name: "加入班級" }))
  expect(
    await screen.findByText("找不到這個班級，或老師已經停止加入。"),
  ).toBeTruthy()
  expect(classApi.join).toHaveBeenCalledWith({ code: "ZZZZZZ" })
})
