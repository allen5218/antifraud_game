import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ScenarioService } from "@/client"

// ── 查詢 ──────────────────────────────────────────────────────────────────────

/** 聊天收件匣(5位固定聯絡人最新事件) */
export function useScenarioInbox() {
  return useQuery({
    queryKey: ["scenario", "inbox"],
    queryFn: () => ScenarioService.inbox(),
  })
}

/** 單場情境完整對話(斷線重連) */
export function useScenario(id: string) {
  return useQuery({
    queryKey: ["scenario", id],
    queryFn: () => ScenarioService.readScenario({ scenarioId: id }),
  })
}

// ── 變更 ──────────────────────────────────────────────────────────────────────

export interface SendMessageArgs {
  text: string
  expectedRevision?: number
  requestId?: string
}

/** 送出玩家訊息;支援 CAS revision 與冪等 request_id 控制 (T1, T4) */
export function useSendMessage(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (args: string | SendMessageArgs) => {
      const payload = typeof args === "string" ? { text: args } : args
      return ScenarioService.sendMessage({
        scenarioId: id,
        requestBody: {
          text: payload.text,
          expected_revision: payload.expectedRevision,
          request_id: payload.requestId,
        },
      })
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scenario", id] }),
  })
}

export interface JudgeArgs {
  action: "report" | "comply" | "safe_exit" | "pause"
  expectedRevision?: number
  requestId?: string
}

/** 下判斷;成功後刷新經濟(可能失財/獎勵)與所有情境查詢 (T1, T2, T4) */
export function useJudge(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (
      args: "report" | "comply" | "safe_exit" | "pause" | JudgeArgs,
    ) => {
      const payload = typeof args === "string" ? { action: args } : args
      return ScenarioService.judgeScenario({
        scenarioId: id,
        requestBody: {
          action: payload.action,
          expected_revision: payload.expectedRevision,
          request_id: payload.requestId,
        },
      })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["economy"] })
      qc.invalidateQueries({ queryKey: ["scenario"] })
    },
  })
}

export interface VerifyScenarioArgs {
  toolId: string
  expectedRevision?: number
  requestId?: string
}

/** 執行情境獨立查證工具;支援 CAS revision 與冪等 request_id (T1, T4) */
export function useVerifyScenario(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (args: string | VerifyScenarioArgs) => {
      const payload = typeof args === "string" ? { toolId: args } : args
      return ScenarioService.verifyScenario({
        scenarioId: id,
        requestBody: {
          tool_id: payload.toolId,
          expected_revision: payload.expectedRevision,
          request_id: payload.requestId,
        },
      })
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scenario", id] }),
  })
}

export interface ExecuteActionArgs {
  actionId: string
  expectedRevision?: number
  requestId?: string
}

/** 執行情境分支行動;支援 CAS revision 與冪等 request_id 控制 (G2, T4) */
export function useExecuteAction(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (args: string | ExecuteActionArgs) => {
      const payload = typeof args === "string" ? { actionId: args } : args
      return ScenarioService.performScenarioAction({
        scenarioId: id,
        requestBody: {
          action_id: payload.actionId,
          expected_revision: payload.expectedRevision,
          request_id: payload.requestId,
        },
      })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["scenario", id] })
      qc.invalidateQueries({ queryKey: ["economy"] })
    },
  })
}

export interface PauseScenarioArgs {
  expectedRevision?: number
  requestId?: string
}

/** 暫停對話;封存進度與事證，不洩露真相或變更經濟數值 (T2, T4) */
export function usePauseScenario(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (args?: PauseScenarioArgs) =>
      ScenarioService.pauseScenario({
        scenarioId: id,
        requestBody: {
          expected_revision: args?.expectedRevision,
          request_id: args?.requestId,
        },
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["scenario", id] })
      qc.invalidateQueries({ queryKey: ["scenario", "inbox"] })
    },
  })
}

export interface ResumeScenarioArgs {
  expectedRevision?: number
  requestId?: string
}

/** 繼續對話;恢復暫停中之事件，保持相同快照、事證、回合數與歷史 (T2, T4) */
export function useResumeScenario(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (args?: ResumeScenarioArgs) =>
      ScenarioService.resumeScenario({
        scenarioId: id,
        requestBody: {
          expected_revision: args?.expectedRevision,
          request_id: args?.requestId,
        },
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["scenario", id] })
      qc.invalidateQueries({ queryKey: ["scenario", "inbox"] })
    },
  })
}

export interface NewScenarioArgs {
  contactId?: string
  fraudType?: string
  storyId?: string
  requestId?: string
}

/** 開新對話 (T1, T3, T4) */
export function useNewScenario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (args: NewScenarioArgs) =>
      ScenarioService.createScenario({
        requestBody: {
          contact_id: args.contactId,
          fraud_type: args.fraudType,
          story_id: args.storyId,
          request_id: args.requestId,
        },
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scenario", "inbox"] }),
  })
}

/** 查詢 5 位聯絡人與玩家關係記憶 (C4) */
export function useContacts() {
  return useQuery({
    queryKey: ["scenario", "contacts"],
    queryFn: () => ScenarioService.listContacts(),
  })
}

/** 查詢 12 件可購買之調查/環境/社交道具清單 (C5) */
export function useShopItems() {
  return useQuery({
    queryKey: ["scenario", "items"],
    queryFn: () => ScenarioService.listShopItems(),
  })
}

export interface PurchaseItemArgs {
  itemId: string
  requestId?: string
}

/** 購買調查或社交道具 (C5, T1, T4) */
export function usePurchaseItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (args: string | PurchaseItemArgs) => {
      const payload = typeof args === "string" ? { itemId: args } : args
      return ScenarioService.purchaseItem({
        requestBody: {
          item_id: payload.itemId,
          request_id: payload.requestId,
        },
      })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["economy"] })
      qc.invalidateQueries({ queryKey: ["scenario"] })
    },
  })
}
