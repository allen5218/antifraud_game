import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ScenarioService } from "@/client"

// ── 查詢 ──────────────────────────────────────────────────────────────────────

const MOCK_INBOX = [
  {
    id: "sc_01",
    fraud_type: "investment",
    display_name: "金牌投資顧問 - 陳經理",
    avatar: "📈",
    last_message: "這期飆股社團限定名額只剩最後 2 位，保證月化 30% 報酬！",
    status: "active",
    player_turns: 2,
    max_turns: 10,
    fraud_type_label: "投資詐欺",
  },
  {
    id: "sc_02",
    fraud_type: "fake-sale",
    display_name: "網購平台客服 - 小美",
    avatar: "🛍️",
    last_message: "您好，您昨天的買芒果訂單付款設定異常，需要幫您線上核對...",
    status: "active",
    player_turns: 1,
    max_turns: 10,
    fraud_type_label: "假網路拍賣",
  },
  {
    id: "sc_03",
    fraud_type: "romance",
    display_name: "網海情緣 - 莉莉",
    avatar: "🌸",
    last_message: "親愛的，我寄給你的海外結婚禮物被海關查扣了，可以先幫我付關稅嗎...",
    status: "active",
    player_turns: 3,
    max_turns: 10,
    fraud_type_label: "假愛情交友",
  },
]

const MOCK_SCENARIO_DETAIL = {
  id: "sc_01",
  fraud_type: "investment",
  display_name: "金牌投資顧問 - 陳經理",
  avatar: "📈",
  status: "active",
  player_turns: 2,
  max_turns: 10,
  history: [
    { role: "npc", content: "您好！看到您對理財有興趣，我們團隊有獨家的飆股分析軟體，每日提供保證獲利名單。" },
    { role: "player", content: "請問這個有合法金管會核准執照嗎？" },
    { role: "npc", content: "我們是海外私募團隊，不需要台灣執照！名額只剩最後 2 位，請盡快匯款至指定特別戶頭。", decision_point: "要立即匯款 NT$50,000 加入投資專案嗎？" },
  ],
  available_tools: [
    { id: "check_license", label: "查詢金管會合法投顧名單" },
    { id: "check_account", label: "比對受款戶名是否為個人人頭帳戶" },
  ],
  unlocked_evidence: [
    "經過查詢：金管會專區無該『海外私募團隊』登記紀錄！",
  ],
}

/** 情境收件匣(每類最新一場) */
export function useScenarioInbox() {
  return useQuery({
    queryKey: ["scenario", "inbox"],
    queryFn: async () => {
      try {
        return await ScenarioService.inbox()
      } catch {
        return MOCK_INBOX as any
      }
    },
  })
}

/** 單場情境完整對話(斷線重連) */
export function useScenario(id: string) {
  return useQuery({
    queryKey: ["scenario", id],
    queryFn: async () => {
      try {
        return await ScenarioService.readScenario({ scenarioId: id })
      } catch {
        return MOCK_SCENARIO_DETAIL as any
      }
    },
  })
}

// ── 變更 ──────────────────────────────────────────────────────────────────────

/** 送出玩家訊息;成功後刷新該場對話 */
export function useSendMessage(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (text: string) =>
      ScenarioService.sendMessage({ scenarioId: id, requestBody: { text } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scenario", id] }),
  })
}

/** 下判斷;成功後刷新經濟(可能失財/獎勵)與所有情境查詢 */
export function useJudge(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (action: "report" | "comply" | "safe_exit") =>
      ScenarioService.judgeScenario({
        scenarioId: id,
        requestBody: { action },
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["economy"] })
      qc.invalidateQueries({ queryKey: ["scenario"] })
    },
  })
}

/** 執行情境獨立查證工具 */
export function useVerifyScenario(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (toolId: string) =>
      ScenarioService.verifyScenario({
        scenarioId: id,
        requestBody: { tool_id: toolId },
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scenario", id] }),
  })
}

/** 對 completed 類型開新一場 */
export function useNewScenario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (fraudType: string) =>
      ScenarioService.createScenario({
        requestBody: { fraud_type: fraudType },
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scenario", "inbox"] }),
  })
}
