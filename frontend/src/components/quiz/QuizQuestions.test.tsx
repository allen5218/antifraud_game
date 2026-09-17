import { afterEach, describe, expect, it } from "bun:test"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import { MatchQuestion } from "./MatchQuestion"
import { TacticsQuestion } from "./TacticsQuestion"
import { VerdictQuestion } from "./VerdictQuestion"

afterEach(cleanup)

describe("quiz 題型元件", () => {
  it("verdict 送出玩家選擇", () => {
    let answer: boolean | undefined
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
        onSubmit={(guessIsScam) => {
          answer = guessIsScam
        }}
      />,
    )

    fireEvent.click(screen.getByRole("button", { name: /這是詐騙/ }))

    expect(answer).toBe(true)
  })

  it("tactics 可改複選並回報已選數量", () => {
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
    fireEvent.click(screen.getByRole("button", { name: "送出答案" }))

    expect(selected).toEqual(["authority"])
  })

  it("match 點選配對、可取消，且全部完成才能送出", () => {
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

    const submit = screen.getByRole("button", { name: "送出答案" })
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
