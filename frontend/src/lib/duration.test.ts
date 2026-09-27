import { describe, expect, it } from "bun:test"
import { formatDuration } from "./duration"

describe("formatDuration", () => {
  it("formats seconds and minutes in plain Chinese", () => {
    expect(formatDuration(0)).toBe("0 秒")
    expect(formatDuration(42)).toBe("42 秒")
    expect(formatDuration(65)).toBe("1 分 05 秒")
    expect(formatDuration(600)).toBe("10 分 00 秒")
  })
})
