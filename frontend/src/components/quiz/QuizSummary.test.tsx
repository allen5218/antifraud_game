import { afterEach, describe, expect, it } from "bun:test"
import { cleanup, render, screen } from "@testing-library/react"
import { QuizSummary } from "./QuizSummary"

afterEach(cleanup)

describe("<QuizSummary />", () => {
  it("shows reward and weakness", () => {
    render(
      <QuizSummary
        result={{
          correct_count: 4,
          total: 5,
          best_streak: 3,
          cash_earned: 176,
          xp_earned: 80,
          weakness_summary: [{ tag: "authority", count: 2 }],
        }}
        onRestart={() => {}}
      />,
    )
    expect(screen.getByText(/4 \/ 5/)).toBeTruthy()
    expect(screen.getByText(/\+\$176/)).toBeTruthy()
    expect(screen.getByText(/\+80 XP/)).toBeTruthy()
    expect(screen.getByText(/authority/)).toBeTruthy()
  })
})
