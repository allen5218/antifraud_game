import { expect, test } from "bun:test"
import { formatCycle, formatDuration, formatYuan, perSecond } from "./format"

test("一萬以下照寫，以上用中文單位，不夾英文", () => {
  expect(formatYuan(0)).toBe("0")
  expect(formatYuan(1234)).toBe("1,234")
  expect(formatYuan(12_345)).toBe("1.23 萬")
  expect(formatYuan(123_456)).toBe("12.3 萬")
  expect(formatYuan(10_000)).toBe("1 萬")
  expect(formatYuan(250_000_000)).toBe("2.5 億")
  expect(formatYuan("12000000000000")).toBe("12 兆")
  expect(formatYuan(-45_000)).toBe("-4.5 萬")
  expect(formatYuan(`${10n ** 60n}`)).toMatch(/極$/)
  expect(formatYuan(`${10n ** 40n * 3n}`)).not.toMatch(/[A-Za-z]/)
})

test("每小時換成每秒，保留一位小數", () => {
  expect(perSecond(600)).toBe("0.1")
  expect(perSecond(3600)).toBe("1")
  expect(perSecond(5400)).toBe("1.5")
  expect(perSecond(3600 * 2_000_000)).toBe("200 萬")
})

test("收租時間與離開多久", () => {
  expect(formatCycle(6)).toBe("6 秒")
  expect(formatCycle(120)).toBe("2 分鐘")
  expect(formatCycle(14_400)).toBe("4 小時")
  expect(formatDuration(3600 * 3 + 60 * 20)).toBe("3 小時 20 分")
  expect(formatDuration(30)).toBe("1 分鐘")
  expect(formatDuration(3600 * 30)).toBe("1 天 6 小時")
})
