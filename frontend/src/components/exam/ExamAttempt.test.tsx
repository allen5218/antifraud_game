import { afterEach, expect, mock, spyOn, test } from "bun:test"
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query"
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react"
import type { ReactNode } from "react"
import type { ExamState, ScenarioDetail } from "@/client"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { ExamService, ScenarioService } from "@/client/sdk.gen"
import { renderWithRouter } from "@/test/renderWithRouter"
import { ExamAttempt } from "./ExamAttempt"

const base: ExamState = {
  id: "a",
  mode: "specialized",
  status: "active",
  stage: "swipe",
  fraud_type: "romance",
  expires_at: "2099-01-01T00:00:00Z",
  stage_items: [{ id: "c", source_label: "通知", scenario: "請先看資料" }],
  progress: { stage_index: 0, stage_count: 3 },
  scenario: null,
  result: null,
}
const response = <T,>(value: T) =>
  new CancelablePromise<T>((resolve) => resolve(value))
const qc = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
})
afterEach(() => {
  cleanup()
  qc.clear()
  sessionStorage.clear()
  mock.restore()
})
async function mount(extra?: ReactNode) {
  await renderWithRouter(
    <QueryClientProvider client={qc}>
      {extra}
      <ExamAttempt attemptId="a" />
    </QueryClientProvider>,
  )
}

test("重新整理先讀伺服器關卡，提交失敗重送原 payload，成功才進下一關", async () => {
  spyOn(ExamService, "read").mockImplementation(() => response(base))
  const submit = spyOn(ExamService, "swipe")
    .mockImplementationOnce(
      () =>
        new CancelablePromise((_resolve, reject) =>
          reject(new Error("network")),
        ),
    )
    .mockImplementation(() =>
      response({
        ...base,
        stage: "message",
        progress: { stage_index: 1, stage_count: 3 },
        stage_items: [
          {
            item_id: "m",
            kind: "verdict",
            title: "下一關",
            narrative: "完整訊息",
          },
        ],
      }),
    )
  await mount()
  fireEvent.click(await screen.findByRole("button", { name: "詐騙" }))
  fireEvent.click(screen.getByRole("button", { name: "送出這一關" }))
  await screen.findByRole("alert")
  fireEvent.click(screen.getByRole("button", { name: "送出這一關" }))
  await screen.findByText("下一關")
  expect(submit.mock.calls).toEqual([
    [
      {
        attemptId: "a",
        requestBody: { answers: [{ card_id: "c", guess_is_scam: true }] },
      },
    ],
    [
      {
        attemptId: "a",
        requestBody: { answers: [{ card_id: "c", guess_is_scam: true }] },
      },
    ],
  ])
})

test("放棄確認把繼續作答放在主要按鈕，確定放棄是次要按鈕", async () => {
  spyOn(ExamService, "read").mockImplementation(() => response(base))
  await mount()
  fireEvent.click(await screen.findByRole("button", { name: "放棄檢測" }))
  const keep = screen.getByRole("button", { name: "繼續作答" })
  const drop = screen.getByRole("button", { name: "確定放棄" })
  expect(screen.getByRole("dialog").textContent).toContain(
    "還沒交的關卡以零分計算",
  )
  expect(keep.className).toContain("bg-primary")
  expect(drop.className).not.toContain("bg-primary")
})

test("放棄需要確認，確認後顯示保存的結果", async () => {
  spyOn(ExamService, "read").mockImplementation(() => response(base))
  const abandon = spyOn(ExamService, "abandon").mockImplementation(() =>
    response({
      ...base,
      status: "abandoned",
      stage: "done",
      result: {
        total_score: 0,
        passed: false,
        mode: "specialized",
        fraud_type: "romance",
        pretest_by_type: null,
        weakness_score: 0,
        weakness_max: 100,
        missed_tactics: [],
        badges: [],
        reward: { cash: 0, xp: 0 },
      },
    }),
  )
  await mount()
  fireEvent.click(await screen.findByRole("button", { name: "放棄檢測" }))
  expect(abandon).not.toHaveBeenCalled()
  expect(screen.getByRole("dialog").textContent).toContain("放棄算一次沒過")
  fireEvent.click(screen.getByRole("button", { name: "確定放棄" }))
  await screen.findByText("這次沒有通過")
  expect(abandon).toHaveBeenCalledTimes(1)
})

test("到期重新讀伺服器結果，voided 不顯示零分沒過", async () => {
  spyOn(ExamService, "read")
    .mockImplementationOnce(() =>
      response({ ...base, expires_at: "2000-01-01T00:00:00Z" }),
    )
    .mockImplementation(() =>
      response({ ...base, status: "voided", stage: "done" }),
    )
  await mount()
  await waitFor(() => expect(screen.getByText("這次檢測不計次")).toBeTruthy())
  expect(screen.queryByText("這次沒有通過")).toBeNull()
})

const chat: ScenarioDetail = {
  id: "s",
  fraud_type: "romance",
  display_name: "聯絡人",
  avatar: "romance-1",
  status: "active",
  outcome: null,
  player_turns: 1,
  max_turns: 8,
  history: [{ role: "npc", messages: ["你好"], decision_point: null }],
}

