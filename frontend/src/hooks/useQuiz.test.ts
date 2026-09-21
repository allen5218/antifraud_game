import { describe, expect, it, mock } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { renderHook, waitFor } from "@testing-library/react"
import React from "react"
import { QuickService } from "@/client"
import { useQuizAnswer } from "./useQuiz"

describe("useQuiz hook", () => {
  const createWrapper = () => {
    const qc = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    return ({ children }: { children: React.ReactNode }) =>
      React.createElement(QueryClientProvider, { client: qc }, children)
  }

  it("q5 mock: 選正常時 correct=true, is_scam=false，解析不含私人帳戶/車款/保證金；選詐騙時 correct=false", async () => {
    const { result } = renderHook(() => useQuizAnswer(), {
      wrapper: createWrapper(),
    })

    // 選還好（非詐騙）
    const legitResult = await result.current.mutateAsync({
      session_id: "mock_session_test",
      item_id: "q5",
      guess_is_scam: false,
    } as any)

    expect(legitResult.type).toBe("verdict")
    expect(legitResult.correct).toBe(true)
    expect(legitResult.is_scam).toBe(false)
    const text = (legitResult as any).red_flags?.[0]?.text || ""
    expect(text).toContain("臨櫃行員")
    expect(text).not.toContain("私人帳戶")
    expect(text).not.toContain("車款")
    expect(text).not.toContain("保證金")
    expect(text).not.toContain("二手車")

    // 選有問題（認定詐騙，實際是正常）
    const scamResult = await result.current.mutateAsync({
      session_id: "mock_session_test",
      item_id: "q5",
      guess_is_scam: true,
    } as any)
    expect(scamResult.correct).toBe(false)
  })

  it("q1 仍為詐騙，且 q1/q5 解析不可互串", async () => {
    const { result } = renderHook(() => useQuizAnswer(), {
      wrapper: createWrapper(),
    })

    const q1Result = await result.current.mutateAsync({
      session_id: "mock_session_test",
      item_id: "q1",
      guess_is_scam: true,
    } as any)

    expect(q1Result.type).toBe("verdict")
    expect(q1Result.correct).toBe(true)
    expect(q1Result.is_scam).toBe(true)
    const q1Text = JSON.stringify((q1Result as any).red_flags)
    expect(q1Text).toContain("個人帳戶")
    expect(q1Text).not.toContain("臨櫃行員")
  })

  it("真實 session 的 answer API 失敗時 mutation 保持 error，不回傳 mock success", async () => {
    const originalAnswer = QuickService.quizAnswer
    QuickService.quizAnswer = mock(async () => {
      throw new Error("Backend 500 error")
    })

    try {
      const { result } = renderHook(() => useQuizAnswer(), {
        wrapper: createWrapper(),
      })

      await expect(
        result.current.mutateAsync({
          session_id: "real-session-uuid-1234",
          item_id: "q5",
          guess_is_scam: false,
        } as any),
      ).rejects.toThrow("Backend 500 error")
    } finally {
      QuickService.quizAnswer = originalAnswer
    }
  })

  it("第一輪作答後取得第二輪 deck/complete，第二輪未作答時不得沿用第一輪分數", async () => {
    const originalDeck = QuickService.quizDeck
    QuickService.quizDeck = mock(async () => {
      throw new Error("Backend offline")
    })

    try {
      const qc = new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      })
      const wrapper = ({ children }: { children: React.ReactNode }) =>
        React.createElement(QueryClientProvider, { client: qc }, children)

      const { useQuizDeck: hookDeck, useQuizComplete: hookComplete } =
        await import("./useQuiz")

      const { result: deckR1 } = renderHook(() => hookDeck(0), { wrapper })
      await waitFor(() => expect(deckR1.current.data?.session_id).toBeDefined())
      const r1SessionId = deckR1.current.data!.session_id
      expect(r1SessionId).toContain("mock_session_r0_")

      const { result: answerM } = renderHook(() => useQuizAnswer(), { wrapper })
      await answerM.current.mutateAsync({
        session_id: r1SessionId,
        item_id: "q1",
        guess_is_scam: true,
      } as any)

      const { result: completeM } = renderHook(() => hookComplete(), {
        wrapper,
      })
      const r1Summary = await completeM.current.mutateAsync(r1SessionId)
      expect(r1Summary.correct_count).toBe(1)

      // 第二輪：round 1 產生新 session
      const { result: deckR2 } = renderHook(() => hookDeck(1), { wrapper })
      await waitFor(() => expect(deckR2.current.data?.session_id).toBeDefined())
      const r2SessionId = deckR2.current.data!.session_id
      expect(r2SessionId).toContain("mock_session_r1_")
      expect(r2SessionId).not.toBe(r1SessionId)

      // 第二輪未作答直接結算：不得沿用第一輪分數，correct_count 必須為 0
      const r2Summary = await completeM.current.mutateAsync(r2SessionId)
      expect(r2Summary.correct_count).toBe(0)
    } finally {
      QuickService.quizDeck = originalDeck
    }
  })
})
