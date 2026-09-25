import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { QuickService } from "@/client"
import { refreshPracticeProfileSoon } from "@/hooks/usePractice"

// ── 查詢 ──────────────────────────────────────────────────────────────────────

/**
 * 取得滑卡牌組（預設 12 張）。
 * query key 帶 `round`:再來一輪時遞增,拿到照最新練習重點發的新牌,
 * 而不是先顯示上一輪的牌再被換掉。
 */
export function useSwipeDeck(size = 12, round = 0) {
  return useQuery({
    queryKey: ["swipe", "deck", size, round],
    queryFn: () => QuickService.swipeDeck({ size }),
    staleTime: 0,
    gcTime: 0,
    refetchOnWindowFocus: false,
  })
}

// ── 變更 ──────────────────────────────────────────────────────────────────────

/** 提交單張卡片答案 */
export function useSwipeAnswer() {
  return useMutation({
    mutationFn: (vars: { cardId: string; guessIsScam: boolean }) =>
      QuickService.swipeAnswer({
        requestBody: { card_id: vars.cardId, guess_is_scam: vars.guessIsScam },
      }),
  })
}

/** 提交整輪結算（同時刷新經濟狀態） */
export function useSwipeComplete() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (answers: { card_id: string; guess_is_scam: boolean }[]) =>
      QuickService.swipeComplete({ requestBody: { answers } }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["economy"] })
      refreshPracticeProfileSoon(qc)
    },
  })
}
