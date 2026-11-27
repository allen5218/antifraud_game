import { afterEach, describe, expect, it } from "bun:test"
import { cleanup, screen } from "@testing-library/react"
import { renderWithRouter } from "@/test/renderWithRouter"
import { QuizSummary } from "./QuizSummary"

afterEach(cleanup)

describe("<QuizSummary />", () => {
  it("shows reward and weakness", async () => {
    await renderWithRouter(
      <QuizSummary
        result={{
          correct_count: 4,
          total: 5,
          best_streak: 3,
          cash_earned: 176,
          xp_earned: 80,
          weakness_summary: [
            { tag: "authority", label: "冒充官方或專家", count: 2 },
          ],
        }}
        onRestart={() => {}}
      />,
    )
    expect(screen.getByText(/4 \/ 5/)).toBeTruthy()
    expect(screen.getByText(/\+\$176/)).toBeTruthy()
    expect(screen.getByText(/\+80 XP/)).toBeTruthy()
    expect(screen.getByText(/冒充官方或專家 ×2/)).toBeTruthy()
    expect(screen.queryByText(/authority/)).toBeNull()
    expect(
      screen.getByRole("link", { name: "回首頁" }).getAttribute("href"),
    ).toBe("/")
    expect(
      screen.getByRole("link", { name: /去經營收租/ }).getAttribute("href"),
    ).toBe("/room")
  })

  it("keeps the estate entry without offering another daily round", async () => {
    await renderWithRouter(
      <QuizSummary
        result={{
          correct_count: 0,
          total: 5,
          best_streak: 0,
          cash_earned: "0",
          xp_earned: 0,
          weakness_summary: [],
        }}
      />,
    )
    expect(screen.queryByRole("button", { name: "再來一輪" })).toBeNull()
    expect(screen.getByRole("link", { name: /去經營收租/ })).toBeTruthy()
  })
})
