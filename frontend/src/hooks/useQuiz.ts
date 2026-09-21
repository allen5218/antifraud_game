import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { QuickService, type QuizAnswerRequest } from "@/client"

const MOCK_QUIZ_DECK_ITEMS = [
  {
    item_id: "q1",
    type: "verdict" as const,
    title: "網路二手車低利購車貸款",
    narrative:
      "你在 Messenger 收到融資專員簡訊，稱可幫你全額貸款買中古車。簽約後車輛被第三人逕行過戶帶走，專員稱過戶是保證金流程，要求你將剩餘款項轉入個人帳號。",
  },
  {
    item_id: "q2",
    type: "tactics" as const,
    title: "這些話哪裡怪？",
    narrative: "看看下面幾句話，選出讓你覺得有壓力或不對勁的地方。",
    question: "你覺得他用了哪些招？（可複選）",
    options: [
      {
        tag: "time_pressure",
        label: "今日下午 5 點前未匯款，將立即凍結您的所有名下資產",
        text: "今日下午 5 點前未匯款，將立即凍結您的所有名下資產",
      },
      {
        tag: "authority",
        label: "我是台北地檢署主任檢察官，現正執行線上資產監管專案",
        text: "我是台北地檢署主任檢察官，現正執行線上資產監管專案",
      },
      {
        tag: "trust_building",
        label: "您好，這裡是銀行客服，提醒您本月信用卡帳單已寄出",
        text: "您好，這裡是銀行客服，提醒您本月信用卡帳單已寄出",
      },
      {
        tag: "greed",
        label: "加入保證獲利內部群組，每日穩賺 5% 派彩",
        text: "加入保證獲利內部群組，每日穩賺 5% 派彩",
      },
    ],
  },
  {
    item_id: "q3",
    type: "match" as const,
    question: "把每句話和它的問題配在一起",
    match_prompts: [
      { pair_id: "p1", text: "自稱檢警電話要求至 ATM 操作『解除監管』" },
      { pair_id: "p2", text: "簡訊稱『包裹配送失敗，請點擊網址更新地址』" },
    ],
    match_targets: [
      { tag: "atm_scam", label: "ATM 不能解除設定" },
      { tag: "phishing_link", label: "陌生網址不要點" },
    ],
  },
  {
    item_id: "q4",
    type: "verification" as const,
    title: "有人自稱健保局打來",
    narrative: "他說你的健保卡被冒用，要你在線上配合做筆錄。",
    question: "你認為怎麼做比較好？",
    options: [
      { key: "a", text: "先掛斷，自己打 165 或 110 查證" },
      { key: "b", text: "照他說的按 9，轉接地檢署" },
      { key: "c", text: "把存款領出來交給警官保管" },
    ],
  },
  {
    item_id: "q5",
    type: "verdict" as const,
    title: "銀行臨櫃房屋修繕款提領",
    narrative:
      "你至銀行臨櫃欲提領 50 萬元修繕房屋，行員親切詢問提款用途並要求出示合約或單據。",
  },
]

export const MOCK_QUIZ_DECK = {
  session_id: "mock_session_123",
  items: MOCK_QUIZ_DECK_ITEMS,
}

const mockSessionAnswers: Record<
  string,
  Record<string, { correct: boolean; item_id: string }>
> = {}

export function createMockSessionId(round = 0): string {
  const randomSuffix =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : Math.random().toString(36).substring(2, 9)
  return `mock_session_r${round}_${randomSuffix}`
}

export function createMockDeck(round = 0) {
  const sessionId = createMockSessionId(round)
  mockSessionAnswers[sessionId] = {}
  return {
    session_id: sessionId,
    items: MOCK_QUIZ_DECK_ITEMS,
  }
}

