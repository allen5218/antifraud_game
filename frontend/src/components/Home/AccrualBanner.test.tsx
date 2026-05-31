import { afterEach, beforeEach, describe, expect, it } from "bun:test"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import { useEconomyStore } from "@/stores/economy"
import { AccrualBanner } from "./AccrualBanner"

afterEach(() => {
  cleanup()
})

describe("<AccrualBanner />", () => {
  beforeEach(() => useEconomyStore.getState().reset())

  it("shows pending amount and claim button when pending > 0", () => {
    render(<AccrualBanner />)
    expect(screen.getByText(/\+\$840/)).toBeTruthy()
    expect(screen.getByRole("button", { name: /領取/ })).toBeTruthy()
  })

  it("hides when pending is 0", () => {
    useEconomyStore.getState().claimAccrual()
    const { container } = render(<AccrualBanner />)
    expect(container.firstChild).toBeNull()
  })

  it("clicking 領取 moves pending into cash", () => {
    const { cash: cashBefore, pendingAccrual } = useEconomyStore.getState()
    render(<AccrualBanner />)
    fireEvent.click(screen.getByRole("button", { name: /領取/ }))
    expect(useEconomyStore.getState().cash).toBe(cashBefore + pendingAccrual)
  })
})
