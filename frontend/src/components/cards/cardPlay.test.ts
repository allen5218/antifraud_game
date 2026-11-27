import { expect, test } from "bun:test"
import {
  EMPTY_MATCH,
  matchAnswer,
  splitBlank,
  tapLeft,
  tapRight,
  toggleStep,
} from "./cardPlay"

test("填空切成空格前後", () => {
  expect(splitBlank("真的客服不會叫你去＿＿。")).toEqual([
    "真的客服不會叫你去",
    "。",
  ])
  expect(splitBlank("沒有空格")).toBeNull()
})

test("排順序點一下加到最後，再點拿回來", () => {
  expect(toggleStep([], "a")).toEqual(["a"])
  expect(toggleStep(["a", "b"], "a")).toEqual(["b"])
  expect(toggleStep(["b"], "a")).toEqual(["b", "a"])
})

test("配對：先點左再點右就配起來", () => {
  let s = tapLeft(EMPTY_MATCH, "L1")
  expect(s.pending).toBe("L1")
  s = tapRight(s, "R2")
  expect(s).toEqual({ pairs: { L1: "R2" }, pending: null })
})

test("配對：右邊被搶走時，原本的配對拆掉", () => {
  let s = tapRight(tapLeft(EMPTY_MATCH, "L1"), "R1")
  s = tapRight(tapLeft(s, "L2"), "R1")
  expect(s.pairs).toEqual({ L2: "R1" })
})

test("配對：點已經配好的左邊會拆開", () => {
  const s = tapLeft({ pairs: { L1: "R1" }, pending: null }, "L1")
  expect(s.pairs).toEqual({})
  expect(s.pending).toBe("L1")
})

test("配對：沒先點左邊，點右邊不會配", () => {
  expect(tapRight(EMPTY_MATCH, "R1")).toEqual(EMPTY_MATCH)
})

test("配完才給答案，照左邊順序", () => {
  const left = [
    { id: "L1", text: "a" },
    { id: "L2", text: "b" },
  ]
  expect(matchAnswer(left, { L1: "R2" })).toBeNull()
  expect(matchAnswer(left, { L2: "R1", L1: "R2" })).toEqual(["R2", "R1"])
})
