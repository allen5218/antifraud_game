import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { type ApiError, ScenarioService } from "@/client"
import { refreshPracticeProfileSoon } from "@/hooks/usePractice"
import { fraudTypeLabel } from "@/lib/fraudTypes"

// ── 查詢 ──────────────────────────────────────────────────────────────────────

/** 情境收件匣(每類最新一場) */
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
    mutationFn: (action: "report" | "comply") =>
      ScenarioService.judgeScenario({
        scenarioId: id,
        requestBody: { action },
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["economy"] })
      qc.invalidateQueries({ queryKey: ["scenario"] })
      refreshPracticeProfileSoon(qc)
    },
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

/** 開新對話失敗時給玩家看的一句話(後端回 400 {code, limit})。 */
export function newScenarioError(err: unknown, fraudType: string): string {
  const body = (err as ApiError | undefined)?.body as
    | { detail?: { code?: string; limit?: number } }
    | undefined
  const code = body?.detail?.code
  const label = fraudTypeLabel(fraudType)
  if (code === "daily_limit_reached") {
    const limit = body?.detail?.limit
    return limit
      ? `今天「${label}」已經練了 ${limit} 場，明天再來。`
      : `今天「${label}」已經練滿了，明天再來。`
  }
  if (code === "active_exists") {
    return `「${label}」還有一場沒聊完，先回聯絡人把它聊完。`
  }
  return "開不了新對話，請稍後再試。"
}
