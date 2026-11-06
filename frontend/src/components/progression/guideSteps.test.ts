import { afterEach, expect, test } from "bun:test"
import {
  GUIDE_STEPS,
  guideSeen,
  markGuideSeen,
  PROGRESSION_GUIDE_KEY,
} from "./guideSteps"

afterEach(() => {
  localStorage.removeItem(PROGRESSION_GUIDE_KEY)
})

test("說明涵蓋資源、核心等級、配裝、強化突破、兩週競技", () => {
  const all = GUIDE_STEPS.map((s) => `${s.title}${s.text}`).join("")
  for (const word of [
    "養成經驗",
    "鍛造能量",
    "核心養成階級",
    "生效配裝",
    "強化",
    "突破圖紙",
    "競技榜",
    "下一局",
  ]) {
    expect(all).toContain(word)
  }
})

test("說明文字不夾英文、不用破折號與「不是…而是」", () => {
  for (const step of GUIDE_STEPS) {
    const text = `${step.title}${step.text}`
    expect(text).not.toMatch(/[A-Za-z]|—|──/)
    expect(text).not.toMatch(/不是.*而是/)
  }
})

test("沒看過才自動打開，看過就記住", () => {
  expect(guideSeen()).toBe(false)
  markGuideSeen()
  expect(guideSeen()).toBe(true)
})

test("瀏覽器不給存東西時當成沒看過，也不會壞掉", () => {
  const original = Storage.prototype.getItem
  const originalSet = Storage.prototype.setItem
  Storage.prototype.getItem = () => {
    throw new Error("blocked")
  }
  Storage.prototype.setItem = () => {
    throw new Error("blocked")
  }
  try {
    expect(guideSeen()).toBe(false)
    expect(() => markGuideSeen()).not.toThrow()
  } finally {
    Storage.prototype.getItem = original
    Storage.prototype.setItem = originalSet
  }
})
