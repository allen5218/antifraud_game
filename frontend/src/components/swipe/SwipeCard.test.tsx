import { describe, expect, it } from "bun:test"
import { fireEvent, render, screen } from "@testing-library/react"
import { SwipeCard } from "./SwipeCard"

describe("<SwipeCard />", () => {
  it("calls onJudge(true) for 詐騙 and onJudge(false) for 正常", () => {
    const calls: boolean[] = []
    render(
      <SwipeCard
        card={{
          id: "c1",
          scenario: "測試情境",
          source_label: "來源",
          fraud_type: "investment",
          difficulty: 1,
        }}
        onJudge={(g) => calls.push(g)}
      />,
    )
    fireEvent.click(screen.getByRole("button", { name: /詐騙/ }))
    fireEvent.click(screen.getByRole("button", { name: /正常/ }))
    expect(calls).toEqual([true, false])
  })
})