test("倒數歸零仍可交卷，伺服器仍進行中時改約每十秒再讀", async () => {
  const delays: number[] = []
  const original = globalThis.setInterval
  spyOn(globalThis, "setInterval").mockImplementation(((
    handler: TimerHandler,
    timeout?: number,
    ...args: unknown[]
  ) => {
    if (typeof timeout === "number") delays.push(timeout)
    return original(handler, timeout, ...(args as []))
  }) as typeof setInterval)
  const expired = { ...base, expires_at: "2000-01-01T00:00:00Z" }
  let current: ExamState = expired
  const read = spyOn(ExamService, "read").mockImplementation(() =>
    response(current),
  )
  const submit = spyOn(ExamService, "swipe").mockImplementation(() => {
    current = {
      ...expired,
      stage: "message",
      progress: { stage_index: 1, stage_count: 3 },
      stage_items: [
        {
          item_id: "m",
          kind: "verdict",
          title: "下一關",
          narrative: "完整訊息",
        },
      ],
    }
    return response(current)
  })
  await mount()
  expect(await screen.findByText("正在確認時間")).toBeTruthy()
  expect(screen.queryByText("時間到了，正在確認檢測結果。")).toBeNull()
  expect(screen.getByText(/剩餘時間 0：00/)).toBeTruthy()
  fireEvent.click(screen.getByRole("button", { name: "詐騙" }))
  fireEvent.click(screen.getByRole("button", { name: "送出這一關" }))
  await screen.findByText("下一關")
  expect(submit).toHaveBeenCalledTimes(1)
  await waitFor(() => expect(delays).toContain(10_000))
  expect(delays).not.toContain(30_000)
  expect(read).toHaveBeenCalled()
})

test("重新讀取檢測失敗時保留錯誤提示，且不往外拋", async () => {
  const reasons: unknown[] = []
  const onUnhandled = (reason: unknown) => {
    reasons.push(reason)
  }
  process.on("unhandledRejection", onUnhandled)
  try {
    spyOn(ExamService, "read")
      .mockImplementationOnce(() => response(base))
      .mockImplementation(
        () =>
          new CancelablePromise((_resolve, reject) =>
            reject(new Error("offline")),
          ),
      )
    spyOn(ExamService, "swipe").mockImplementation(
      () =>
        new CancelablePromise((_resolve, reject) =>
          reject(new Error("network")),
        ),
    )
    await mount()
    fireEvent.click(await screen.findByRole("button", { name: "詐騙" }))
    fireEvent.click(screen.getByRole("button", { name: "送出這一關" }))
    await screen.findByText("目前無法完成，請再試一次。")
    fireEvent.click(screen.getByRole("button", { name: "重新讀取檢測" }))
    await new Promise((resolve) => setTimeout(resolve, 40))
    expect(screen.getByRole("alert").textContent).toContain(
      "目前無法完成，請再試一次。",
    )
    expect(reasons).toEqual([])
  } finally {
    process.off("unhandledRejection", onUnhandled)
  }
})

test("結算後立刻重抓畫面上的金額與等級", async () => {
  spyOn(ExamService, "read").mockImplementation(() => response(base))
  let rewarded = false
  function EconomyOnScreen() {
    const economy = useQuery({
      queryKey: ["economy", "me"],
      queryFn: () =>
        response(rewarded ? { cash: 3100, level: 2 } : { cash: 100, level: 1 }),
      staleTime: 30_000,
    })
    if (!economy.data) return null
    return (
      <p>
        <span data-testid="hdr-cash">{economy.data.cash.toLocaleString()}</span>
        <span>Lv.{economy.data.level}</span>
      </p>
    )
  }
  spyOn(ExamService, "swipe").mockImplementation(() => {
    rewarded = true
    return response({
      ...base,
      status: "completed",
      stage: "done",
      stage_items: [],
      progress: { stage_index: 3, stage_count: 3 },
      result: {
        total_score: 90,
        passed: true,
        mode: "specialized",
        fraud_type: "romance",
        pretest_by_type: null,
        weakness_score: 90,
        weakness_max: 100,
        missed_tactics: [],
        badges: [],
        reward: { cash: 3000, xp: 150 },
      },
    })
  })
  await mount(<EconomyOnScreen />)
  await waitFor(() =>
    expect(screen.getByTestId("hdr-cash").textContent).toContain("100"),
  )
  fireEvent.click(screen.getByRole("button", { name: "詐騙" }))
  fireEvent.click(screen.getByRole("button", { name: "送出這一關" }))
  await screen.findByText("檢測通過")
  await waitFor(() =>
    expect(screen.getByTestId("hdr-cash").textContent).toContain("3,100"),
  )
  expect(screen.getByText("Lv.2")).toBeTruthy()
})

test("判斷已記錄時改讀伺服器狀態並進下一場", async () => {
  const scenarioState: ExamState = {
    ...base,
    stage: "scenario",
    stage_items: [],
    scenario: {
      session_id: "s",
      index: 1,
      count: 2,
      max_turns: 8,
      player_turns: 1,
    },
  }
  const next: ExamState = {
    ...scenarioState,
    scenario: {
      session_id: null,
      index: 2,
      count: 2,
      max_turns: 8,
      player_turns: 0,
    },
  }
  let judged = false
  spyOn(ExamService, "read").mockImplementation(() =>
    response(judged ? next : scenarioState),
  )
  spyOn(ScenarioService, "readScenario").mockImplementation(() =>
    response(chat),
  )
  spyOn(ExamService, "scenarioJudge").mockImplementation(
    () =>
      new CancelablePromise((_resolve, reject) => {
        judged = true
        reject({
          body: { detail: { code: "exam_scenario_already_answered" } },
        })
      }),
  )
  await mount()
  fireEvent.click(await screen.findByRole("button", { name: "下判斷" }))
  fireEvent.click(
    screen.getByRole("button", { name: "這是詐騙（檢舉並封鎖）" }),
  )
  await screen.findByRole("button", { name: "開始這場對話" })
  expect(screen.getByText("情境對抗第 2 場，共 2 場")).toBeTruthy()
  expect(screen.queryByText("目前無法完成，請再試一次。")).toBeNull()
})
