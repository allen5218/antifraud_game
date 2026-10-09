import { afterEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react"
import type { ExamState, ScenarioDetail } from "@/client"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { ExamService, ScenarioService } from "@/client/sdk.gen"
import { ExamScenario } from "./ExamScenario"

const response = <T,>(value: T) =>
  new CancelablePromise<T>((resolve) => resolve(value))
const state: ExamState = {
  id: "a",
  mode: "specialized",
  status: "active",
  stage: "scenario",
  fraud_type: "romance",
  expires_at: "2099-01-01T00:00:00Z",
  stage_items: [],
  progress: { stage_index: 2, stage_count: 3 },
  scenario: {
    session_id: "s",
    index: 1,
    count: 2,
    max_turns: 8,
    player_turns: 0,
  },
  result: null,
}
const detail: ScenarioDetail = {
  id: "s",
  fraud_type: "romance",
  display_name: "聯絡人",
  avatar: "romance-1",
  status: "active",
  outcome: null,
  player_turns: 0,
  max_turns: 8,
  history: [{ role: "npc", messages: ["你好"], decision_point: null }],
}
const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
afterEach(() => {
  cleanup()
  qc.clear()
  mock.restore()
})
function mount(
  s = state,
  mutate = async (operation: () => PromiseLike<ExamState>) => {
    await operation()
  },
  refresh: () => Promise<unknown> = async () => {},
) {
  render(
    <QueryClientProvider client={qc}>
      <ExamScenario state={s} busy={false} mutate={mutate} refresh={refresh} />
    </QueryClientProvider>,
  )
}

test("讀原本場次對話，用 API 回合數，502 保留訊息且不扣回合", async () => {
  spyOn(ScenarioService, "readScenario").mockImplementation(() =>
    response(detail),
  )
  const send = spyOn(ScenarioService, "sendMessage")
    .mockImplementationOnce(
      () =>
        new CancelablePromise((_resolve, reject) =>
          reject({ body: { detail: { code: "agent_failed" } } }),
        ),
    )
    .mockImplementation(() =>
      response({ messages: ["好"], decision_point: null, turns_left: 7 }),
    )
  mount()
  await screen.findByText("你好")
  const input = screen.getByRole("textbox", { name: "對話訊息" })
  fireEvent.change(input, { target: { value: "請說明" } })
  fireEvent.click(screen.getByRole("button", { name: "送出訊息" }))
  await screen.findByRole("alert")
  await waitFor(() =>
    expect(
      (screen.getByRole("button", { name: "送出訊息" }) as HTMLButtonElement)
        .disabled,
    ).toBe(false),
  )
  expect((input as HTMLInputElement).value).toBe("請說明")
  expect(screen.getByText(/還能回覆 8 次/)).toBeTruthy()
  fireEvent.click(screen.getByRole("button", { name: "送出訊息" }))
  await waitFor(() => expect(send).toHaveBeenCalledTimes(2))
  expect(send.mock.calls[0]).toEqual(send.mock.calls[1])
})

test("回合用完仍可判斷，走檢測 judge 且不揭曉身分，重送鎖住原判斷", async () => {
  spyOn(ScenarioService, "readScenario").mockImplementation(() =>
    response({ ...detail, player_turns: 8 }),
  )
  const judge = spyOn(ExamService, "scenarioJudge").mockImplementation(() =>
    response(state),
  )
  mount()
  await screen.findByText("你好")
  expect(
    (screen.getByRole("textbox", { name: "對話訊息" }) as HTMLInputElement)
      .disabled,
  ).toBe(true)
  fireEvent.click(screen.getByRole("button", { name: "下判斷" }))
  expect(screen.getByRole("dialog").textContent).not.toContain("付出代價")
  fireEvent.click(
    screen.getByRole("button", { name: "這是詐騙（檢舉並封鎖）" }),
  )
  await waitFor(() => expect(judge).toHaveBeenCalledTimes(1))
  fireEvent.click(screen.getByRole("button", { name: "重送原判斷" }))
  await waitFor(() => expect(judge).toHaveBeenCalledTimes(2))
  expect(judge.mock.calls[0][0]).toEqual({
    attemptId: "a",
    requestBody: { session_id: "s", action: "report" },
  })
  expect(judge.mock.calls[0]).toEqual(judge.mock.calls[1])
  expect(screen.queryByText(/對方是|判斷正確|判斷錯誤/)).toBeNull()
})

test("開始情境沿用檢測 scenario start", async () => {
  const start = spyOn(ExamService, "scenarioStart").mockImplementation(() =>
    response(state),
  )
  mount({ ...state, scenario: { ...state.scenario!, session_id: null } })
  fireEvent.click(screen.getByRole("button", { name: "開始這場對話" }))
  await waitFor(() => expect(start).toHaveBeenCalledTimes(1))
  expect(start.mock.calls[0][0]).toEqual({ attemptId: "a" })
})

test("回應遺失且對話恢復失敗時，鎖住行動卡與判斷直到重讀成功", async () => {
  const chat = {
    ...detail,
    history: [{ role: "npc", messages: ["你好"], decision_point: "請付款" }],
  }
  spyOn(ScenarioService, "readScenario")
    .mockImplementationOnce(() => response(chat))
    .mockImplementationOnce(
      () =>
        new CancelablePromise((_resolve, reject) =>
          reject(new Error("network")),
        ),
    )
    .mockImplementation(() => response({ ...chat, player_turns: 1 }))
  const send = spyOn(ScenarioService, "sendMessage").mockImplementation(
    () =>
      new CancelablePromise((_resolve, reject) =>
        reject(new Error("lost-response")),
      ),
  )
  mount()
  fireEvent.click(await screen.findByRole("button", { name: "拒絕" }))
  await screen.findByRole("button", { name: "重新讀取對話" })
  expect(
    (screen.getByRole("button", { name: "拒絕" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true)
  expect(
    (screen.getByRole("button", { name: "照做" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true)
  expect(
    (screen.getByRole("button", { name: "下判斷" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true)
  fireEvent.click(screen.getByRole("button", { name: "拒絕" }))
  expect(send).toHaveBeenCalledTimes(1)
  fireEvent.click(screen.getByRole("button", { name: "重新讀取對話" }))
  await waitFor(() =>
    expect(
      (screen.getByRole("button", { name: "下判斷" }) as HTMLButtonElement)
        .disabled,
    ).toBe(false),
  )
  expect(
    (screen.getByRole("button", { name: "拒絕" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true)
  expect(screen.getByText(/還能回覆 7 次/)).toBeTruthy()
  expect(send).toHaveBeenCalledTimes(1)
})

test("成功讀到較多回合就清掉草稿，手動重讀與拒絕也一樣", async () => {
  let phase: "initial" | "fail" | "saved" = "initial"
  let chat = detail
  spyOn(ScenarioService, "readScenario").mockImplementation(() => {
    if (phase === "fail")
      return new CancelablePromise((_resolve, reject) =>
        reject(new Error("network")),
      )
    if (phase === "saved") return response({ ...chat, player_turns: 1 })
    return response(chat)
  })
  const send = spyOn(ScenarioService, "sendMessage").mockImplementation(
    () =>
      new CancelablePromise((_resolve, reject) => {
        phase = "fail"
        reject(new Error("lost"))
      }),
  )
  mount()
  const input = await screen.findByRole("textbox", { name: "對話訊息" })
  fireEvent.change(input, { target: { value: "請說明" } })
  fireEvent.click(screen.getByRole("button", { name: "送出訊息" }))
  await screen.findByRole("button", { name: "重新讀取對話" })
  expect((input as HTMLInputElement).value).toBe("請說明")
  phase = "saved"
  fireEvent.click(screen.getByRole("button", { name: "重新讀取對話" }))
  await waitFor(() => expect((input as HTMLInputElement).value).toBe(""))
  expect(screen.queryByRole("alert")).toBeNull()
  expect(send).toHaveBeenCalledTimes(1)

  cleanup()
  qc.clear()
  phase = "initial"
  chat = {
    ...detail,
    history: [{ role: "npc", messages: ["你好"], decision_point: "請付款" }],
  }
  mount()
  fireEvent.click(await screen.findByRole("button", { name: "拒絕" }))
  await screen.findByRole("button", { name: "重新讀取對話" })
  phase = "saved"
  fireEvent.click(screen.getByRole("button", { name: "重新讀取對話" }))
  await screen.findByText(/還能回覆 7 次/)
  const sent = send.mock.calls.length
  fireEvent.click(screen.getByRole("button", { name: "拒絕" }))
  expect(send.mock.calls.length).toBe(sent)
})

test("判斷說明會看還有沒有下一場", async () => {
  spyOn(ScenarioService, "readScenario").mockImplementation(() =>
    response(detail),
  )
  mount()
  fireEvent.click(await screen.findByRole("button", { name: "下判斷" }))
  expect(screen.getByRole("dialog").textContent).toContain(
    "判斷後這場對話就結束，接著進下一場。",
  )
  cleanup()
  qc.clear()
  mount({
    ...state,
    mode: "comprehensive",
    scenario: { ...state.scenario!, index: 1, count: 1 },
  })
  fireEvent.click(await screen.findByRole("button", { name: "下判斷" }))
  expect(screen.getByRole("dialog").textContent).toContain(
    "判斷後這場對話就結束，接著完成檢測。",
  )
})

test("重讀失敗時留在錯誤提示，不往外拋", async () => {
  const reasons: unknown[] = []
  const onUnhandled = (reason: unknown) => {
    reasons.push(reason)
  }
  process.on("unhandledRejection", onUnhandled)
  try {
    spyOn(ScenarioService, "readScenario").mockImplementation(() =>
      response(detail),
    )
    spyOn(ScenarioService, "sendMessage").mockImplementation(
      () =>
        new CancelablePromise((_resolve, reject) =>
          reject({ body: { detail: { code: "exam_ended" } } }),
        ),
    )
    mount(
      state,
      async (operation) => {
        await operation()
      },
      () => Promise.reject(new Error("refresh-failed")),
    )
    const input = await screen.findByRole("textbox", { name: "對話訊息" })
    fireEvent.change(input, { target: { value: "請說明" } })
    fireEvent.click(screen.getByRole("button", { name: "送出訊息" }))
    await screen.findByText("檢測已結束，請重新讀取結果。")
    await new Promise((resolve) => setTimeout(resolve, 40))
    expect(reasons).toEqual([])
  } finally {
    process.off("unhandledRejection", onUnhandled)
  }
})
