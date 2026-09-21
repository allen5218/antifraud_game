import { afterEach, describe, expect, it, mock } from "bun:test"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"

const mockRefetch = mock(() => {})
let mockJourneyState: any = {
  isPending: false,
  isError: false,
  data: null,
  refetch: mockRefetch,
}

mock.module("@/hooks/useEconomy", () => ({
  useJourney: () => mockJourneyState,
  useEconomyMe: () => ({
    data: {
      cash: 10000,
      xp: 200,
      level: 1,
      streak_days: 1,
      pending_accrual: 0,
      bankruptcy_pending: false,
      completed_chapters: 0,
    },
  }),
  useClaimAccrual: () => ({ mutate: () => {}, isPending: false }),
}))

mock.module("@tanstack/react-router", () => ({
  Link: ({ children, to, ...props }: any) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
  createFileRoute: () => () => ({ component: () => null }),
}))

import { Home } from "@/routes/_shell/index"
import { LadderJourney } from "./LadderJourney"

const SAMPLE_JOURNEY = {
  completed_chapters: 0,
  unlocked_contact_ids: ["landlady"],
  chapter: {
    id: 1,
    title: "別離開平台",
    rung_title: "鄰里幫手",
    description: "房東阿姨管理著多處物業，近期常遇上有疑慮的通聯與租賃要求。",
    completed: false,
    is_current: true,
    is_locked: false,
    contact_id: "landlady",
    contact_name: "房東阿姨",
    contact_avatar: "LAND",
    contact_persona: "管理多處老舊公寓與出租套房的房東",
    steps: [
      { id: "quiz", label: "先看一眼", status: "current" },
      { id: "scenario", label: "接下委託", status: "upcoming" },
    ],
  },
  next_step: {
    kind: "quiz",
    title: "先看一眼：別離開平台",
    reason: "在幫房東阿姨處理事情前，先看幾則相關案例掌握判讀重點。",
    href: "/quick/quiz",
    estimated_time: "約 2 分鐘",
    contact_id: "landlady",
  },
  all_chapters: [
    {
      id: 1,
      title: "別離開平台",
      rung_title: "鄰里幫手",
      description: "房東阿姨管理著多處物業",
      completed: false,
      is_current: true,
      is_locked: false,
      contact_id: "landlady",
      contact_name: "房東阿姨",
      contact_avatar: "LAND",
      steps: [
        { id: "quiz", label: "先看一眼", status: "current" },
        { id: "scenario", label: "接下委託", status: "upcoming" },
      ],
    },
    {
      id: 2,
      title: "便宜得太剛好",
      rung_title: "網路同好",
      description: "梨梨熱愛手作次文化",
      completed: false,
      is_current: false,
      is_locked: true,
      contact_id: null,
      contact_name: "下一階解鎖：梨梨",
      contact_avatar: "🔒",
      steps: [
        { id: "quiz", label: "先看一眼", status: "upcoming" },
        { id: "scenario", label: "接下委託", status: "upcoming" },
      ],
    },
    {
      id: 3,
      title: "第 3 階",
      rung_title: "社群現場",
      description: "通關前置階級以解鎖本階內容。",
      completed: false,
      is_current: false,
      is_locked: true,
      contact_id: null,
      contact_name: "神秘聯絡人",
      contact_avatar: "🔒",
      steps: [],
    },
    {
      id: 4,
      title: "第 4 階",
      rung_title: "人脈考驗",
      description: "通關前置階級以解鎖本階內容。",
      completed: false,
      is_current: false,
      is_locked: true,
      contact_id: null,
      contact_name: "神秘聯絡人",
      contact_avatar: "🔒",
      steps: [],
    },
    {
      id: 5,
      title: "第 5 階",
      rung_title: "高額委託",
      description: "通關前置階級以解鎖本階內容。",
      completed: false,
      is_current: false,
      is_locked: true,
      contact_id: null,
      contact_name: "神秘聯絡人",
      contact_avatar: "🔒",
      steps: [],
    },
  ],
}

afterEach(() => {
  cleanup()
  mockRefetch.mockClear()
})

