import { beforeEach, describe, expect, it } from "bun:test"
import { useEconomyStore } from "./economy"

describe("economy store (mock)", () => {
  beforeEach(() => {
    useEconomyStore.getState().reset()
  })

  it("starts with default mock state", () => {
    const s = useEconomyStore.getState()
    expect(s.cash).toBe(12450)
    expect(s.streak).toBe(5)
    expect(s.level).toBe(3)
    expect(s.pendingAccrual).toBe(840)
    expect(s.bankruptcyPending).toBe(false)
    expect(s.ownedProperties.length).toBeGreaterThan(0)
  })

  it("claimAccrual moves pending into cash", () => {
    useEconomyStore.getState().claimAccrual()
    expect(useEconomyStore.getState().cash).toBe(12450 + 840)
    expect(useEconomyStore.getState().pendingAccrual).toBe(0)
  })

  it("triggerBankruptcy sets cash negative and bankruptcyPending true", () => {
    useEconomyStore.getState().triggerBankruptcy(35000)
    expect(useEconomyStore.getState().cash).toBeLessThan(0)
    expect(useEconomyStore.getState().bankruptcyPending).toBe(true)
  })

  it("liquidateProperties sells selected and credits exact recovery", () => {
    useEconomyStore.getState().triggerBankruptcy(3000)
    const owned = useEconomyStore.getState().ownedProperties
    const cashBefore = useEconomyStore.getState().cash // 12450 - 3000 = 9450
    const expectedRecovery = owned.reduce(
      (sum, p) => sum + Math.floor(p.tier.price * 0.6),
      0,
    )
    useEconomyStore.getState().liquidateProperties(owned.map((p) => p.id))
    expect(useEconomyStore.getState().cash).toBe(cashBefore + expectedRecovery)
    expect(useEconomyStore.getState().bankruptcyPending).toBe(false)
  })

  it("reset restores default ownedProperties after liquidation", () => {
    useEconomyStore.getState().liquidateProperties(["mock-1"])
    useEconomyStore.getState().reset()
    expect(useEconomyStore.getState().ownedProperties).toHaveLength(2)
  })
})
