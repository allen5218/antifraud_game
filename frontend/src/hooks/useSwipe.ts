import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { QuickService } from "@/client"

// ── 查詢 ──────────────────────────────────────────────────────────────────────

/** 取得滑卡牌組（預設 12 張） */
export function useSwipeDeck(size = 12) {
  return useQuery({
    queryKey: ["swipe", "deck", size],
    queryFn: () => QuickService.swipeDeck({ size }),
    staleTime: 0,
    refetchOnWindowFocus: false,
  })
}

// ── 變更 ──────────────────────────────────────────────────────────────────────

/** 提交單張卡片答案（支援詐騙、正常與安全略過） */
export function useSwipeAnswer() {
  return useMutation({
    mutationFn: (vars: {
      sessionId: string
      cardId: string
      action: "scam" | "legit" | "skip"
    }) =>
      QuickService.swipeAnswer({
        requestBody: {
          session_id: vars.sessionId,
          card_id: vars.cardId,
          action: vars.action,
          guess_is_scam:
            vars.action === "scam"
              ? true
              : vars.action === "legit"
                ? false
                : null,
        },
      }),
  })
}

/** 提交整輪結算（同時刷新經濟狀態） */
export function useSwipeComplete() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (sessionId: string) =>
      QuickService.swipeComplete({ requestBody: { session_id: sessionId } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["economy"] }),
  })
}
