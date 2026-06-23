import { describe, expect, it } from "bun:test"
import { render, screen } from "@testing-library/react"
import { SwipeStatsBar } from "./SwipeStatsBar"

describe("<SwipeStatsBar />", () => {
  it("shows alertness, streak and progress", () => {
    render(
      <SwipeStatsBar
        alertness={2}
        maxAlertness={3}
        streak={4}
        progress={5}
        total={12}
      />,
    )
    expect(screen.getByTestId("swipe-alertness").textContent).toContain("2")
    expect(screen.getByText(/連勝 4/)).toBeTruthy()
    expect(screen.getByText(/5 \/ 12/)).toBeTruthy()
  })
})
