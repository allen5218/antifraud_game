import {
  afterEach,
  beforeEach,
  expect,
  mock,
  setSystemTime,
  spyOn,
  test,
} from "bun:test"
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
  setSystemTime()
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

test("房間鋪滿整個區塊，入口都在舞台上", async () => {
  await renderScene()
  const hero = await screen.findByTestId("home-hero")
  // 不再限制成手機寬度：平板也鋪滿，比例由舞台處理
  expect(hero.className).not.toContain("max-w-md")
  const stage = screen.getByTestId("room-stage")
  for (const id of ["phone", "tv", "letters", "calendar", "bookshelf"]) {
    expect(stage.contains(screen.getByTestId(`hotspot-${id}`))).toBe(true)
  }
  expect(stage.contains(screen.getByTestId("hotspot-mascot"))).toBe(true)
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
  // 物件上不放圖示泡泡（使用者 10-18：「泡泡都拿掉」），推薦去的物件呼吸光比較快
  for (const id of ["tv", "phone", "letters", "calendar", "bookshelf"]) {
    expect(screen.queryByTestId(`bubble-${id}`)).toBeNull()
  }
  expect(screen.getByTestId("glow-tv").getAttribute("data-strong")).toBe("true")
  fireEvent.click(start)
  expect(await screen.findByText("進了前測")).toBeTruthy()
})

test("試測帳號今天看過對話框，回房間仍打開並帶去檢測", async () => {
  current = summary({ trial: true, pretest_done: false, survey_pending: true })
  localStorage.setItem(
    "room-guide-seen",
    new Date().toLocaleDateString("sv-SE", { timeZone: "Asia/Taipei" }),
  )
  await renderScene()
  const start = await screen.findByRole("link", { name: "開始檢測" })
  expect(start.getAttribute("href")).toBe("/exam")
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
  setSystemTime(new Date(Date.now() + 5_000)) // 練一輪一定超過首頁資料的兩秒新鮮期
  await renderScene()
  expect(
    await screen.findByText("本輪加強：假交友。先去練練看，做完就有錢。"),
  ).toBeTruthy()
})

test("資料還沒回來時先用上次的房間與吉祥物，不閃破舊房間和柴犬", async () => {
  localStorage.setItem(
    "room-last-look",
    JSON.stringify({ stage: 3, mascot: "/assets/mascot/fox/base.webp" }),
  )
  spyOn(homeApi, "summary").mockImplementation(
    () => new CancelablePromise<HomeSummary>(() => {}),
  )
  await renderScene()
  expect(screen.getByTestId("room-bg").getAttribute("src")).toBe(
    "/assets/room/3/bg.webp",
  )
  expect(screen.getByTestId("layer-mascot").getAttribute("src")).toBe(
    "/assets/mascot/fox/base.webp",
  )
})

test("資料回來後記住這次的房間與吉祥物", async () => {
  current = summary({
    room_stage: 2,
    mascot_image_url: "/assets/mascot/cat/base.webp",
  })
  await renderScene()
  await waitFor(() =>
    expect(JSON.parse(localStorage.getItem("room-last-look") ?? "{}")).toEqual({
      stage: 2,
      mascot: "/assets/mascot/cat/base.webp",
    }),
  )
})

test("管理員在頁首看到試測管理，一般玩家沒有", async () => {
  await renderScene()
  await screen.findByTestId("room-me")
  await waitFor(() => expect(homeApi.summary).toHaveBeenCalled())
  expect(screen.queryByTestId("room-admin")).toBeNull()
  cleanup()
  qc.clear()
  current = summary({ admin_access: true })
  await renderScene()
  const admin = await screen.findByTestId("room-admin")
  expect(admin.getAttribute("href")).toBe("/admin/cohorts")
  expect(admin.textContent).toBe("試測管理")
})

test("核准的老師在頁首看到班級管理，申請中與一般玩家沒有", async () => {
  current = summary({ teacher_status: "pending" })
  await renderScene()
  await screen.findByTestId("room-me")
  await waitFor(() => expect(homeApi.summary).toHaveBeenCalled())
  expect(screen.queryByTestId("room-classes")).toBeNull()
  cleanup()
  qc.clear()
  current = summary({ teacher_status: "approved" })
  await renderScene()
  const classes = await screen.findByTestId("room-classes")
  expect(classes.getAttribute("href")).toBe("/classes")
  expect(classes.textContent).toBe("班級管理")
})
