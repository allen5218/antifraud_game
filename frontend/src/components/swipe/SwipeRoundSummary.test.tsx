import { describe, expect, it } from "bun:test"
import { render, screen } from "@testing-library/react"
import { SwipeRoundSummary } from "./SwipeRoundSummary"

describe("<SwipeRoundSummary />", () => {
  it("shows reward and weakness summary", () => {
    render(
      <SwipeRoundSummary
        result={{
          correct_count: 8,
          total: 12,
          best_streak: 6,
          cash_earned: 240,
          xp_earned: 80,
          weakness_summary: [{ tag: "authority", count: 2 }],
        }}
      />,
    )
    expect(screen.getByText(/\+\$240/)).toBeTruthy()
    expect(screen.getByText(/\+80 XP/)).toBeTruthy()
    expect(screen.getByText(/authority/)).toBeTruthy()
  })
})
