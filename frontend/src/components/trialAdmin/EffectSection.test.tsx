import { afterEach, expect, test } from "bun:test"
import { cleanup, render, screen } from "@testing-library/react"
import type { EffectAnalytics, PairedChange, SurveyAnalytics } from "@/client"
import { EffectSection } from "./EffectSection"

afterEach(cleanup)

const TYPES = ["investment", "fake-sale", "shopping", "romance", "atm"]
const TAGS = [
  "time_pressure",
  "authority",
  "greed",
  "social_proof",
  "trust_building",
]

function change(n: number, before: number | null, after: number | null) {
  return {
    n,
    before_mean: before,
    after_mean: after,
    diff_mean: before == null || after == null ? null : after - before,
    improved: n,
    same: 0,
    worse: 0,
  } satisfies PairedChange
}

function effect(n: number): EffectAnalytics {
  const pct = n ? 50 : null
  return {
    exams: [
      {
        version: 2,
        label: "新版檢測",
        pretest_items: 10,
        exam: {
          stages: [
            {
              key: "pretest_weakest",
              label: "前測關（最弱一類）",
              accuracy: n ? 25 : null,
              people: n,
              items: n * 4,
            },
            {
              key: "swipe",
              label: "滑卡",
              accuracy: pct,
              people: n,
              items: n * 2,
            },
            {
              key: "cards",
              label: "卡片題",
              accuracy: pct,
              people: n,
              items: n * 5,
            },
            {
              key: "message",
              label: "訊息判讀",
              accuracy: pct,
              people: n,
              items: n * 5,
            },
            {
              key: "scenario",
              label: "情境對抗",
              accuracy: pct,
              people: n,
              items: n,
            },
          ],
          change: n ? change(n, 25, 80) : change(0, null, null),
        },
        repeat: {
          people: 0,
          pretest: change(0, null, null),
          score: change(0, null, null),
          failed_first: 0,
          retook: 0,
          retake_passed: 0,
        },
      },
    ],
    entry: {
      total: n ? change(n, 50, 75) : change(0, null, null),
      by_type: TYPES.map((t) => ({
        fraud_type: t,
        before: pct,
        after: pct,
        people: n,
      })),
      practiced_between: 0,
    },
    practice: {
      baseline_people: n,
      by_type: TYPES.map((t) => ({
        fraud_type: t,
        before: pct,
        after: pct,
        people: n,
      })),
      curve: n
        ? [
            {
              label: "1–10",
              accuracy: 60,
              missed_rate: 20,
              people: n,
              items: n * 10,
            },
          ]
        : [],
      tags: TAGS.map((t) => ({
        tag: t,
        label: t,
        first_half: 0,
        second_half: 0,
      })),
      modes: [
        { mode: "card", label: "卡片練習", change: change(0, null, null) },
        { mode: "swipe", label: "滑卡", change: change(0, null, null) },
        { mode: "quiz", label: "訊息判讀", change: change(0, null, null) },
        { mode: "scenario", label: "情境對抗", change: change(0, null, null) },
      ],
    },
    volume: {
      exam_people: n,
      practiced_people: n,
      median_answers: n ? 10 : null,
      median_days: n ? 1 : null,
      scenario_rounds: 0,
    },
  }
}

const survey: SurveyAnalytics = {
  responses: 0,
  likert: [],
  confidence: change(0, null, null),
  choices: [],
  texts: [],
}

test("有資料時寫出前後的答對率", () => {
  render(<EffectSection effect={effect(8)} survey={survey} />)
  // 只有一版時標題不標版本
  expect(screen.getByText("檢測：前測關到後面幾關")).toBeTruthy()
  expect(screen.getByText("卡片題")).toBeTruthy()
  expect(screen.getByText("平均 25% → 80%，8 人裡 8 人進步")).toBeTruthy()
  expect(screen.getByText("平均 50% → 75%，8 人裡 8 人進步")).toBeTruthy()
})

test("沒有資料時每張卡都寫還沒有資料", () => {
  render(<EffectSection effect={effect(0)} survey={survey} />)
  expect(screen.getAllByText("還沒有資料").length).toBeGreaterThanOrEqual(8)
  expect(screen.queryByText(/平均 .*→/)).toBeNull()
})

test("人數少於 5 標示只供參考", () => {
  render(<EffectSection effect={effect(3)} survey={survey} />)
  expect(screen.getAllByText("人數少，只供參考。").length).toBeGreaterThan(0)
})

test("範圍內有新舊兩版檢測時各畫一組，前測題數照各版", () => {
  const data = effect(8)
  const [current] = data.exams
  data.exams = [
    current,
    {
      ...current,
      version: 1,
      label: "舊版檢測",
      pretest_items: 20,
      repeat: { ...current.repeat, people: 2, pretest: change(2, 12, 15) },
    },
  ]
  render(<EffectSection effect={data} survey={survey} />)
  expect(screen.getByText("檢測：前測關到後面幾關（新版檢測）")).toBeTruthy()
  expect(screen.getByText("檢測：前測關到後面幾關（舊版檢測）")).toBeTruthy()
  expect(screen.getByText("考兩次以上的人（舊版檢測）")).toBeTruthy()
  expect(screen.getByText("前測關答對題數（20 題）")).toBeTruthy()
})
