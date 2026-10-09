import { afterEach, describe, expect, it, mock } from "bun:test"
import { cleanup, screen } from "@testing-library/react"
import type { PracticeProfilePublic } from "@/client"
import { renderWithRouter } from "@/test/renderWithRouter"

let profile: PracticeProfilePublic | undefined
let profileError = false
let streakDays = 0

mock.module("@/hooks/usePractice", () => ({
  usePracticeProfile: () => ({
    data: profile,
    isError: profileError,
    isPending: !profile && !profileError,
    refetch: () => undefined,
  }),
}))
mock.module("@/hooks/useEconomy", () => ({
  useEconomyMe: () => ({ data: { streak_days: streakDays } }),
}))

import { NextStepHero } from "./NextStepHero"

afterEach(() => {
  cleanup()
  profile = undefined
  profileError = false
  streakDays = 0
})

const EVEN = {
  investment: 0.2,
  "fake-sale": 0.2,
  shopping: 0.2,
  romance: 0.2,
  atm: 0.2,
}

function gate(met: boolean) {
  return {
    fraud_type: "shopping",
    met,
    swipe: { done: met ? 6 : 4, need: 6 },
    quiz: { done: met ? 5 : 0, need: 5 },
    scenario: { done: met ? 1 : 0, need: 1 },
    recent: { correct: met ? 7 : 1, need: 7, total: met ? 10 : 4 },
  }
}

const href = (name: string) =>
  screen.getByRole("link", { name }).getAttribute("href")

describe("<NextStepHero />", () => {
  it("還沒有紀錄時，大卡的下一步是做前測", async () => {
    profile = {
      focus_type: null,
      focus_label: null,
      note: "還沒有作答紀錄。先做前測，系統會找出你最需要加強的類型。",
      weights: EVEN,
      source: "none",
      answers_seen: 0,
    }
    await renderWithRouter(<NextStepHero />)
    expect(screen.getByText("先做前測")).toBeTruthy()
    expect(href("做前測")).toBe("/pretest")
  })

  it("有練習重點時寫出加強哪一類，只留一個主按鈕", async () => {
    profile = {
      focus_type: "romance",
      focus_label: "假交友",
      note: "最近在「假交友」答錯 6 題（共 6 題），接下來會多練這一類。",
      weights: { ...EVEN, romance: 0.5 },
      source: "gemini",
      answers_seen: 26,
    }
    await renderWithRouter(<NextStepHero />)
    expect(screen.getByText("本輪加強：假交友")).toBeTruthy()
    expect(screen.getByText(/答錯 6 題/)).toBeTruthy()
    expect(href("開始練習")).toBe("/quick/swipe")
    // 三種訓練的入口就在大卡正下方，大卡不再重複
    expect(screen.queryByRole("link", { name: "訊息判讀" })).toBeNull()
    expect(screen.queryByRole("link", { name: "情境對抗" })).toBeNull()
    // 五類比例長條留在「我」頁，首頁大卡不畫
    expect(screen.queryByLabelText("各類出題比例")).toBeNull()
  })

  it("檢測沒過時，大卡換成補考還差多少", async () => {
    profile = {
      focus_type: "shopping",
      focus_label: "購物詐騙",
      note: "檢測沒過，先加強購物詐騙。",
      weights: { ...EVEN, shopping: 0.5 },
      source: "rule",
      answers_seen: 4,
      retake: { fraud_type: "shopping", gate: gate(false) },
    } as PracticeProfilePublic
    await renderWithRouter(<NextStepHero />)
    expect(screen.getByText("檢測沒過：先加強購物詐騙")).toBeTruthy()
    expect(screen.getByText(/還差滑卡 2 張、訊息判讀 5 題/)).toBeTruthy()
    expect(href("練滑卡")).toBe("/quick/swipe")
    expect(href("查看重考資格")).toBe("/exam")
  })

  it("補考練夠了就提示可以再檢測", async () => {
    profile = {
      focus_type: "shopping",
      focus_label: "購物詐騙",
      note: "購物詐騙已經練夠了，可以再檢測一次。",
      weights: { ...EVEN, shopping: 0.5 },
      source: "rule",
      answers_seen: 20,
      retake: { fraud_type: "shopping", gate: gate(true) },
    } as PracticeProfilePublic
    await renderWithRouter(<NextStepHero />)
    expect(screen.getByText("可以再檢測了")).toBeTruthy()
    expect(href("去檢測")).toBe("/exam")
    expect(screen.queryByRole("link", { name: "練滑卡" })).toBeNull()
  })

  it("有連續天數時顯示在大卡上", async () => {
    streakDays = 3
    profile = {
      focus_type: null,
      focus_label: null,
      note: "目前各類答得差不多，接下來每一類平均練習。",
      weights: EVEN,
      source: "rule",
      answers_seen: 30,
    }
    await renderWithRouter(<NextStepHero />)
    expect(screen.getByText("五類平均練習")).toBeTruthy()
    expect(screen.getByText(/連續 3 天/)).toBeTruthy()
  })

  it("練習重點讀不到時仍給一個能玩的入口", async () => {
    profileError = true
    await renderWithRouter(<NextStepHero />)
    expect(href("開始練習")).toBe("/quick/swipe")
  })
})
