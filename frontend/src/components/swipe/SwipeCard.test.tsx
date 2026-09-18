import { describe, expect, it } from "bun:test"
import { fireEvent, render, screen } from "@testing-library/react"
import { SwipeCard } from "./SwipeCard"

describe("<SwipeCard />", () => {
  it("calls onJudge with scam, skip, and legit", () => {
    const calls: string[] = []
    render(
      <SwipeCard
        card={{
          id: "c1",
          scenario: "測試情境",
        }}
        onJudge={(action) => calls.push(action)}
      />,
    )
    fireEvent.click(screen.getByRole("button", { name: /詐騙/ }))
    fireEvent.click(screen.getByRole("button", { name: /略過/ }))
    fireEvent.click(screen.getByRole("button", { name: /正常/ }))
    expect(calls).toEqual(["scam", "skip", "legit"])
  })
})
