import { afterEach, describe, expect, it, mock } from "bun:test"
import { cleanup, screen } from "@testing-library/react"
import type { PracticeProfilePublic } from "@/client"
import { renderWithRouter } from "@/test/renderWithRouter"

let profile: PracticeProfilePublic | undefined

mock.module("@/hooks/usePractice", () => ({
  usePracticeProfile: () => ({ data: profile }),
}))

import { PracticeFocusBadge, PracticeFocusCard } from "./PracticeFocus"

afterEach(cleanup)

const EVEN = {
  investment: 0.2,
  "fake-sale": 0.2,
  shopping: 0.2,
  romance: 0.2,
  atm: 0.2,
}

describe("<PracticeFocusCard />", () => {
  it("還沒有紀錄時引導去做前測,不畫比例", async () => {
    profile = {
      focus_type: null,
      focus_label: null,
      note: "還沒有作答紀錄。先做前測，系統會找出你最需要加強的類型。",
      weights: EVEN,
      source: "none",
      answers_seen: 0,
    }
    await renderWithRouter(<PracticeFocusCard />)
    expect(screen.getByText("做前測")).toBeTruthy()
    expect(screen.queryByLabelText("各類出題比例")).toBeNull()
  })

  it("有重點時顯示是哪一類、說明與五類比例", async () => {
    profile = {
      focus_type: "romance",
      focus_label: "假交友",
      note: "最近在「假交友」答錯 6 題（共 6 題），接下來會多練這一類。",
      weights: {
        investment: 0.125,
        "fake-sale": 0.125,
        shopping: 0.125,
        romance: 0.5,
        atm: 0.125,
      },
      source: "gemini",
      answers_seen: 26,
    }
    await renderWithRouter(<PracticeFocusCard />)
    expect(screen.getByText("多練「假交友」")).toBeTruthy()
    expect(screen.getByText(/答錯 6 題/)).toBeTruthy()
    expect(screen.getByText("50%")).toBeTruthy()
    // 12.5% 不能四捨五入成 13%,否則五類加起來是 102%
    expect(screen.getAllByText("12.5%")).toHaveLength(4)
    // 五類都要列出來,名稱跟後端一致
    for (const label of [
      "投資詐騙",
      "假網拍",
      "購物詐騙",
      "假交友",
      "解除分期",
    ]) {
      expect(screen.getByText(label)).toBeTruthy()
    }
  })
})

describe("<PracticeFocusBadge />", () => {
  it("沒有重點時不顯示", async () => {
    profile = {
      focus_type: null,
      focus_label: null,
      note: "目前各類答得差不多，接下來每一類平均練習。",
      weights: EVEN,
      source: "rule",
      answers_seen: 20,
    }
    await renderWithRouter(<PracticeFocusBadge />)
    expect(screen.queryByTestId("practice-focus-badge")).toBeNull()
  })

  it("有重點時標出本輪加強的類型", async () => {
    profile = {
      focus_type: "atm",
      focus_label: "解除分期",
      note: "前測顯示你在「解除分期」最容易失手，接下來會多練這一類。",
      weights: EVEN,
      source: "pretest",
      answers_seen: 0,
    }
    await renderWithRouter(<PracticeFocusBadge />)
    expect(screen.getByTestId("practice-focus-badge").textContent).toBe(
      "本輪加強：解除分期",
    )
  })
})
