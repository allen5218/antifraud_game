import { expect, test } from "bun:test"
import type { HomeSummary } from "@/hooks/useHomeSummary"
import { tourSteps } from "./tour"

function summary(overrides: Partial<HomeSummary> = {}): HomeSummary {
  return {
    room_stage: 0,
    mascot_image_url: "/assets/mascot/shiba/base.webp",
    pretest_done: false,
    inbox_pending: 5,
    daily_unlocked: false,
    daily_done: false,
    exam_active_attempt_id: null,
    exam_can_start: true,
    retake: null,
    focus_type: null,
    focus_label: null,
    badges: [],
    ...overrides,
  }
}

test("一件一件介紹家具，再講錢、裝備、購物和選單", () => {
  const targets = tourSteps(summary(), false).map((s) => String(s.target))
  expect(targets).toEqual([
    "null",
    "tv",
    "letters",
    "phone",
    "calendar",
    "bookshelf",
    "cash",
    "progression",
    "shop",
    "menu",
    "null",
  ])
})

test("試測帳號看完導覽就去做綜合檢測", () => {
  const steps = tourSteps(summary({ trial: true }), false)
  expect(steps.at(-1)?.action).toEqual({ label: "開始檢測", to: "/exam" })
})

test("新帳號看完導覽就去做入門前測", () => {
  const steps = tourSteps(summary(), false)
  expect(steps.at(-1)?.action).toEqual({ label: "開始", to: "/pretest" })
})

test("從選單重看導覽，看完只是關掉", () => {
  const steps = tourSteps(summary({ trial: true }), true)
  expect(steps.at(-1)?.action).toBeUndefined()
})

test("導覽文字不夾英文、不用破折號", () => {
  for (const step of tourSteps(summary(), false)) {
    // 「AI」是遊戲裡固定的說法（AI 角色），其他英文不要
    expect(`${step.title}${step.text}`.replaceAll("AI", "")).not.toMatch(
      /[A-Za-z]|—|──/,
    )
  }
})

test("裝備那一步亮頁首的裝備按鈕，只講大概，細節點進去看", () => {
  const step = tourSteps(summary(), false).find(
    (s) => s.target === "progression",
  )
  expect(step?.title).toContain("裝備")
  expect(step?.text).toContain("點進去")
})

test("月曆那一步講到兩週一期的競技榜", () => {
  const step = tourSteps(summary(), false).find((s) => s.target === "calendar")
  expect(step?.text).toContain("兩週")
})
