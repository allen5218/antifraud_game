import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { Clock } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import type {
  ExamMessageAnswer,
  ExamPretestAnswer,
  ExamState,
  ExamSwipeAnswer,
} from "@/client"
import { ExamService } from "@/client/sdk.gen"
import { Button } from "@/components/ui/button"
import { fraudTypeLabel } from "@/lib/fraudTypes"
import { ExamAbandonDialog } from "./ExamAbandonDialog"
import { ExamResult } from "./ExamResult"
import { ExamScenario } from "./ExamScenario"
import { ExamStage } from "./ExamStage"
import {
  clearDraft,
  type DraftAnswer,
  errorCode,
  examError,
  secondsLeft,
} from "./exam"

const LABELS = {
  pretest: "前測",
  swipe: "滑卡",
  message: "訊息判讀",
  scenario: "情境對抗",
  done: "結果",
}
export function ExamAttempt({ attemptId }: { attemptId: string }) {
  const qc = useQueryClient()
  const queryKey = ["exam", "attempt", attemptId]
  const [busy, setBusy] = useState(false)
  const lock = useRef(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [confirm, setConfirm] = useState(false)
  const [now, setNow] = useState(Date.now())
  const expiredRead = useRef(false)
  const query = useQuery({
    queryKey,
    queryFn: () => ExamService.read({ attemptId }),
    retry: false,
    enabled: !busy,
    staleTime: 0,
    refetchInterval: (q) => {
      const current = q.state.data
      if (current?.status !== "active") return false
      return secondsLeft(current.expires_at) === 0 ? 10_000 : 30_000
    },
  })
  const state = query.data
  const remaining = state ? secondsLeft(state.expires_at, now) : 0
  const refetchExam = query.refetch
  useEffect(() => {
    if (state?.status !== "active") return
    const timer = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(timer)
  }, [state?.status])
  useEffect(() => {
    if (state?.status !== "active" || remaining !== 0 || busy) return
    if (expiredRead.current) return
    expiredRead.current = true
    void refetchExam().catch(() => undefined)
  }, [state?.status, remaining, busy, refetchExam])

  const mutate = async (operation: () => PromiseLike<ExamState>) => {
    if (lock.current || state?.status !== "active") return
    lock.current = true
    setBusy(true)
    setNotice(null)
    await qc.cancelQueries({ queryKey })
    try {
      const next = await operation()
      if (state && (next.stage !== state.stage || next.status !== "active"))
        clearDraft(state)
      qc.setQueryData(queryKey, next)
      for (const key of ["practice", "economy", "scenario", "exam"] as const)
        void qc.invalidateQueries({
          queryKey: [key],
          refetchType: key === "economy" ? "active" : "none",
        })
      setConfirm(false)
    } catch (error) {
      if (errorCode(error) === "exam_scenario_already_answered") {
        try {
          const latest = await refetchExam()
          if (!latest.isError && latest.data) setNotice(null)
          else setNotice(examError(error))
        } catch {
          setNotice(examError(error))
        }
      } else {
        setNotice(examError(error))
      }
    } finally {
      lock.current = false
      setBusy(false)
    }
  }
  const submit = (answers: DraftAnswer[]) =>
    mutate(() => {
      if (state?.stage === "pretest")
        return ExamService.pretest({
          attemptId,
          requestBody: { answers: answers as ExamPretestAnswer[] },
        })
      if (state?.stage === "swipe")
        return ExamService.swipe({
          attemptId,
          requestBody: { answers: answers as ExamSwipeAnswer[] },
        })
      return ExamService.message({
        attemptId,
        requestBody: { answers: answers as ExamMessageAnswer[] },
      })
    })
  if (!state)
    return (
      <div className="space-y-4 py-6">
        {query.isError ? (
          <>
            <p role="alert">{examError(query.error)}</p>
            <Button
              onClick={() => {
                void query.refetch().catch(() => undefined)
              }}
            >
              重新讀取
            </Button>
            <Link to="/exam" className="block text-primary">
              回檢測頁
            </Link>
          </>
        ) : (
          <p>正在讀取檢測…</p>
        )}
      </div>
    )
  if (state.status !== "active") return <ExamResult state={state} />
  const stages =
    state.mode === "comprehensive"
      ? ["前測", "滑卡", "訊息判讀", "情境對抗"]
      : ["滑卡", "訊息判讀", "情境對抗"]
  return (
    <div className="space-y-4">
      <header className="space-y-3">
        <div className="flex items-center justify-between gap-2">
          <h1 className="text-xl font-bold">{LABELS[state.stage]}</h1>
          <Button
            variant="outline"
            size="sm"
            disabled={busy}
            onClick={() => setConfirm(true)}
          >
            放棄檢測
          </Button>
        </div>
        {state.fraud_type && (
          <p className="text-sm text-muted-foreground">
            {fraudTypeLabel(state.fraud_type)}
          </p>
        )}
        <p className="flex flex-wrap items-center gap-1 text-sm tabular-nums">
          <Clock aria-hidden className="size-4" />
          剩餘時間 {Math.floor(remaining / 60)}：
          {String(remaining % 60).padStart(2, "0")}
          {remaining === 0 && (
            <span className="font-normal text-muted-foreground">
              正在確認時間
            </span>
          )}
        </p>
        <ol aria-label="檢測關卡" className="flex gap-1">
          {stages.map((label, index) => (
            <li
              key={label}
              aria-current={
                state.progress.stage_index === index ? "step" : undefined
              }
              className={`min-w-0 flex-1 rounded-lg px-1 py-2 text-center text-xs ${index <= state.progress.stage_index ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
            >
              {index + 1} {label}
            </li>
          ))}
        </ol>
      </header>
      {(notice || query.isError) && (
        <div
          role="alert"
          className="space-y-2 rounded-xl bg-scam/10 p-3 text-sm text-scam"
        >
          <p>{notice ?? "進度暫時讀不到，請重新讀取。"}</p>
          <Button
            variant="outline"
            disabled={busy}
            onClick={() => {
              void query
                .refetch()
                .then((result) => {
                  if (!result.isError) setNotice(null)
                })
                .catch(() => undefined)
            }}
          >
            重新讀取檢測
          </Button>
        </div>
      )}
      {state.stage === "scenario" ? (
        <ExamScenario
          key={state.scenario?.session_id ?? `next-${state.scenario?.index}`}
          state={state}
          busy={busy}
          mutate={mutate}
          refresh={() => query.refetch().catch(() => undefined)}
        />
      ) : (
        <ExamStage
          key={`${state.id}:${state.stage}`}
          state={state}
          onSubmit={submit}
          busy={busy}
        />
      )}
      <ExamAbandonDialog
        open={confirm}
        pending={busy}
        onOpenChange={setConfirm}
        onConfirm={() => mutate(() => ExamService.abandon({ attemptId }))}
      />
    </div>
  )
}
