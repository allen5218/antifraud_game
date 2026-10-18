import { afterEach, describe, expect, it, mock, spyOn } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react"
import type { ExamStatus } from "@/client"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { ExamService } from "@/client/sdk.gen"
import { renderWithRouter } from "@/test/renderWithRouter"

// 第一次送出答案時模擬「回應遺失」,之後成功。hold 時先不回應,模擬還在送出中。
const sent: boolean[] = []
let failNext = true
let hold = false
let examLock = false
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

const card = (id: string, scenario: string) => ({
  id,
  scenario,
  source_label: "簡訊",
  fraud_type: "shopping",
  difficulty: 1,
})
const ONE_CARD = [card("c1", "有人傳訊息說包裹卡在海關")]
let deckCards = ONE_CARD
let answerResult: typeof ok = ok
let completeCalls = 0

// mock.module 必須在 import 元件之前呼叫
mock.module("@/hooks/useSwipe", () => ({
  useSwipeDeck: () => ({
    isLoading: false,
    data: { session_id: "s1", cards: deckCards },
  }),
  useSwipeAnswer: () => ({
    isPending: false,
    mutate: (vars: { guessIsScam: boolean }, opts: Callbacks) => {
      sent.push(vars.guessIsScam)
      if (hold) {
        pending = opts
        return
      }
      if (examLock) {
        examLock = false
        opts.onError({
          status: 400,
          body: { detail: { code: "exam_in_progress" } },
        } as Error)
        opts.onSettled()
        return
      }
      if (failNext) {
        failNext = false
        opts.onError(new Error("network"))
      } else {
        opts.onSuccess(answerResult)
      }
      opts.onSettled()
    },
  }),
  useSwipeComplete: () => ({
    mutate: () => {
      completeCalls += 1
    },
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
  examLock = false
  pending = null
  deckCards = ONE_CARD
  answerResult = ok
  completeCalls = 0
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
  // 2026-10-18 正式環境：第三次答錯就直接結算，最後那張的解說沒顯示
  it("警覺值用完時先給看最後一張的解說，按了才結算", () => {
    failNext = false
    deckCards = [
      card("c1", "第一則"),
      card("c2", "第二則"),
      card("c3", "第三則"),
    ]
    answerResult = { ...ok, correct: false, explanation: "這張是正常的通知" }
    renderDeck()
    for (let i = 0; i < 2; i++) {
      fireEvent.click(screen.getByRole("button", { name: /詐騙/ }))
      fireEvent.click(screen.getByRole("button", { name: "下一張" }))
    }
    fireEvent.click(screen.getByRole("button", { name: /詐騙/ }))

    expect(screen.getByText("這張是正常的通知")).toBeTruthy()
    expect(completeCalls).toBe(0)
    fireEvent.click(screen.getByRole("button", { name: "看結算" }))
    expect(completeCalls).toBe(1)
  })

  it("resends the original answer after a lost response", () => {
    renderDeck()
    fireEvent.click(screen.getByRole("button", { name: /詐騙/ }))
    // 失敗後不能換答案:卡片的兩個按鈕收起來,只剩「再送一次」
    expect(screen.getByRole("alert").textContent).toContain("沒有送出成功")
    expect(screen.queryByRole("button", { name: /正常/ })).toBeNull()

    fireEvent.click(screen.getByRole("button", { name: "再送一次" }))
    expect(sent).toEqual([true, true])
    // 只有一張卡，答完就是最後一張
    expect(screen.getByRole("button", { name: "看結算" })).toBeTruthy()
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

  it("作答被檢測鎖擋下時整頁換成繼續檢測，不當成這一局失效", async () => {
    examLock = true
    const status: ExamStatus = {
      active_attempt_id: "attempt-1",
      can_start: false,
      block_reason: "exam_in_progress",
      gate: null,
      daily_used: 0,
      daily_limit: 3,
      badges: [],
    }
    spyOn(ExamService, "readStatus").mockImplementation(
      () => new CancelablePromise((resolve) => resolve(status)),
    )
    await renderWithRouter(
      <QueryClientProvider
        client={
          new QueryClient({ defaultOptions: { queries: { retry: false } } })
        }
      >
        <SwipeDeck />
      </QueryClientProvider>,
    )
    fireEvent.click(screen.getByRole("button", { name: /詐騙/ }))
    expect((await screen.findByRole("alert")).textContent).toContain(
      "先完成檢測再回來練習",
    )
    expect(screen.queryByText("這一局已經失效了。")).toBeNull()
    expect(screen.queryByText("剛才的答案沒有送出成功。")).toBeNull()
    await waitFor(() =>
      expect(
        screen.getByRole("link", { name: "繼續檢測" }).getAttribute("href"),
      ).toBe("/exam/attempt-1"),
    )
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
