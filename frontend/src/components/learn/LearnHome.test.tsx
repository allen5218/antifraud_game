import { afterEach, beforeEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, screen, within } from "@testing-library/react"
import type { CardSummary } from "@/client"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { CardsService } from "@/client/sdk.gen"
import type { HomeSummary } from "@/hooks/useHomeSummary"
import { homeApi } from "@/hooks/useHomeSummary"
import { renderWithRouter } from "@/test/renderWithRouter"
import { LearnHome } from "./LearnHome"

const response = <T,>(value: T) =>
  new CancelablePromise<T>((resolve) => resolve(value))

function home(overrides: Partial<HomeSummary> = {}): HomeSummary {
  return {
    room_stage: 0,
    mascot_image_url: "/assets/mascot/shiba/base.webp",
    pretest_done: true,
    inbox_pending: 0,
    daily_unlocked: false,
    daily_done: false,
    exam_active_attempt_id: null,
    exam_can_start: false,
    retake: null,
    focus_type: null,
    focus_label: null,
    badges: [],
    ...overrides,
  }
}

const SUMMARY: CardSummary = {
  elder_mode: false,
  daily_goal: 20,
  today_done: 12,
  streak_days: 5,
  learned: 38,
  total: 200,
  due_now: 3,
  topics: [
    { fraud_type: "investment", learned: 10, total: 40 },
    { fraud_type: "general", learned: 2, total: 12 },
  ],
}

let homeData = home()

async function renderHome() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  await renderWithRouter(
    <QueryClientProvider client={qc}>
      <LearnHome />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  homeData = home()
  spyOn(homeApi, "summary").mockImplementation(() => response(homeData))
  spyOn(CardsService, "cardSummary").mockImplementation(() => response(SUMMARY))
})
afterEach(() => {
  cleanup()
  mock.restore()
})

test("今天的目標、連續天數、學會幾招、繼續練習", async () => {
  await renderHome()
  expect(await screen.findByText("連續練習")).toBeTruthy()
  expect(screen.getByText("5 天")).toBeTruthy()
  expect(screen.getByText("38／200 招")).toBeTruthy()
  expect(screen.getByRole("img", { name: "完成 60%" })).toBeTruthy()
  const go = screen.getByTestId("continue-practice")
  expect(go.getAttribute("href")).toBe("/learn")
  expect(screen.getByText("有 3 張該複習了")).toBeTruthy()
})

test("各類只練那一類，共通類叫防詐常識", async () => {
  await renderHome()
  const inv = await screen.findByTestId("topic-investment")
  expect(inv.getAttribute("href")).toBe("/learn?topic=investment")
  expect(within(inv).getByText("投資詐騙")).toBeTruthy()
  expect(within(inv).getByText("學會 10／40 招")).toBeTruthy()
  expect(
    within(screen.getByTestId("topic-general")).getByText("防詐常識"),
  ).toBeTruthy()
})

test("有要先做的事才出現提醒，連結和房間吉祥物一樣", async () => {
  homeData = home({ pretest_done: false })
  await renderHome()
  const reminder = await screen.findByTestId("home-reminder")
  expect(
    within(reminder).getByRole("link", { name: "開始" }).getAttribute("href"),
  ).toBe("/pretest")
})

test("只是一般鼓勵時不顯示提醒", async () => {
  homeData = home({ focus_label: "投資詐騙" })
  await renderHome()
  await screen.findByText("連續練習")
  expect(screen.queryByTestId("home-reminder")).toBeNull()
})
