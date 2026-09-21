import { afterEach, describe, expect, it } from "bun:test"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import { MatchQuestion } from "./MatchQuestion"
import { TacticsQuestion } from "./TacticsQuestion"
import { VerdictQuestion } from "./VerdictQuestion"
import { VerificationQuestion } from "./VerificationQuestion"

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

describe("<VerificationQuestion />", () => {
  const item = {
    item_id: "verif-1",
    type: "verification" as const,
    fraud_type: "atm",
    title: "客服說今晚會扣款",
    narrative: "有人自稱購物平台客服，說你被誤設成會員。",
    difficulty: 1,
    question: "接下來怎麼做比較好？",
    options: [
      { key: "A", text: "自己打開官方 App 查一次" },
      { key: "B", text: "照對方給的連結操作" },
      { key: "C", text: "先把款項匯出再說" },
    ],
  }

  it("沒選之前不能送出，選完才送出所選的 key", () => {
    let submitted: string | null = null
    render(
      <VerificationQuestion
        item={item}
        index={0}
        total={5}
        disabled={false}
        onSubmit={(key) => {
          submitted = key
        }}
      />,
    )

    const submit = screen.getByRole("button", { name: "送出答案" })
    expect(submit.hasAttribute("disabled")).toBe(true)

    fireEvent.click(screen.getByRole("button", { name: /照對方給的連結操作/ }))
    expect(submit.hasAttribute("disabled")).toBe(false)

    // 送出前可以改答案。
    fireEvent.click(
      screen.getByRole("button", { name: /自己打開官方 App 查一次/ }),
    )
    fireEvent.click(submit)

    expect(submitted).toBe("A")
  })

  it("題面不洩漏哪個是正解", () => {
    render(
      <VerificationQuestion
        item={item}
        index={0}
        total={5}
        disabled={false}
        onSubmit={() => {}}
      />,
    )

    for (const option of item.options) {
      const button = screen.getByRole("button", {
        name: new RegExp(option.text),
      })
      expect(button.getAttribute("aria-pressed")).toBe("false")
    }
  })
})
