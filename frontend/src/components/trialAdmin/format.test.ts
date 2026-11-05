import { expect, test } from "bun:test"
import { notAskedText } from "./format"

test("沒被問到的人數另外寫，0 人就不寫", () => {
  expect(notAskedText(3)).toBe("・沒被問到 3 人")
  expect(notAskedText(0)).toBe("")
  expect(notAskedText(undefined)).toBe("")
})
