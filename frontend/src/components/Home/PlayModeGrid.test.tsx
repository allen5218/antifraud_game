import { afterEach, beforeEach, describe, expect, it } from "bun:test"
import { cleanup, render, screen } from "@testing-library/react"
import { useEconomyStore } from "@/stores/economy"
import { PlayModeGrid } from "./PlayModeGrid"

describe("<PlayModeGrid />", () => {
  beforeEach(() => useEconomyStore.getState().reset())
  afterEach(cleanup)

  it("locks cards above current level, unlocks others", () => {
    render(<PlayModeGrid />)
    // default level 3
    const unlocked = screen.getByTestId("mode-題組訓練")
    const locked = screen.getByTestId("mode-排行榜")
    expect(unlocked.getAttribute("aria-disabled")).toBe("false")
    expect(unlocked.className).not.toContain("opacity-55")
    expect(locked.getAttribute("aria-disabled")).toBe("true")
    expect(locked.className).toContain("opacity-55")
  })
})
