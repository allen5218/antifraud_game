import { afterEach, describe, expect, it } from "bun:test"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import { MatchQuestion } from "./MatchQuestion"
import { TacticsQuestion } from "./TacticsQuestion"
import { VerdictQuestion } from "./VerdictQuestion"

afterEach(cleanup)

describe("quiz 題型元件", () => {
  it("verdict 選第一個答案不會立即送出；按確認才送出", () => {
    let answer: boolean | undefined
    let signals: any
    render(
      <VerdictQuestion
        item={{
          item_id: "verdict-1",
          type: "verdict",
          fraud_type: "investment",
          title: "投資訊息",
          narrative: "保證獲利",
          difficulty: 2,
        }}
        index={0}
        total={5}
        disabled={false}
        onSubmit={(guessIsScam, s) => {
          answer = guessIsScam
          signals = s
        }}
      />,
    )

    const confirmBtn = screen.getByRole("button", { name: "就這樣" })
    expect(confirmBtn.hasAttribute("disabled")).toBe(true)

    // 點選答案但尚未確認，不可觸發 onSubmit
    fireEvent.click(screen.getByRole("button", { name: "我覺得有問題" }))
    expect(answer).toBeUndefined()
    expect(confirmBtn.hasAttribute("disabled")).toBe(false)

    // 點確認才送出
    fireEvent.click(confirmBtn)
    expect(answer).toBe(true)
    expect(signals?.response_time_ms).toBeGreaterThanOrEqual(0)
    expect(signals?.option_switch_count).toBe(0)
  })

  it("A → B → A 後送出，option_switch_count == 2；重按 A 不增加", () => {
    let signals: any
    render(
      <VerdictQuestion
        item={{
          item_id: "verdict-switch",
          type: "verdict",
          fraud_type: "investment",
          title: "切換測試",
          narrative: "測試切換次數",
          difficulty: 1,
        }}
        index={0}
        total={5}
        disabled={false}
        onSubmit={(_guess, s) => {
          signals = s
        }}
      />,
    )

    const optionProblem = screen.getByRole("button", { name: "我覺得有問題" })
    const optionFine = screen.getByRole("button", { name: "我覺得還好" })
    const confirmBtn = screen.getByRole("button", { name: "就這樣" })

    // 初始選 A (我覺得有問題) -> switch count 仍為 0
    fireEvent.click(optionProblem)
    // 重按 A -> 不增加
    fireEvent.click(optionProblem)

    // 切到 B (我覺得還好) -> switch count = 1
    fireEvent.click(optionFine)

    // 切回 A (我覺得有問題) -> switch count = 2
    fireEvent.click(optionProblem)

    fireEvent.click(confirmBtn)
    expect(signals?.option_switch_count).toBe(2)
  })

  it("送出的 response_time_ms >= 0，visibility hidden 後 interaction_obscured == true", () => {
    let signals: any
    render(
      <VerdictQuestion
        item={{
          item_id: "verdict-obscured",
          type: "verdict",
          fraud_type: "investment",
          title: "遮蔽測試",
          narrative: "測試頁面遮蔽訊號",
          difficulty: 1,
        }}
        index={0}
        total={5}
        disabled={false}
        onSubmit={(_guess, s) => {
          signals = s
        }}
      />,
    )

    // 模擬 visibilitychange 為 hidden
    Object.defineProperty(document, "visibilityState", {
      value: "hidden",
      writable: true,
      configurable: true,
    })
    fireEvent(document, new Event("visibilitychange"))

    fireEvent.click(screen.getByRole("button", { name: "我覺得還好" }))
    fireEvent.click(screen.getByRole("button", { name: "就這樣" }))

    expect(signals?.response_time_ms).toBeGreaterThanOrEqual(0)
    expect(signals?.interaction_obscured).toBe(true)
  })

  it("tactics 可改複選並回報已選數量，送出按鈕為「選好了」", () => {
    let selected: string[] = []
    render(
      <TacticsQuestion
        item={{
          item_id: "tactics-1",
          type: "tactics",
          fraud_type: "investment",
          title: "投資訊息",
          narrative: "今晚前加入",
          difficulty: 2,
          question: "用了哪些話術？",
          options: [
            { tag: "time_pressure", label: "時間壓力" },
            { tag: "authority", label: "權威服從" },
          ],
        }}
        index={1}
        total={5}
        disabled={false}
        onSubmit={(tags) => {
          selected = tags
        }}
      />,
    )

    fireEvent.click(screen.getByRole("checkbox", { name: "時間壓力" }))
    expect(screen.getByText("已選 1 個")).toBeTruthy()
    fireEvent.click(screen.getByRole("checkbox", { name: "權威服從" }))
    fireEvent.click(screen.getByRole("checkbox", { name: "時間壓力" }))
    expect(screen.getByText("已選 1 個")).toBeTruthy()
    fireEvent.click(screen.getByRole("button", { name: "選好了" }))

    expect(selected).toEqual(["authority"])
  })

  it("match 點選配對、可取消，且全部完成才能送出（按鈕為「配好了」）", () => {
    let pairs: Record<string, string> = {}
    render(
      <MatchQuestion
        item={{
          item_id: "match-1",
          type: "match",
          question: "把話術和例句配對起來",
          match_prompts: [
            { pair_id: "pair-1", text: "今晚前匯款" },
            { pair_id: "pair-2", text: "我是警察" },
          ],
          match_targets: [
            { tag: "time_pressure", label: "時間壓力" },
            { tag: "authority", label: "權威服從" },
          ],
        }}
        index={2}
        total={5}
        disabled={false}
        onSubmit={(answer) => {
          pairs = answer
        }}
      />,
    )

    const submit = screen.getByRole("button", { name: "配好了" })
    expect(submit.hasAttribute("disabled")).toBe(true)

    fireEvent.click(screen.getByRole("button", { name: /今晚前匯款/ }))
    fireEvent.click(screen.getByRole("button", { name: "時間壓力" }))
    expect(screen.getByText("已配對 1 / 2")).toBeTruthy()
    fireEvent.click(
      screen.getByRole("button", { name: "取消「今晚前匯款」的配對" }),
    )
    expect(screen.getByText("已配對 0 / 2")).toBeTruthy()

    fireEvent.click(screen.getByRole("button", { name: /今晚前匯款/ }))
    fireEvent.click(screen.getByRole("button", { name: "時間壓力" }))
    fireEvent.click(screen.getByRole("button", { name: /我是警察/ }))
    fireEvent.click(screen.getByRole("button", { name: "權威服從" }))
    expect(submit.hasAttribute("disabled")).toBe(false)
    fireEvent.click(submit)

    expect(pairs).toEqual({
      "pair-1": "time_pressure",
      "pair-2": "authority",
    })
  })
})
