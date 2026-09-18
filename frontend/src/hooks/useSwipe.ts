import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { QuickService } from "@/client"

// ── 查詢 ──────────────────────────────────────────────────────────────────────

const MOCK_SWIPE_DECK = {
  session_id: "mock_swipe_session_123",
  cards: [
    {
      id: "swipe_1",
      scenario_text: "【飆股簡訊】『專人帶盤！加入 LINE 社群，今日免費領取漲停飆股名單！』",
      sender_avatar: "📈",
      is_scam: true,
      explanation: "標榜保證獲利、飆股名單並要求加 LINE 社群均為典型投資詐欺！",
    },
    {
      id: "swipe_2",
      scenario_text: "【銀行關懷】『您的帳戶進行跨行轉帳，扣款 NT$1,200。若非本人操作請聯繫官方客服。』",
      sender_avatar: "🏦",
      is_scam: false,
      explanation: "正常的銀行轉帳通知簡訊，提供官方客服電話供查證。",
    },
    {
      id: "swipe_3",
      scenario_text: "【假網拍客服】『您昨天的訂單物流系統扣款錯誤，請點擊此連結進行雙倍退款認證。』",
      sender_avatar: "📦",
      is_scam: true,
      explanation: "網購退款絕不需要點擊未知連結輸入信用卡或金融資訊！",
    },
  ],
}

/** 取得滑卡牌組（預設 12 張） */
export function useSwipeDeck(size = 12) {
  return useQuery({
    queryKey: ["swipe", "deck", size],
    queryFn: async () => {
      try {
        return await QuickService.swipeDeck({ size })
      } catch {
        return MOCK_SWIPE_DECK as any
      }
    },
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
