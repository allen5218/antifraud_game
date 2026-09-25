import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { QuickService } from "@/client"
import { refreshPracticeProfileSoon } from "@/hooks/usePractice"

// ── 查詢 ──────────────────────────────────────────────────────────────────────

/**
 * 取得滑卡牌組（預設 12 張）與這一局的 session_id。
 * 作答與結算都要帶 session_id:結算只認這一局發的卡、每張卡第一次的作答。
 * query key 帶 `round`:再來一輪時遞增,拿到照最新練習重點發的新牌,
 * 而不是先顯示上一輪的牌再被換掉。
 * 一輪只發一次牌:每次發牌都是新的一局,網路重連或切回視窗時自動重抓的話,
 * 玩到一半會換成另一局,先前的作答留在舊局、結算對不上。
 * 進頁面(gcTime 0 不留快取)或按「再來一輪」才會發新牌。
 */
export function useSwipeDeck(size = 12, round = 0) {
  return useQuery({
    queryKey: ["swipe", "deck", size, round],
    queryFn: () => QuickService.swipeDeck({ size }),
    staleTime: Number.POSITIVE_INFINITY,
    gcTime: 0,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  })
}

// ── 變更 ──────────────────────────────────────────────────────────────────────

/** 提交單張卡片答案（伺服器只記第一次） */
export function useSwipeAnswer() {
  return useMutation({
    mutationFn: (vars: {
      sessionId: string
      cardId: string
      guessIsScam: boolean
    }) =>
      QuickService.swipeAnswer({
        requestBody: {
          session_id: vars.sessionId,
          card_id: vars.cardId,
          guess_is_scam: vars.guessIsScam,
        },
      }),
  })
}

/** 提交整輪結算（答案已逐張存在伺服器端，只帶 session_id；同時刷新經濟狀態） */
export function useSwipeComplete() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (sessionId: string) =>
      QuickService.swipeComplete({ requestBody: { session_id: sessionId } }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["economy"] })
      refreshPracticeProfileSoon(qc)
    },
  })
}