describe("<LadderJourney />", () => {
  it("renders loading indicator when pending", () => {
    mockJourneyState = {
      isPending: true,
      isError: false,
      data: null,
      refetch: mockRefetch,
    }
    render(<LadderJourney />)
    expect(screen.getByTestId("journey-loading")).toBeTruthy()
    expect(screen.getByText(/載入天梯主線中/)).toBeTruthy()
  })

  it("renders error state with retry button and calls refetch", () => {
    mockJourneyState = {
      isPending: false,
      isError: true,
      data: null,
      error: { status: 500 },
      refetch: mockRefetch,
    }
    render(<LadderJourney />)
    expect(screen.getByTestId("journey-error")).toBeTruthy()
    const retryBtn = screen.getByTestId("journey-retry-btn")
    fireEvent.click(retryBtn)
    expect(mockRefetch).toHaveBeenCalledTimes(1)
  })

  it("renders error state with login button when 401 auth error occurs", () => {
    mockJourneyState = {
      isPending: false,
      isError: true,
      data: null,
      error: { status: 401 },
      refetch: mockRefetch,
    }
    render(<LadderJourney />)
    expect(screen.getByTestId("journey-error")).toBeTruthy()
    expect(screen.getByTestId("journey-login-btn")).toBeTruthy()
    expect(screen.getByText(/登入憑證已失效/)).toBeTruthy()
  })

  it("renders error state with reload button when 404 version error occurs", () => {
    mockJourneyState = {
      isPending: false,
      isError: true,
      data: null,
      error: { status: 404 },
      refetch: mockRefetch,
    }
    render(<LadderJourney />)
    expect(screen.getByTestId("journey-error")).toBeTruthy()
    expect(screen.getByTestId("journey-reload-btn")).toBeTruthy()
    expect(screen.getByText(/系統版本不相符/)).toBeTruthy()
  })

  it("renders single primary CTA, current chapter steps without duplicate 前往 buttons", () => {
    mockJourneyState = {
      isPending: false,
      isError: false,
      data: SAMPLE_JOURNEY,
      refetch: mockRefetch,
    }
    render(<LadderJourney />)

    // 1. 唯一主要 CTA 驗證
    const mainCta = screen.getByTestId("journey-main-cta")
    expect(mainCta).toBeTruthy()
    expect(mainCta.getAttribute("href")).toBe("/quick/quiz")
    expect(screen.getByTestId("next-step-title").textContent).toContain(
      "先看一眼：別離開平台",
    )
    expect(screen.getByTestId("next-step-reason").textContent).toContain(
      "在幫房東阿姨處理事情前",
    )
    expect(screen.getByText("約 2 分鐘")).toBeTruthy()

    // 2. 這一章節點狀態展示（進行中、稍後），不可有多個前往按鈕
    const stepsContainer = screen.getByTestId("chapter-steps")
    expect(stepsContainer).toBeTruthy()
    expect(screen.getByTestId("step-quiz").textContent).toContain("進行中")
    expect(screen.getByTestId("step-scenario").textContent).toContain("稍後")

    // 驗證全畫面只有 1 個主要導覽連結指向動作，章節節點無多餘按鈕
    const allCtaButtons = screen.getAllByTestId("journey-main-cta")
    expect(allCtaButtons.length).toBe(1)
  })

  it("expands all 5 rungs showing unlocked, next unlock preview, and silhouettes", () => {
    mockJourneyState = {
      isPending: false,
      isError: false,
      data: SAMPLE_JOURNEY,
      refetch: mockRefetch,
    }
    render(<LadderJourney />)

    // 初始折疊
    expect(screen.queryByTestId("all-rungs-list")).toBeNull()

    // 點擊展開
    const toggleBtn = screen.getByTestId("toggle-all-rungs")
    fireEvent.click(toggleBtn)
    expect(screen.getByTestId("all-rungs-list")).toBeTruthy()

    // 驗證 5 階全數在列
    for (let i = 1; i <= 5; i++) {
      expect(screen.getByTestId(`rung-item-${i}`)).toBeTruthy()
    }

    // 驗證下一階解鎖預告與更高階神秘剪影
    expect(
      screen.getAllByText("下一階解鎖：梨梨").length,
    ).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText("神秘聯絡人").length).toBeGreaterThanOrEqual(1)
  })

  it("renders all completed state correctly when completed_chapters >= 5", () => {
    const allCompleteJourney = {
      ...SAMPLE_JOURNEY,
      completed_chapters: 5,
      next_step: {
        kind: "all_completed",
        title: "來一件新的生活事件",
        reason: "你已完成五階天梯考驗，隨時可以前往收件匣挑戰其他生活委託。",
        href: "/scenarios",
      },
    }
    mockJourneyState = {
      isPending: false,
      isError: false,
      data: allCompleteJourney,
      refetch: mockRefetch,
    }
    render(<LadderJourney />)

    expect(screen.getByTestId("next-step-title").textContent).toContain(
      "來一件新的生活事件",
    )
    expect(screen.getByText(/五階天梯全數通關/)).toBeTruthy()
  })

  it("renders Home component with LadderJourney and AccrualBanner, without PlayModeGrid", () => {
    mockJourneyState = {
      isPending: false,
      isError: false,
      data: SAMPLE_JOURNEY,
      refetch: mockRefetch,
    }
    render(<Home />)

    // LadderJourney is present with main CTA
    expect(screen.getByTestId("ladder-journey")).toBeTruthy()
    expect(screen.getByTestId("journey-main-cta")).toBeTruthy()

    // 驗證六個模式格不再渲染於首頁
    expect(screen.queryByText("題組訓練")).toBeNull()
    expect(screen.queryByText("滑卡辨識")).toBeNull()
    expect(screen.queryByText("防詐天賦")).toBeNull()
    expect(screen.queryByText("社區守護")).toBeNull()
    expect(screen.queryByText("真實案件")).toBeNull()
    expect(screen.queryByText("實驗沙盒")).toBeNull()
  })
})
