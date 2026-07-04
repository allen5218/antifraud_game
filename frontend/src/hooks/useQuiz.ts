import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { QuickService } from "@/client"

/**
 * 題組牌組(預設 5 題)。每副牌對應一個一次性結算 session,故 query key 帶
 * `round`——重玩時遞增 round 取新牌,避免重用已結算的舊 deck/session_id;
 * `gcTime: 0` 確保元件卸載後不留舊 deck 於快取,remount 時必重新發牌。
 */
export function useQuizDeck(round = 0, size = 5) {
  return useQuery({
    queryKey: ["quiz", "deck", size, round],
    queryFn: () => QuickService.quizDeck({ size }),
    staleTime: 0,
    gcTime: 0,
    refetchOnWindowFocus: false,
  })
}

/** 單題判定(揭曉紅旗與溯源) */
export function useQuizAnswer() {
  return useMutation({
    mutationFn: (vars: { caseId: number; guessIsScam: boolean }) =>
      QuickService.quizAnswer({
        requestBody: { case_id: vars.caseId, guess_is_scam: vars.guessIsScam },
      }),
  })
}

/** 整輪結算(刷新經濟);需帶發牌時的 session_id 防跨請求重放刷獎 */
export function useQuizComplete() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (vars: {
      sessionId: string
      answers: { case_id: number; guess_is_scam: boolean }[]
    }) =>
      QuickService.quizComplete({
        requestBody: { session_id: vars.sessionId, answers: vars.answers },
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["economy"] }),
  })
}
