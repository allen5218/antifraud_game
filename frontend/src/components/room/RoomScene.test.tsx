import { afterEach, beforeEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
  RouterProvider,
} from "@tanstack/react-router"
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react"
import type { ExamStatus } from "@/client"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { EconomyService, ExamService } from "@/client/sdk.gen"
import type { HomeSummary } from "@/hooks/useHomeSummary"
import { homeApi } from "@/hooks/useHomeSummary"
import { BADGE_SLOTS, HOTSPOTS } from "./hotspots"
import { RoomScene } from "./RoomScene"

const response = <T,>(value: T) =>
  new CancelablePromise<T>((resolve) => resolve(value))

const idle: ExamStatus = {
  active_attempt_id: null,
  can_start: true,
  block_reason: null,
  gate: null,
  daily_used: 0,
  daily_limit: 3,
  badges: [],
}

function summary(overrides: Partial<HomeSummary> = {}): HomeSummary {
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
    focus_label: "投資詐騙",
    badges: [],
    ...overrides,
  }
}

let current = summary()
let pendingAccrual = 0
const qc = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
})

beforeEach(() => {
  localStorage.clear()
  current = summary()
  pendingAccrual = 0
  spyOn(homeApi, "summary").mockImplementation(() => response(current))
  spyOn(EconomyService, "readMe").mockImplementation(() =>
    response({
      cash: 12450,
      xp: 0,
      level: 1,
      streak_days: 3,
      pending_accrual: pendingAccrual,
      bankruptcy_pending: false,
    }),
  )
  spyOn(ExamService, "readStatus").mockImplementation(() => response(idle))
})

afterEach(() => {
  cleanup()
  qc.clear()
  localStorage.clear()
  mock.restore()
})

async function renderScene() {
  const rootRoute = createRootRoute({
    component: () => (
      <QueryClientProvider client={qc}>
        <Outlet />
      </QueryClientProvider>
    ),
  })
  const home = createRoute({
    getParentRoute: () => rootRoute,
    path: "/",
    component: RoomScene,
  })
  const scenarios = createRoute({
    getParentRoute: () => rootRoute,
    path: "/scenarios",
    component: () => <p>進了情境對抗</p>,
  })
  const pretest = createRoute({
    getParentRoute: () => rootRoute,
    path: "/pretest",
    component: () => <p>進了前測</p>,
  })
  const router = createRouter({
    routeTree: rootRoute.addChildren([home, scenarios, pretest]),
    history: createMemoryHistory({ initialEntries: ["/"] }),
  })
  await router.load()
  await act(async () => {
    render(<RouterProvider router={router} />)
  })
}

test("hotspots stay inside the image box", () => {
  for (const spot of [...Object.values(HOTSPOTS), ...BADGE_SLOTS]) {
    expect(spot.x).toBeGreaterThanOrEqual(0)
    expect(spot.x).toBeLessThanOrEqual(100)
    expect(spot.y).toBeGreaterThanOrEqual(0)
    expect(spot.y).toBeLessThanOrEqual(100)
  }
})

test("home-hero 存在，圖框照房間圖的實際比例", async () => {
  await renderScene()
  const hero = await screen.findByTestId("home-hero")
  expect(hero.className).toContain("max-w-md")
  // 圖框比例要和 stage-0～6 的實際像素（941×1672）一樣，熱區百分比才會對準物件
  const frame = screen.getByTestId("room-frame")
  expect(frame.style.aspectRatio.replace(/ /g, "")).toBe("941/1672")
  expect(frame.contains(screen.getByTestId("hotspot-phone"))).toBe(true)
})

test("點手機導到情境對抗", async () => {
  current = summary({ inbox_pending: 2 })
  await renderScene()
  fireEvent.click(await screen.findByTestId("hotspot-phone"))
  expect(await screen.findByText("進了情境對抗")).toBeTruthy()
})

test("選單打開列出五項、排行榜和我的徽章", async () => {
  await renderScene()
  await screen.findByText("本輪加強：投資詐騙。先去練練看，做完就有錢。")
  fireEvent.click(screen.getByTestId("room-menu"))
  for (const label of [
    "情境對抗",
    "滑卡訓練",
    "訊息判讀",
    "每日訓練",
    "檢測",
    "排行榜",
    "我的徽章",
  ]) {
    expect(screen.getByText(label)).toBeTruthy()
  }
})

test("新玩家看到開始按鈕", async () => {
  current = summary({
    pretest_done: false,
    focus_label: null,
    inbox_pending: 5,
  })
  await renderScene()
  const start = await screen.findByRole("link", { name: "開始" })
  expect(start.getAttribute("href")).toBe("/pretest")
  expect(screen.getByTestId("room-menu").textContent).toContain("5")
  expect(screen.getByTestId("bubble-tv").className).toContain("ring-warning")
  fireEvent.click(start)
  expect(await screen.findByText("進了前測")).toBeTruthy()
})

test("待領收益顯示可領，點了就領", async () => {
  pendingAccrual = 840
  let claimed = false
  spyOn(EconomyService, "claim").mockImplementation(() => {
    claimed = true
    return response({
      cash: 13290,
      xp: 0,
      level: 1,
      streak_days: 3,
      pending_accrual: 0,
      bankruptcy_pending: false,
    })
  })
  await renderScene()
  fireEvent.click(await screen.findByRole("button", { name: "可領 840" }))
  await waitFor(() => expect(claimed).toBe(true))
})

test("離開房間再回來會重讀首頁資料，不沿用舊的台詞", async () => {
  await renderScene()
  await screen.findByText("本輪加強：投資詐騙。先去練練看，做完就有錢。")

  // 在別頁練完、補考期結束之類的變化，回到房間就要看得到
  cleanup()
  localStorage.clear() // 對話框一天只自動開一次，清掉才看得到台詞
  current = summary({ focus_label: "假交友" })
  await renderScene()
  expect(
    await screen.findByText("本輪加強：假交友。先去練練看，做完就有錢。"),
  ).toBeTruthy()
})
