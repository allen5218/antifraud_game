import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { QuickService, type QuizAnswerRequest } from "@/client"

const MOCK_QUIZ_DECK = {
  session_id: "mock_session_123",
  items: [
    {
      item_id: "q1",
      type: "verdict" as const,
      title: "【中古車貸款陷阱】網路低利貸款",
      narrative:
        "你在 Messenger 收到融資專員簡訊，稱可幫你全額貸款買中古車。簽約後車輛被第三人逕行過戶帶走，專員稱過戶是保證金流程，要求你將剩餘款項轉入個人帳號。",
    },
    {
      item_id: "q2",
      type: "tactics" as const,
      title: "話術辨識測驗",
      narrative: "分析詐騙集團常用手法，選出包含『時間壓力』或『權威恐嚇』的選項：",
      question: "請勾選屬於詐騙紅旗話術的選項（複選）：",
      options: [
        { tag: "urgency", text: "今日下午 5 點前未匯款，將立即凍結您的所有名下資產" },
        { tag: "authority", text: "我是台北地檢署主任檢察官，現正執行線上資產監管專案" },
        { tag: "legit", text: "您好，這裡是銀行客服，提醒您本月信用卡帳單已寄出" },
        { tag: "greed", text: "加入保證獲利內部群組，每日穩賺 5% 派彩" },
      ],
    },
    {
      item_id: "q3",
      type: "match" as const,
      question: "將下列詐騙情境文字與對應的防詐核心觀念配對：",
      match_prompts: [
        { pair_id: "p1", text: "自稱檢警電話要求至 ATM 操做『解除監管』" },
        { pair_id: "p2", text: "簡訊稱『包裹配送失敗，請點擊網址更新地址』" },
      ],
      match_targets: [
        { tag: "atm_scam", label: "ATM 僅能轉帳提款，絕無解除設定功能" },
        { tag: "phishing_link", label: "不點擊不明短網址，務必回官網確認" },
      ],
    },
    {
      item_id: "q4",
      type: "verification" as const,
      title: "官方查證管道",
      narrative: "當接獲自稱健保局專員電話，告知健保卡遭人冒用開立處方箋，要求配合作案筆錄時：",
      question: "何者為最安全的處置管道？",
      options: [
        { text: "直接撥打 165 反詐騙諮詢專線或 110 報案台查證" },
        { text: "依對方指示按 9 轉接地檢署線上專員" },
        { text: "將存款全數領出交由警官保管" },
      ],
    },
    {
      item_id: "q5",
      type: "verdict" as const,
      title: "【銀行臨櫃提款關懷】",
      narrative: "你至銀行臨櫃欲提領 50 萬元修繕房屋，行員親切詢問提款用途並要求出示合約或單據。",
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
        const body = requestBody as any
        if (body.selected_tags) {
          return {
            type: "tactics",
            correct: true,
            correct_tags: ["urgency", "authority", "greed"],
            missed_tags: [],
            extra_tags: [],
            tag_details: [
              {
                tag: "urgency",
                label: "時間製造焦慮",
                suggestion: "遇到催促付款或凍結警告，請停下思考 10 分鐘。",
              },
              {
                tag: "authority",
                label: "假冒公務機關",
                suggestion: "檢警單位絕不會透過電話做筆錄或要求監管帳戶。",
              },
            ],
          } as any
        }
        if (body.pairs) {
          return {
            type: "match",
            correct: true,
            results: Object.keys(body.pairs).map((pair_id) => ({
              pair_id,
              correct: true,
              correct_tag: pair_id === "p1" ? "atm_scam" : "phishing_link",
            })),
            tag_details: [
              {
                tag: "atm_scam",
                label: "ATM 防詐常識",
                suggestion: "ATM 沒有解約、驗證身份或退款功能。",
              },
            ],
          } as any
        }
        if (body.selected_option) {
          return {
            type: "verification",
            correct: true,
            explanation:
              "【權威查證建議】遇有疑慮，應立即掛斷電話，親自撥打 165 反詐騙諮詢專線或 110 尋求求證。",
            tag_details: [],
          } as any
        }
        return {
          type: "verdict",
          correct: true,
          is_scam: true,
          red_flags: [
            { text: " 要求匯款至個人帳戶而非公司戶", tag: "payment_redirect" },
            { text: " 規避正規合約與交車程序", tag: "no_contract" },
          ],
          provenance: "司務院裁判書與 165 官方數據記錄",
          tag_details: [
            {
              tag: "payment_redirect",
              label: "非官方支付管道",
              suggestion: "切勿將車款或保證金轉匯至私人名義帳戶。",
            },
          ],
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
          total_questions: 5,
          correct_count: 5,
          best_streak: 5,
          cash_earned: 500,
          xp_earned: 250,
          weaknesses_to_improve: [],
        } as any
      }
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["economy"] }),
  })
}
