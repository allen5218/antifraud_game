import { afterEach, expect, mock, test } from "bun:test"
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react"
import type { ExamState } from "@/client"
import { ExamStage } from "./ExamStage"

afterEach(() => {
  cleanup()
  sessionStorage.clear()
})
const state: ExamState = {
  id: "s",
  mode: "specialized",
  status: "active",
  stage: "swipe",
  fraud_type: "romance",
  expires_at: "2099-01-01T00:00:00Z",
  stage_items: [
    { id: "c1", source_label: "通知", scenario: "請先看資料" },
    { id: "c2", source_label: "簡訊", scenario: "今天要付款" },
  ],
  progress: { stage_index: 0, stage_count: 3 },
  scenario: null,
  result: null,
}

test("滑卡整關才送出、不顯示回饋，重掛保留原答案", async () => {
  const submit = mock(async () => {})
  render(<ExamStage state={state} onSubmit={submit} busy={false} />)
  fireEvent.click(screen.getByRole("button", { name: "詐騙" }))
  expect(submit).not.toHaveBeenCalled()
  expect(screen.queryByText(/答對|答錯|解說/)).toBeNull()
  cleanup()
  render(<ExamStage state={state} onSubmit={submit} busy={false} />)
  expect(screen.getByText("今天要付款")).toBeTruthy()
  fireEvent.click(screen.getByRole("button", { name: "正常" }))
  fireEvent.click(screen.getByRole("button", { name: "送出這一關" }))
  await waitFor(() => expect(submit).toHaveBeenCalledTimes(1))
  expect(submit.mock.calls[0][0]).toEqual([
    { card_id: "c1", guess_is_scam: true },
    { card_id: "c2", guess_is_scam: false },
  ])
})

test("真假與話術複選整關提交，空選項仍可作答", async () => {
  const submit = mock(async () => {})
  const messages: ExamState = {
    ...state,
    stage: "message",
    stage_items: [
      { item_id: "m", kind: "verdict", title: "通知", narrative: "你好" },
      {
        item_id: "t",
        kind: "tactics",
        title: "話術",
        narrative: "馬上付錢",
        question: "用了哪些話術？",
        options: [{ tag: "authority", label: "冒充官方或專家" }],
      },
    ],
  }
  render(<ExamStage state={messages} onSubmit={submit} busy={false} />)
  fireEvent.click(screen.getByRole("button", { name: "這是正常的" }))
  expect(submit).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole("button", { name: "送出答案" }))
  fireEvent.click(screen.getByRole("button", { name: "送出這一關" }))
  await waitFor(() => expect(submit).toHaveBeenCalledTimes(1))
  expect(submit.mock.calls[0][0]).toEqual([
    { item_id: "m", guess_is_scam: false },
    { item_id: "t", tags: [] },
  ])
})

test("送出期間不能再次交卷", () => {
  sessionStorage.setItem(
    "exam-draft:s:swipe",
    JSON.stringify([
      { card_id: "c1", guess_is_scam: true },
      { card_id: "c2", guess_is_scam: false },
    ]),
  )
  const submit = mock(async () => {})
  render(<ExamStage state={state} onSubmit={submit} busy />)
  expect(
    (screen.getByRole("button", { name: "正在送出…" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true)
})

test("綜合前測沿用選項外觀，二十題都作答後一次提交", async () => {
  const submit = mock(async () => {})
  const pretest: ExamState = {
    ...state,
    mode: "comprehensive",
    stage: "pretest",
    fraud_type: null,
    progress: { stage_index: 0, stage_count: 4 },
    stage_items: Array.from({ length: 20 }, (_, i) => ({
      id: `q${i}`,
      question_text: `前測第 ${i + 1} 題`,
      options: [
        { key: "A", text: "先查證" },
        { key: "B", text: "照做" },
      ],
    })),
  }
  render(<ExamStage state={pretest} onSubmit={submit} busy={false} />)
  for (let i = 0; i < 20; i++) {
    await screen.findByText(`前測第 ${i + 1} 題`)
    fireEvent.click(screen.getByRole("button", { name: "A 先查證" }))
    expect(submit).not.toHaveBeenCalled()
  }
  fireEvent.click(await screen.findByRole("button", { name: "送出這一關" }))
  await waitFor(() => expect(submit).toHaveBeenCalledTimes(1))
  expect(submit.mock.calls[0][0]).toEqual(
    Array.from({ length: 20 }, (_, i) => ({
      question_id: `q${i}`,
      selected_option: "A",
    })),
  )
}, 15000)
