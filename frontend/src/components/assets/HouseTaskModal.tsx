import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { EconomyService } from "@/client"
import { Button } from "@/components/ui/button"

interface HouseTaskModalProps {
  open: boolean
  onClose: () => void
  onSuccessBuy?: () => void
}

export function HouseTaskModal({
  open,
  onClose,
  onSuccessBuy,
}: HouseTaskModalProps) {
  const qc = useQueryClient()
  const [resolveFeedback, setResolveFeedback] = useState<{
    passed: boolean
    message: string
  } | null>(null)

  const { data: task, isLoading } = useQuery({
    queryKey: ["economy", "house-task"],
    queryFn: async () => {
      try {
        return await EconomyService.getHouseTask()
      } catch {
        return {
          scenario:
            "賣方要求將首期房屋保證金 10 萬元直接轉入私人指定賬號，並宣稱可省下代書規費與履約保證費用。",
          is_passed: false,
          steps: [
            {
              step_id: "s1",
              name: "調閱建物謄本與實價登錄",
              description: "核對房屋所有人與標的物抵押狀況",
              is_done: true,
              evidence: "謄本顯示賣方名下無查封，但有第二順位高利抵押權。",
            },
            {
              step_id: "s2",
              name: "驗證銀行履約保證專戶",
              description: "確認匯款帳戶是否為銀行獨立託管專戶",
              is_done: true,
              evidence: "賣方提供的帳戶為個人戶名，非銀行履約託管帳戶！",
            },
          ],
        } as any
      }
    },
    enabled: open,
  })

  const verifyM = useMutation({
    mutationFn: (stepId: string) =>
      EconomyService.verifyHouseTask({ requestBody: { step_id: stepId } }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["economy", "house-task"] })
    },
  })

  const resolveM = useMutation({
    mutationFn: (choice: "official_escrow" | "private_wire") =>
      EconomyService.resolveHouseTaskEndpoint({ requestBody: { choice } }),
    onSuccess: (res) => {
      setResolveFeedback({ passed: res.is_passed, message: res.message })
      qc.invalidateQueries({ queryKey: ["economy"] })
      if (res.is_passed && onSuccessBuy) {
        onSuccessBuy()
      }
    },
  })

  if (!open) return null

  const completedStepsCount =
    task?.steps.filter((s: { is_done: boolean }) => s.is_done).length ?? 0
  const canResolve = completedStepsCount >= 2

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 sm:items-center sm:p-4">
      <div className="flex max-h-[90vh] w-full max-w-lg flex-col rounded-t-2xl bg-background p-4 sm:rounded-2xl">
        <div className="flex items-center justify-between border-b pb-3">
          <div>
            <h3 className="text-base font-bold">首次購屋交易查證挑戰</h3>
            <p className="text-xs text-muted-foreground">
              高額不動產交易具高詐騙風險，需先完成至少兩項客觀查證
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-1 text-muted-foreground hover:bg-muted"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-3 space-y-4 text-xs">
          {isLoading || !task ? (
            <div className="py-8 text-center text-muted-foreground">
              載入購屋任務中…
            </div>
          ) : (
            <>
              {/* 情境描述 */}
              <div className="rounded-xl bg-amber-500/10 p-3 leading-relaxed text-amber-900 dark:text-amber-200">
                <p className="font-bold">購屋情境：</p>
                <p className="mt-1">{task.scenario}</p>
              </div>

              {/* 查證步驟清單 */}
              <div className="space-y-2">
                <div className="flex items-center justify-between font-bold">
                  <span>
                    查證步驟清單（已完成 {completedStepsCount} /{" "}
                    {task.steps.length}）
                  </span>
                  {canResolve && (
                    <span className="text-[11px] text-green-600">
                      已滿足決策門檻
                    </span>
                  )}
                </div>

                <div className="grid gap-2">
                  {task.steps.map(
                    (step: {
                      step_id: string
                      is_done: boolean
                      name: string
                      description: string
                      evidence?: string
                    }) => (
                      <div
                        key={step.step_id}
                        className={`rounded-xl border p-3 ${
                          step.is_done
                            ? "border-green-300 bg-green-50/40 dark:border-green-950 dark:bg-green-950/20"
                            : "border-border bg-card"
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-bold">{step.name}</span>
                          {step.is_done ? (
                            <span className="text-[11px] font-bold text-green-600">
                              已查核
                            </span>
                          ) : (
                            <Button
                              size="sm"
                              disabled={verifyM.isPending}
                              onClick={() => verifyM.mutate(step.step_id)}
                              className="h-7 text-[11px]"
                            >
                              調閱查證
                            </Button>
                          )}
                        </div>
                        <p className="mt-1 text-muted-foreground">
                          {step.description}
                        </p>
                        {step.evidence && (
                          <div className="mt-2 rounded-lg bg-background/80 p-2 font-medium text-foreground">
                            查證客觀事實：{step.evidence}
                          </div>
                        )}
                      </div>
                    ),
                  )}
                </div>
              </div>

              {/* 最終決策 */}
              <div className="space-y-2 border-t pt-3">
                <h4 className="font-bold">下一步交易處置決策</h4>
                {!canResolve && (
                  <p className="text-muted-foreground">
                    請先執行上方至少兩項查證動作，調閱真實產權與金流紀錄。
                  </p>
                )}

                {resolveFeedback && (
                  <div
                    className={`rounded-xl p-3 ${
                      resolveFeedback.passed
                        ? "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-200"
                        : "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200"
                    }`}
                  >
                    <p className="font-bold">
                      {resolveFeedback.passed ? "✓ 查證成功！" : "✗ 決策警訊！"}
                    </p>
                    <p className="mt-1 leading-relaxed">
                      {resolveFeedback.message}
                    </p>
                  </div>
                )}

                <div className="grid grid-cols-1 gap-2 pt-1 sm:grid-cols-2">
                  <Button
                    disabled={
                      !canResolve || resolveM.isPending || task.is_passed
                    }
                    onClick={() => resolveM.mutate("official_escrow")}
                    className="w-full text-xs font-bold"
                  >
                    堅持銀行履約保證專戶（官方渠道）
                  </Button>
                  <Button
                    variant="outline"
                    disabled={
                      !canResolve || resolveM.isPending || task.is_passed
                    }
                    onClick={() => resolveM.mutate("private_wire")}
                    className="w-full border-red-200 text-xs font-bold text-red-600 hover:bg-red-50"
                  >
                    私下匯款一成保留金
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>

        <div className="border-t pt-3">
          <Button
            variant="ghost"
            onClick={onClose}
            className="w-full text-xs font-bold"
          >
            {task?.is_passed ? "關閉並前往購屋" : "稍後再查"}
          </Button>
        </div>
      </div>
    </div>
  )
}
