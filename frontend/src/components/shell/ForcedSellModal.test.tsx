import { afterEach, beforeEach, describe, expect, it } from "bun:test"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import { useEconomyStore } from "@/stores/economy"
import { ForcedSellModal } from "./ForcedSellModal"

describe("<ForcedSellModal />", () => {
  beforeEach(() => useEconomyStore.getState().reset())
  afterEach(cleanup)

  it("renders null when bankruptcyPending is false", () => {
    const { container } = render(<ForcedSellModal />)
    expect(container.firstChild).toBeNull()
  })

  it("renders modal with deficit when bankruptcyPending is true", () => {
    useEconomyStore.getState().triggerBankruptcy(35000)
    render(<ForcedSellModal />)
    expect(screen.getByText(/被詐騙/)).toBeTruthy()
    expect(screen.getByText(/現金不足/)).toBeTruthy()
  })

  it("confirm disabled when recovered < deficit, enabled after enough selected", () => {
    // cash 12450; trigger 14000 -> deficit 1550; 套房(mock-2) recovers floor(5000*0.6)=3000 >= 1550
    useEconomyStore.getState().triggerBankruptcy(14000)
    render(<ForcedSellModal />)
    const btn = screen.getByRole("button", { name: /確認變賣/ })
    expect(btn.hasAttribute("disabled")).toBe(true)
    fireEvent.click(screen.getByTestId("sell-row-mock-2"))
    expect(btn.hasAttribute("disabled")).toBe(false)
  })
})
