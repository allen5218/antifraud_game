import { describe, expect, it } from "bun:test"
import { equipmentActionKey, formatFactor } from "./progressionDisplay"

describe("formatFactor", () => {
  it("把很長的精確倍率縮成手機放得下的長度", () => {
    expect(formatFactor("95.3962166440690129601298432")).toBe("95.4")
    expect(formatFactor("1.2")).toBe("1.2")
    expect(formatFactor("1")).toBe("1")
    expect(formatFactor("1.04976")).toBe("1.05")
  })
  it("很大的倍率加上千分位", () => {
    expect(formatFactor("12345.678")).toBe("12,346")
  })
  it("沒有值或看不懂的值用 1", () => {
    expect(formatFactor(undefined)).toBe("1")
    expect(formatFactor("abc")).toBe("1")
  })
})

describe("equipmentActionKey", () => {
  const item = {
    id: "11111111-2222-3333-4444-555555555555",
    rank: 2,
    rank_cap: 5,
  }
  it("同一階重送用同一把鑰匙（後端不會再扣一次）", () => {
    expect(equipmentActionKey("upgrade", item)).toBe(
      equipmentActionKey("upgrade", { ...item }),
    )
  })
  it("升了一階就換新鑰匙", () => {
    expect(equipmentActionKey("upgrade", item)).not.toBe(
      equipmentActionKey("upgrade", { ...item, rank: 3 }),
    )
  })
  it("突破看上限", () => {
    expect(equipmentActionKey("breakthrough", item)).not.toBe(
      equipmentActionKey("breakthrough", { ...item, rank_cap: 6 }),
    )
  })
  it("鑰匙不超過後端限制的 64 字", () => {
    expect(equipmentActionKey("breakthrough", item).length).toBeLessThanOrEqual(
      64,
    )
  })
})
