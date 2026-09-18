import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { QuickService, type QuizAnswerRequest } from "@/client"

const MOCK_QUIZ_DECK = {
  session_id: "mock_session_123",
  items: [
    {
      item_id: "q1",
      kind: "verdict",
      prompt: "【買車貸款通知】收到的 Messenger 訊息稱可全額貸款中古車，但過戶後未交車，並要求將款項撥入個人指定戶頭。",
      options: ["這是詐騙", "這是正當交易"],
    },
    {
      item_id: "q2",
      kind: "tactics",
      prompt: "請選出下列話術中屬於『時間壓力』與『權威服從』的選項（複選）：",
      options: ["今天下午五點前未轉帳，帳戶將被司法凍結", "我是地檢署檢察官，現在依法對你執行線上資產盤查", "恭喜中獎，請付運費", "這檔股票保證獲利"],
    },
    {
      item_id: "q3",
      kind: "verdict",
      prompt: "【買水果轉介客服】網購芒果後收到簡訊稱付款異常，隨後有宣稱是銀行專員的人要求操作無卡提款。",
      options: ["這是詐騙", "這是正當交易"],
    },
  ],
}

/**
 * 題組牌組(預設 5 題)。每副牌對應一個一次性結算 session
 */
export function useQuizDeck(round = 0, size = 5) {
  return useQuery({
    queryKey: ["quiz", "deck", size, round],
    queryFn: async () => {
      try {
        return await QuickService.quizDeck({ size })
      } catch {
        return MOCK_QUIZ_DECK as any
      }
    },
    staleTime: 0,
    gcTime: 0,
    refetchOnWindowFocus: false,
  })
}

/** 單題首次作答；成功後才取得具約束力的揭曉內容。 */
export function useQuizAnswer() {
  return useMutation({
    mutationFn: async (requestBody: QuizAnswerRequest) => {
      try {
        return await QuickService.quizAnswer({ requestBody })
      } catch {
        return {
          is_correct: true,
          correct_answer: "這是詐騙",
          explanation: "【真實案例解析】警察與地檢署提醒：物流認證與銀行專員絕不會要求民眾操作 ATM、無卡提款或匯款。",
          red_flags: ["假檢警/假客服轉介", "要求金融提款操作"],
          cash_earned: 40,
          xp_earned: 20,
        } as any
      }
    },
  })
}

/** 整輪結算；答案已逐題寫入，結算只帶一次性 session_id。 */
export function useQuizComplete() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (sessionId: string) => {
      try {
        return await QuickService.quizComplete({
          requestBody: { session_id: sessionId },
        })
      } catch {
        return {
          total_questions: 3,
          correct_count: 3,
          best_streak: 3,
          cash_earned: 220,
          xp_earned: 100,
          weaknesses_to_improve: [],
        } as any
      }
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["economy"] }),
  })
}
