import { describe, expect, it } from "bun:test"
import type { ExamState } from "@/client"
import {
  errorCode,
  examKindLabel,
  gateRemaining,
  readDraft,
  saveDraft,
  secondsLeft,
} from "./exam"

const state: ExamState = {
  id: "attempt",
  mode: "specialized",
  status: "active",
  stage: "swipe",
  fraud_type: "romance",
  expires_at: "2026-10-09T11:00:00Z",
  stage_items: [
    { id: "one", source_label: "訊息", scenario: "你好" },
    { id: "two", source_label: "訊息", scenario: "請看說明" },
  ],
  progress: { stage_index: 0, stage_count: 3 },
  scenario: null,
  result: null,
}
describe("檢測草稿與狀態", () => {
  it("綜合檢測前測還沒定類型時只寫綜合檢測，專項帶上類型名稱", () => {
    expect(examKindLabel("comprehensive", null)).toBe("綜合檢測")
    expect(examKindLabel("comprehensive", undefined)).toBe("綜合檢測")
    expect(examKindLabel("comprehensive", "investment")).toBe(
      "綜合檢測・投資詐騙",
    )
    expect(examKindLabel("specialized", "atm")).toBe("專項檢測・解除分期")
  })
  it("重新整理保留已作答與整關重送的原答案", () => {
    const answers = [
      { card_id: "one", guess_is_scam: true },
      { card_id: "two", guess_is_scam: false },
    ]
    saveDraft(state, answers)
    expect(readDraft(state)).toEqual(answers)
    expect(readDraft({ ...state, stage: "message" })).toEqual([])
  })
  it("拒絕題序不符或損壞的草稿", () => {
    saveDraft(state, [{ card_id: "two", guess_is_scam: true }])
    expect(readDraft(state)).toEqual([])
    sessionStorage.setItem("exam-draft:attempt:swipe", "broken")
    expect(readDraft(state)).toEqual([])
  })
  it("草稿不接受真假字串或前測不存在的選項", () => {
    sessionStorage.setItem(
      "exam-draft:attempt:swipe",
      JSON.stringify([{ card_id: "one", guess_is_scam: "false" }]),
    )
    expect(readDraft(state)).toEqual([])
    const pretest = {
      ...state,
      stage: "pretest" as const,
      stage_items: [
        {
          id: "q",
          question_text: "問題",
          options: [{ key: "A", text: "查證" }],
        },
      ],
    }
    saveDraft(pretest, [{ question_id: "q", selected_option: "B" }])
    expect(readDraft(pretest)).toEqual([])
  })
  it("剩餘時間以到期時間計算且不低於零", () => {
    expect(
      secondsLeft(state.expires_at, Date.parse("2026-10-09T10:59:01Z")),
    ).toBe(59)
    expect(
      secondsLeft(state.expires_at, Date.parse("2026-10-09T11:00:01Z")),
    ).toBe(0)
  })
  it("補考只列還差的數量，包含最近十題答對門檻", () => {
    expect(
      gateRemaining({
        fraud_type: "romance",
        swipe: { done: 4, need: 6 },
        quiz: { done: 2, need: 5 },
        scenario: { done: 0, need: 1 },
        recent: { correct: 5, total: 8, need: 7 },
        met: false,
      }),
    ).toBe(
      "還差滑卡 2 張、訊息判讀 3 題、情境對抗 1 場。最近十題還要答對 2 題。",
    )
  })
  it("從 SDK 錯誤讀取檢測鎖，不將一般錯誤視為鎖", () => {
    expect(
      errorCode({
        status: 400,
        body: { detail: { code: "exam_in_progress" } },
      }),
    ).toBe("exam_in_progress")
    expect(errorCode(new Error("network"))).toBeUndefined()
  })
})
