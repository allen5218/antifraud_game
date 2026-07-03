import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { QuickService } from "@/client"

/** 題組牌組(預設 5 題) */
export function useQuizDeck(size = 5) {
  return useQuery({
    queryKey: ["quiz", "deck", size],
    queryFn: () => QuickService.quizDeck({ size }),
    staleTime: 0,
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

/** 整輪結算(刷新經濟) */
export function useQuizComplete() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (answers: { case_id: number; guess_is_scam: boolean }[]) =>
      QuickService.quizComplete({ requestBody: { answers } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["economy"] }),
  })
}
