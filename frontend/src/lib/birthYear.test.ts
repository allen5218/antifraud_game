import { expect, test } from "bun:test"
import { parseBirthYear, taipeiYear } from "./birthYear"

const YEAR = 2026

test("西元年照收", () => {
  expect(parseBirthYear("1975", YEAR)).toBe(1975)
  expect(parseBirthYear(" 2001 ", YEAR)).toBe(2001)
})

test("民國年換成西元", () => {
  expect(parseBirthYear("64", YEAR)).toBe(1975)
  expect(parseBirthYear("民國64年", YEAR)).toBe(1975)
  expect(parseBirthYear("100", YEAR)).toBe(2011)
})

test("不合理的年份回 null", () => {
  expect(parseBirthYear("", YEAR)).toBeNull()
  expect(parseBirthYear("abc", YEAR)).toBeNull()
  expect(parseBirthYear("1899", YEAR)).toBeNull()
  expect(parseBirthYear("2025", YEAR)).toBeNull() // 才 1 歲
  expect(parseBirthYear("120", YEAR)).toBeNull() // 民國 120 年還沒到
  expect(parseBirthYear("12345", YEAR)).toBeNull()
})

test("台灣時間跨年比 UTC 早 8 小時", () => {
  expect(taipeiYear(new Date("2026-12-31T16:30:00Z"))).toBe(2027)
  expect(taipeiYear(new Date("2026-12-31T15:30:00Z"))).toBe(2026)
})
