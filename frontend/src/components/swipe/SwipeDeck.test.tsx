import { afterEach, describe, expect, it, mock } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react"

// 第一次送出答案時模擬「回應遺失」,之後成功。hold 時先不回應,模擬還在送出中。
const sent: boolean[] = []
let failNext = true
let hold = false
type Callbacks = {
  onError: (e: Error) => void
  onSuccess: (r: unknown) => void
  onSettled: () => void
}
let pending: Callbacks | null = null
const ok = {
  correct: true,
  is_scam: true,
  explanation: "要你點連結補繳稅費，是常見的手法",
  weakness_tags: [],
  tag_details: [],
}

// mock.module 必須在 import 元件之前呼叫
mock.module("@/hooks/useSwipe", () => ({
  useSwipeDeck: () => ({
    isLoading: false,
    data: {
      session_id: "s1",
      cards: [
        {
          id: "c1",
          scenario: "有人傳訊息說包裹卡在海關",
          source_label: "簡訊",
          fraud_type: "shopping",
          difficulty: 1,
        },
      ],
    },
  }),
  useSwipeAnswer: () => ({
    isPending: false,
    mutate: (vars: { guessIsScam: boolean }, opts: Callbacks) => {
      sent.push(vars.guessIsScam)
      if (hold) {
        pending = opts
        return
      }
      if (failNext) {
        failNext = false
        opts.onError(new Error("network"))
      } else {
        opts.onSuccess(ok)
      }
      opts.onSettled()
    },
  }),
  useSwipeComplete: () => ({
    mutate: () => {},
    reset: () => {},
    isPending: false,
    isError: false,
    data: undefined,
  }),
}))

import { SwipeDeck } from "./SwipeDeck"

afterEach(() => {
  cleanup()
  sent.length = 0
  failNext = true
  hold = false
  pending = null
})

const renderDeck = () =>
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <SwipeDeck />
    </QueryClientProvider>,
  )

describe("<SwipeDeck />", () => {
  it("resends the original answer after a lost response", () => {
    renderDeck()
    fireEvent.click(screen.getByRole("button", { name: /詐騙/ }))
    // 失敗後不能換答案:卡片的兩個按鈕收起來,只剩「再送一次」
    expect(screen.getByRole("alert").textContent).toContain("沒有送出成功")
    expect(screen.queryByRole("button", { name: /正常/ })).toBeNull()

    fireEvent.click(screen.getByRole("button", { name: "再送一次" }))
    expect(sent).toEqual([true, true])
    expect(screen.getByRole("button", { name: "下一張" })).toBeTruthy()
  })

  it("ignores a second, different answer while the first is still sending", () => {
    failNext = false
    hold = true
    renderDeck()
    fireEvent.click(screen.getByRole("button", { name: /詐騙/ }))
    fireEvent.click(screen.getByRole("button", { name: /正常/ }))
    expect(sent).toEqual([true])
    act(() => {
      pending?.onSuccess(ok)
      pending?.onSettled()
    })
  })

  it("offers a new deal when the round can no longer be answered", () => {
    failNext = false
    hold = true
    renderDeck()
    fireEvent.click(screen.getByRole("button", { name: /詐騙/ }))
    act(() => {
      pending?.onError(Object.assign(new Error("gone"), { status: 400 }))
      pending?.onSettled()
    })
    expect(screen.getByText("這一局已經失效了。")).toBeTruthy()
    expect(screen.getByRole("button", { name: "重新發牌" })).toBeTruthy()
  })
})
