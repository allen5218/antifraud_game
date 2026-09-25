import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { QuickService, type QuizAnswerRequest } from "@/client"
import { refreshPracticeProfileSoon } from "@/hooks/usePractice"

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

/** 單題首次作答；成功後才取得具約束力的揭曉內容。 */
export function useQuizAnswer() {
  return useMutation({
    mutationFn: (requestBody: QuizAnswerRequest) =>
      QuickService.quizAnswer({
        requestBody,
      }),
  })
}

/** 整輪結算；答案已逐題寫入，結算只帶一次性 session_id。 */
export function useQuizComplete() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (sessionId: string) =>
      QuickService.quizComplete({
        requestBody: { session_id: sessionId },
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["economy"] })
      refreshPracticeProfileSoon(qc)
    },
  })
}
