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
  within,
} from "@testing-library/react"
import type { ExamStatus } from "@/client"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { EconomyService, ExamService } from "@/client/sdk.gen"
import type { HomeSummary } from "@/hooks/useHomeSummary"
import { homeApi } from "@/hooks/useHomeSummary"
import { onboardingApi } from "./onboardingApi"
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

async function renderScene(entry = "/") {
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
    history: createMemoryHistory({ initialEntries: [entry] }),
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

test("每件可點的家具都有滑鼠提示，寫出是什麼與狀態", async () => {
  current = summary({ inbox_pending: 2 })
  await renderScene()
  const phone = await screen.findByTestId("hotspot-phone")
  expect(phone.querySelector("[role=tooltip]")?.textContent).toBe(
    "手機・情境對抗：還有 2 人沒聊",
  )
  const mascot = screen.getByTestId("hotspot-mascot")
  expect(mascot.querySelector("[role=tooltip]")?.textContent).toContain(
    "吉祥物",
  )
  // 名稱仍是原本的短名字，不會被提示文字蓋掉
  expect(phone.getAttribute("aria-label")).toBe("情境對抗")
})

test("家具旁常駐模式名稱，手機也看得到", async () => {
  await renderScene()
  const expected = {
    phone: "情境對抗",
    tv: "滑卡訓練",
    letters: "訊息判讀",
    calendar: "每日訓練",
    bookshelf: "檢測",
  }
  for (const [id, text] of Object.entries(expected)) {
    const label = await screen.findByTestId(`room-label-${id}`)
    expect(label.textContent).toBe(text)
    // 標籤是看的，不是另一個按鈕；也不是只在滑鼠移過去才出現的提示
    expect(label.getAttribute("aria-hidden")).toBe("true")
    expect(label.className).not.toContain("opacity-0")
  }
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
    // 房間家具旁也有同樣的模式名稱，只在選單裡找
    expect(
      within(screen.getByTestId("room-menu-list")).getByText(label),
    ).toBeTruthy()
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

test("還沒玩過的帳號一進房間先看導覽，跳過會記下來", async () => {
  current = summary({ tour_pending: true, pretest_done: false })
  const done = spyOn(onboardingApi, "tourDone").mockImplementation(() =>
    response(undefined),
  )
  await renderScene()
  expect(await screen.findByText("這是你的房間")).toBeTruthy()
  // 導覽開著時不同時跳出吉祥物對話框
  expect(screen.queryByText("收起")).toBeNull()
  fireEvent.click(screen.getByRole("button", { name: "跳過導覽" }))
  await waitFor(() => expect(done).toHaveBeenCalledTimes(1))
  await waitFor(() => expect(screen.queryByText("這是你的房間")).toBeNull())
})

test("導覽一步一步走到最後，新帳號接著去做入門前測", async () => {
  current = summary({ tour_pending: true, pretest_done: false })
  const done = spyOn(onboardingApi, "tourDone").mockImplementation(() =>
    response(undefined),
  )
  await renderScene()
  await screen.findByText("這是你的房間")
  expect(screen.getByText("第 1／10 步")).toBeTruthy()
  for (let i = 0; i < 9; i++) {
    fireEvent.click(screen.getByRole("button", { name: "下一步" }))
  }
  expect(screen.getByText("先做個小測驗")).toBeTruthy()
  fireEvent.click(screen.getByRole("link", { name: "開始" }))
  expect(await screen.findByText("進了前測")).toBeTruthy()
  expect(done).toHaveBeenCalledTimes(1)
})

test("選單可以重看導覽，看完只是關掉", async () => {
  const done = spyOn(onboardingApi, "tourDone").mockImplementation(() =>
    response(undefined),
  )
  await renderScene()
  await screen.findByText("本輪加強：投資詐騙。先去練練看，做完就有錢。")
  fireEvent.click(screen.getByTestId("room-menu"))
  fireEvent.click(
    within(screen.getByTestId("room-menu-list")).getByText("重看導覽"),
  )
  expect(await screen.findByText("這是你的房間")).toBeTruthy()
  for (let i = 0; i < 9; i++) {
    fireEvent.click(screen.getByRole("button", { name: "下一步" }))
  }
  fireEvent.click(screen.getByRole("button", { name: "知道了" }))
  await waitFor(() => expect(screen.queryByText("導覽結束")).toBeNull())
  expect(done).toHaveBeenCalledTimes(1)
})

test("有新手任務時房間顯示任務卡，導覽開著時先不顯示", async () => {
  current = summary({
    starter_tasks: {
      swipe: true,
      quiz: false,
      scenario: false,
      shop: false,
      reward_cash: 500,
      reward_xp: 100,
    },
  })
  await renderScene()
  expect(await screen.findByTestId("starter-tasks")).toBeTruthy()
  cleanup()
  // 首頁資料兩秒內不重抓，換一份資料要先清快取
  qc.clear()
  current = summary({
    tour_pending: true,
    starter_tasks: {
      swipe: false,
      quiz: false,
      scenario: false,
      shop: false,
      reward_cash: 500,
      reward_xp: 100,
    },
  })
  await renderScene()
  await screen.findByText("這是你的房間")
  expect(screen.queryByTestId("starter-tasks")).toBeNull()
})