const MOCK_ITEM_HANDLERS: Record<string, (body: any) => any> = {
  q1: (body) => {
    const guessIsScam = body.guess_is_scam
    const correct = guessIsScam === true
    return {
      type: "verdict",
      correct,
      is_scam: true,
      red_flags: [
        {
          text: "要求匯款至個人帳戶而非融資或車行公司戶",
          tag: "payment_redirect",
        },
        { text: "規避正規合約與交車程序，未交車即先過戶", tag: "no_contract" },
      ],
      provenance: "司法院裁判書與 165 官方數據記錄",
      tag_details: [
        {
          tag: "payment_redirect",
          label: "非官方支付管道",
          suggestion: "切勿將車款或保證金轉匯至私人名義帳戶。",
        },
      ],
    }
  },
  q2: (body) => {
    const selected = body.selected_tags || []
    const correctTags = ["time_pressure", "authority", "greed"]
    const missed = correctTags.filter((t: string) => !selected.includes(t))
    const extra = selected.filter((t: string) => !correctTags.includes(t))
    const correct = missed.length === 0 && extra.length === 0
    return {
      type: "tactics",
      correct,
      correct_tags: correctTags,
      missed_tags: missed,
      extra_tags: extra,
      tag_details: [
        {
          tag: "time_pressure",
          label: "時間製造焦慮",
          suggestion: "遇到催促付款或凍結警告，請停下思考 10 分鐘。",
        },
        {
          tag: "authority",
          label: "假冒公務機關",
          suggestion: "檢警單位絕不會透過電話做筆錄或要求監管帳戶。",
        },
      ],
    }
  },
  q3: (body) => {
    const pairs = body.pairs || {}
    const p1Correct = pairs.p1 === "atm_scam"
    const p2Correct = pairs.p2 === "phishing_link"
    const correct = p1Correct && p2Correct
    return {
      type: "match",
      correct,
      results: [
        { pair_id: "p1", correct: p1Correct, correct_tag: "atm_scam" },
        { pair_id: "p2", correct: p2Correct, correct_tag: "phishing_link" },
      ],
      tag_details: [
        {
          tag: "atm_scam",
          label: "ATM 防詐常識",
          suggestion: "ATM 沒有解約、驗證身份或退款功能。",
        },
      ],
    }
  },
  q4: (body) => {
    const correct = body.selected_option === "a"
    return {
      type: "verification",
      correct,
      explanation:
        "先掛斷，再自己打 165 或 110 查證。公務機關不會在電話中要求線上製作筆錄或轉接地檢署。",
      tag_details: [],
    }
  },
  q5: (body) => {
    const guessIsScam = body.guess_is_scam
    const correct = guessIsScam === false
    return {
      type: "verdict",
      correct,
      is_scam: false,
      red_flags: [
        {
          tag: null,
          text: "臨櫃行員確認大額提款用途與單據，是常見的風險控管；仍可確認行員身分及文件用途。",
        },
      ],
      provenance: "金融機構臨櫃關懷提問防詐指引",
      tag_details: [],
    }
  },
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
        return createMockDeck(round) as any
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
      if (requestBody.session_id.startsWith("mock_")) {
        const handler = MOCK_ITEM_HANDLERS[requestBody.item_id]
        if (!handler) {
          throw new Error(`未知題目 ID: ${requestBody.item_id}`)
        }
        const response = handler(requestBody)
        if (!mockSessionAnswers[requestBody.session_id]) {
          mockSessionAnswers[requestBody.session_id] = {}
        }
        mockSessionAnswers[requestBody.session_id][requestBody.item_id] = {
          correct: response.correct,
          item_id: requestBody.item_id,
        }
        return response
      }
      return await QuickService.quizAnswer({ requestBody })
    },
  })
}

/** 整輪結算；答案已逐題寫入，結算只帶一次性 session_id。 */
export function useQuizComplete() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (sessionId: string) => {
      if (sessionId.startsWith("mock_")) {
        const answers = mockSessionAnswers[sessionId] || {}
        const total = MOCK_QUIZ_DECK_ITEMS.length
        let correctCount = 0
        let streak = 0
        let bestStreak = 0
        for (const item of MOCK_QUIZ_DECK_ITEMS) {
          const ans = answers[item.item_id]
          if (ans?.correct) {
            correctCount++
            streak++
            bestStreak = Math.max(bestStreak, streak)
          } else {
            streak = 0
          }
        }
        // 清理該 session，避免記憶體洩漏
        delete mockSessionAnswers[sessionId]
        return {
          total,
          correct_count: correctCount,
          best_streak: bestStreak,
          cash_earned: correctCount * 200,
          xp_earned: correctCount * 50,
          weakness_summary: [],
          signal_detection: {
            d_prime: 2.5,
            criterion: 0.0,
            diagnostic_label: "作答節奏平穩",
            bias_type: "rational",
          },
          calibration: {
            brier_score: 0.05,
            overconfidence_index: 0.0,
            mean_confidence: 0.8,
            mean_accuracy: total > 0 ? correctCount / total : 0,
            diagnosis: "判斷掌握度均衡",
            high_confidence_errors: 0,
            advice: "作答節奏與掌握度均衡，繼續保持。",
          },
        } as any
      }
      return await QuickService.quizComplete({
        requestBody: { session_id: sessionId },
      })
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["economy"] }),
  })
}
