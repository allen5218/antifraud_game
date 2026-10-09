import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import type { ExamStartRequest } from "@/client"
import { ExamService } from "@/client/sdk.gen"
import { Button } from "@/components/ui/button"
import { FRAUD_TYPES, fraudTypeLabel } from "@/lib/fraudTypes"
import { ExamBadges } from "./ExamBadges"
import { ExamGate } from "./ExamGate"
import { examError, examKindLabel } from "./exam"

export function ExamHome() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [type, setType] = useState<string>(FRAUD_TYPES[0])
  const status = useQuery({
    queryKey: ["exam", "status"],
    queryFn: () => ExamService.readStatus(),
    retry: false,
    staleTime: 0,
  })
  const history = useQuery({
    queryKey: ["exam", "history"],
    queryFn: () => ExamService.history(),
    retry: false,
    staleTime: 0,
  })
  const attemptId = status.data?.active_attempt_id ?? null
  const activeAttempt = useQuery({
    queryKey: ["exam", "attempt", attemptId],
    queryFn: () => ExamService.read({ attemptId: attemptId ?? "" }),
    enabled: Boolean(attemptId),
    retry: false,
    staleTime: 0,
  })
  const start = useMutation({
    mutationFn: (requestBody: ExamStartRequest) =>
      ExamService.start({ requestBody }),
    onSuccess: (state) => {
      qc.setQueryData(["exam", "attempt", state.id], state)
      for (const key of ["exam", "practice", "scenario"])
        void qc.invalidateQueries({ queryKey: [key] })
      void navigate({ to: "/exam/$attemptId", params: { attemptId: state.id } })
    },
    onError: () => {
      void status.refetch()
      void history.refetch()
    },
  })
  const data = status.data
  if (!data)
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">檢測</h1>
        {status.isError ? (
          <>
            <p role="alert">檢測資格讀不到，請再試一次。</p>
            <Button onClick={() => status.refetch()}>重新讀取</Button>
          </>
        ) : (
          <p>正在讀取檢測資格…</p>
        )}
      </div>
    )
  const blocked =
    !data.can_start || start.isPending || status.isFetching || status.isError
  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-bold">檢測</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          七十分過關。開始後一小時內完成，可離開再回來繼續。
        </p>
        <p className="mt-2 text-sm">
          今天還能檢測 {Math.max(0, data.daily_limit - data.daily_used)} 次，共{" "}
          {data.daily_limit} 次。
        </p>
      </header>
      {data.active_attempt_id && (
        <section className="space-y-3 rounded-2xl border border-primary bg-primary/10 p-4">
          <h2 className="font-bold">有一場檢測還沒完成</h2>
          {activeAttempt.data && (
            <p className="text-sm">
              {examKindLabel(
                activeAttempt.data.mode,
                activeAttempt.data.fraud_type,
              )}
            </p>
          )}
          <Link
            to="/exam/$attemptId"
            params={{ attemptId: data.active_attempt_id }}
            className="inline-block rounded-xl bg-primary px-4 py-3 font-bold text-primary-foreground"
          >
            繼續檢測
          </Link>
        </section>
      )}
      {data.gate && <ExamGate gate={data.gate} />}
      {data.block_reason === "exam_daily_limit" && (
        <p role="alert" className="text-sm text-warning">
          今天的檢測次數用完了，明天再來。
        </p>
      )}
      {status.isError && (
        <div role="alert">
          <p>資格暫時讀不到，請先重新讀取。</p>
          <Button onClick={() => status.refetch()}>重新讀取</Button>
        </div>
      )}
      {start.isError && (
        <p role="alert" className="text-sm text-scam">
          {examError(start.error)}
        </p>
      )}
      <section className="space-y-3 rounded-2xl border bg-card p-5">
        <h2 className="text-lg font-bold">綜合檢測</h2>
        <p className="text-sm">先做 20 題前測，再考你最弱的一類。</p>
        <p className="text-xs text-muted-foreground">
          前測、滑卡、訊息判讀、情境對抗，共四關。
        </p>
        <Button
          className="w-full"
          disabled={blocked}
          onClick={() => {
            if (!start.isPending) start.mutate({ mode: "comprehensive" })
          }}
        >
          開始綜合檢測
        </Button>
      </section>
      <section className="space-y-3 rounded-2xl border bg-card p-5">
        <h2 className="text-lg font-bold">專項檢測</h2>
        <p className="text-sm">選一類，完成滑卡、訊息判讀和情境對抗三關。</p>
        <label className="block text-sm">
          要考哪一類？
          <select
            aria-label="檢測類型"
            className="mt-2 w-full rounded-xl border bg-background p-3"
            value={type}
            disabled={start.isPending}
            onChange={(event) => setType(event.target.value)}
          >
            {FRAUD_TYPES.map((slug) => (
              <option key={slug} value={slug}>
                {fraudTypeLabel(slug)}
              </option>
            ))}
          </select>
        </label>
        <Button
          className="w-full"
          disabled={blocked}
          onClick={() => {
            if (!start.isPending)
              start.mutate({ mode: "specialized", fraud_type: type })
          }}
        >
          開始專項檢測
        </Button>
      </section>
      <ExamBadges badges={data.badges} />
      <section className="space-y-3">
        <h2 className="text-lg font-bold">檢測紀錄</h2>
        {history.isPending ? (
          <p className="text-sm">正在讀取紀錄…</p>
        ) : history.isError ? (
          <>
            <p role="alert">檢測紀錄暫時讀不到。</p>
            <Button variant="outline" onClick={() => history.refetch()}>
              重新讀取紀錄
            </Button>
          </>
        ) : !history.data?.length ? (
          <p className="text-sm text-muted-foreground">還沒有檢測紀錄。</p>
        ) : (
          <ul className="space-y-2">
            {history.data.map((row) => (
              <li key={row.id}>
                <Link
                  to="/exam/$attemptId"
                  params={{ attemptId: row.id }}
                  className="block rounded-xl border bg-card p-3 text-sm"
                >
                  <span>
                    {row.mode === "comprehensive" ? "綜合檢測" : "專項檢測"}
                    {row.fraud_type
                      ? `・${fraudTypeLabel(row.fraud_type)}`
                      : ""}
                  </span>
                  <span className="mt-1 block text-xs text-muted-foreground">
                    {new Date(row.created_at).toLocaleDateString("zh-TW", {
                      timeZone: "Asia/Taipei",
                    })}
                    ・
                    {row.status === "active"
                      ? "進行中"
                      : row.status === "voided"
                        ? "不計次"
                        : `${row.total_score ?? 0} 分・${row.passed ? "通過" : "沒過"}`}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
