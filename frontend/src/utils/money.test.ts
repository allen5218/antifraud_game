import { describe, expect, it } from "bun:test"
import {
  absMoney,
  addMoney,
  compareMoney,
  formatMoney,
  isGreaterOrEqual,
  isGreaterThan,
  parseBigIntSafe,
  subMoney,
} from "./money"

describe("money utilities", () => {
  describe("parseBigIntSafe", () => {
    it("handles null, undefined, empty string", () => {
      expect(parseBigIntSafe(null)).toBe(0n)
      expect(parseBigIntSafe(undefined)).toBe(0n)
      expect(parseBigIntSafe("")).toBe(0n)
      expect(parseBigIntSafe("   ")).toBe(0n)
      expect(parseBigIntSafe("abc")).toBe(0n)
    })

    it("handles numbers and floats", () => {
      expect(parseBigIntSafe(0)).toBe(0n)
      expect(parseBigIntSafe(123)).toBe(123n)
      expect(parseBigIntSafe(123.99)).toBe(123n)
      expect(parseBigIntSafe(-456.7)).toBe(-456n)
      expect(parseBigIntSafe(NaN)).toBe(0n)
      expect(parseBigIntSafe(Infinity)).toBe(0n)
    })

    it("handles decimal strings and large numbers", () => {
      expect(parseBigIntSafe("123456")).toBe(123456n)
      expect(parseBigIntSafe("123456.789")).toBe(123456n)
      expect(parseBigIntSafe("-9876.54")).toBe(-9876n)
      expect(parseBigIntSafe("9007199254740993")).toBe(9007199254740993n)
      expect(
        parseBigIntSafe("123456789012345678901234567890"),
      ).toBe(123456789012345678901234567890n)
    })
  })

  describe("arithmetic", () => {
    it("adds correctly", () => {
      expect(addMoney(100, 200, "300.5")).toBe(600n)
      expect(addMoney(null, 50, -20)).toBe(30n)
      expect(addMoney("9007199254740991", "10")).toBe(9007199254741001n)
    })

    it("subtracts correctly", () => {
      expect(subMoney(1000, 250)).toBe(750n)
      expect(subMoney("500", "600")).toBe(-100n)
    })

    it("computes absolute values", () => {
      expect(absMoney(-500n)).toBe(500n)
      expect(absMoney(500n)).toBe(500n)
      expect(absMoney("-123.4")).toBe(123n)
    })
  })

  describe("comparisons", () => {
    it("compares correctly", () => {
      expect(compareMoney(100, 200)).toBe(-1)
      expect(compareMoney(200, 200)).toBe(0)
      expect(compareMoney(300, 200)).toBe(1)
      expect(isGreaterOrEqual(200, 200)).toBe(true)
      expect(isGreaterOrEqual(201, 200)).toBe(true)
      expect(isGreaterOrEqual(199, 200)).toBe(false)
      expect(isGreaterThan(201, 200)).toBe(true)
      expect(isGreaterThan(200, 200)).toBe(false)
    })
  })

  describe("formatMoney", () => {
    it("formats standard numbers with commas", () => {
      expect(formatMoney(0)).toBe("0")
      expect(formatMoney(500)).toBe("500")
      expect(formatMoney(1234)).toBe("1,234")
      expect(formatMoney(1234567)).toBe("1,234,567")
      expect(formatMoney("-1234567")).toBe("-1,234,567")
      expect(formatMoney("9007199254740993")).toBe("9,007,199,254,740,993")
    })

    it("formats abbreviated scales", () => {
      expect(formatMoney(500, { abbreviated: true })).toBe("500")
      expect(formatMoney(1200, { abbreviated: true })).toBe("1.2K")
      expect(formatMoney(1250000, { abbreviated: true })).toBe("1.25M")
      expect(formatMoney(2500000000, { abbreviated: true })).toBe("2.5B")
      expect(formatMoney(3750000000000n, { abbreviated: true })).toBe("3.75T")
      expect(formatMoney(-5200000, { abbreviated: true })).toBe("-5.2M")
    })
  })
})
