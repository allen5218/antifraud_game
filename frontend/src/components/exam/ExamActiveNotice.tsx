import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { useState } from "react"
import { ExamService } from "@/client/sdk.gen"
import { Button } from "@/components/ui/button"
import { ExamAbandonDialog } from "./ExamAbandonDialog"
import { examError, examKindLabel } from "./exam"

/**
 * 首頁最上方的進行中檢測。只讀檢測狀態與那一份卷。
 * 每日訓練會建立牌局並開始計時，所以留在每日訓練頁才讀。
 */
export function ExamActiveNotice() {
  const qc = useQueryClient()
  const status = useQuery({
    queryKey: ["exam", "status"],
    queryFn: () => ExamService.readStatus(),
    retry: false,
    staleTime: 0,
  })
  const attemptId = status.data?.active_attempt_id ?? null
  const attempt = useQuery({
    queryKey: ["exam", "attempt", attemptId],
    queryFn: () => ExamService.read({ attemptId: attemptId ?? "" }),
    enabled: Boolean(attemptId),
    retry: false,
    staleTime: 0,
  })
  const [open, setOpen] = useState(false)
  const abandon = useMutation({
    mutationFn: () => ExamService.abandon({ attemptId: attemptId ?? "" }),
    onSuccess: () => {
      setOpen(false)
      void qc.invalidateQueries({ queryKey: ["exam"] })
      void qc.invalidateQueries({ queryKey: ["practice"] })
    },
  })
  if (!attemptId) return null
  const detail = attempt.data
    ? examKindLabel(attempt.data.mode, attempt.data.fraud_type)
    : null
  return (
    <section className="mb-3 space-y-3 rounded-2xl border border-primary bg-primary/10 p-4">
      <h2 className="font-bold">你有一份檢測還沒做完</h2>
      {detail && <p className="text-sm">{detail}</p>}
      <div className="flex flex-wrap gap-2">
        <Link
          to="/exam/$attemptId"
          params={{ attemptId }}
          className="inline-flex items-center justify-center rounded-xl bg-primary px-4 py-3 text-sm font-bold text-primary-foreground"
        >
          繼續檢測
        </Link>
        <Button
          variant="outline"
          disabled={abandon.isPending}
          onClick={() => setOpen(true)}
        >
          放棄
        </Button>
      </div>
      {abandon.isError && (
        <p role="alert" className="text-sm text-scam">
          {examError(abandon.error)}
        </p>
      )}
      <ExamAbandonDialog
        open={open}
        pending={abandon.isPending}
        onOpenChange={setOpen}
        onConfirm={() => {
          if (!abandon.isPending) abandon.mutate()
        }}
      />
    </section>
  )
}
