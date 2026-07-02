import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ScenarioService } from "@/client"

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
