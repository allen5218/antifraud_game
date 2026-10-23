import { useQuery } from "@tanstack/react-query"
import { Check, X } from "lucide-react"
import { AdminCohortsService, type ParticipantDetail } from "@/client"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { fraudTypeLabel } from "@/lib/fraudTypes"
import {
  EXAM_MODE_LABELS,
  EXAM_STAGE_LABELS,
  EXAM_STATUS_LABELS,
  PRACTICE_MODE_LABELS,
  seconds,
  taipeiTime,
} from "./format"

function Section({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <section className="flex flex-col gap-2">
      <h3 className="font-bold">{title}</h3>
      {children}
    </section>
  )
}

function Pretests({ detail }: { detail: ParticipantDetail }) {
  if (detail.pretests.length === 0)
    return <p className="text-sm text-muted-foreground">還沒做。</p>
  return (
    <>
      {detail.pretests.map((p, n) => (
        <details
          key={p.at ?? n}
          className="rounded-lg border border-border bg-card p-3 text-sm"
        >
          <summary className="cursor-pointer font-medium">
            第 {n + 1} 次・答對 {p.correct}／{p.total}・{seconds(p.seconds)}・
            最弱 {fraudTypeLabel(p.weakest_type)}
            <span className="ml-2 text-xs text-muted-foreground">
              {taipeiTime(p.at)}
            </span>
          </summary>
          <ol className="mt-2 flex flex-col gap-1">
            {p.items.map((item, i) => (
              <li key={`${i}-${item.question}`} className="flex gap-2">
                {item.is_correct ? (
                  <Check
                    aria-label="答對"
                    className="mt-0.5 size-4 shrink-0 text-legit"
                  />
                ) : (
                  <X
                    aria-label="答錯"
                    className="mt-0.5 size-4 shrink-0 text-scam"
                  />
                )}
                <span className="min-w-0 flex-1">
                  <span className="text-xs text-muted-foreground">
                    {fraudTypeLabel(item.fraud_type)}・選 {item.selected}
                    {item.is_correct ? "" : `（正解 ${item.correct_option}）`}
                  </span>
                  <span className="line-clamp-2 block">{item.question}</span>
                </span>
              </li>
            ))}
          </ol>
        </details>
      ))}
    </>
  )
}

function Exams({ detail }: { detail: ParticipantDetail }) {
  if (detail.exams.length === 0)
    return <p className="text-sm text-muted-foreground">還沒考過。</p>
  return (
    <ul className="flex flex-col gap-2">
      {detail.exams.map((e) => (
        <li
          key={e.id}
          className="rounded-lg border border-border bg-card p-3 text-sm"
        >
          <p className="font-medium">
            {EXAM_MODE_LABELS[e.mode] ?? e.mode}
            {e.fraud_type ? `・${fraudTypeLabel(e.fraud_type)}` : ""}・
            {EXAM_STATUS_LABELS[e.status] ?? e.status}
            {e.counted ? "" : "（不算次數）"}
          </p>
          <p>
            {e.status === "active"
              ? "還在考"
              : `${e.score} 分・${e.passed ? "通過" : "沒過"}`}
            {e.seconds != null && `・用時 ${seconds(e.seconds)}`}
          </p>
          <p className="text-muted-foreground">
            {e.stages
              .map(
                (s) =>
                  `${EXAM_STAGE_LABELS[s.stage] ?? s.stage} ${s.correct}／${s.total}`,
              )
              .join("・")}
          </p>
          <p className="text-xs text-muted-foreground">
            開始 {taipeiTime(e.started_at)}
          </p>
        </li>
      ))}
    </ul>
  )
}

function DetailBody({ detail }: { detail: ParticipantDetail }) {
  return (
    <div className="flex flex-col gap-5">
      <dl className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <dt className="text-muted-foreground">加入時間</dt>
          <dd>{taipeiTime(detail.created_at)}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">最後活動</dt>
          <dd>{taipeiTime(detail.last_active_at)}</dd>
        </div>
        {detail.nickname && (
          <div>
            <dt className="text-muted-foreground">暱稱</dt>
            <dd>{detail.nickname}</dd>
          </div>
        )}
      </dl>
      <Section title="練習量">
        <ul className="grid grid-cols-3 gap-2 text-center text-sm">
          {detail.practice.map((p) => (
            <li
              key={p.mode}
              className="rounded-lg border border-border bg-card p-2"
            >
              <span className="block text-xs text-muted-foreground">
                {PRACTICE_MODE_LABELS[p.mode] ?? p.mode}
              </span>
              <span className="block text-lg font-bold">{p.total}</span>
              <span className="block text-xs text-muted-foreground">
                {p.mode === "scenario" ? "判斷對" : "答對"} {p.correct}
              </span>
            </li>
          ))}
        </ul>
        <p className="text-xs text-muted-foreground">
          情境對抗聊過 {detail.scenario_sessions}{" "}
          場（有回過訊息的，含還沒判斷的）。
        </p>
      </Section>
      <Section title="入門前測">
        <Pretests detail={detail} />
      </Section>
      <Section title="檢測">
        <Exams detail={detail} />
      </Section>
      <Section title="問卷">
        {detail.survey ? (
          <>
            <p className="text-sm">
              {taipeiTime(detail.survey.submitted_at)} 交・
              {seconds(detail.survey.seconds)}・注意力題
              {detail.survey.attention_ok ? "對" : "錯"}
            </p>
            <dl className="divide-y divide-border rounded-lg border border-border bg-card text-sm">
              {detail.survey.answers.map((a) => (
                <div key={a.question} className="px-3 py-2">
                  <dt className="text-xs text-muted-foreground">
                    {a.question}
                  </dt>
                  <dd className="whitespace-pre-wrap">
                    {a.answer || "（沒填）"}
                  </dd>
                </div>
              ))}
            </dl>
          </>
        ) : (
          <p className="text-sm text-muted-foreground">還沒交。</p>
        )}
      </Section>
    </div>
  )
}

/** 點受試編號打開：前測每題、每次檢測、練習量、問卷答案 */
export function MemberDetail({
  cohortId,
  userId,
  code,
  onClose,
}: {
  cohortId: string
  userId: string | null
  code: string | null
  onClose: () => void
}) {
  const detail = useQuery({
    queryKey: ["admin", "cohorts", cohortId, "member", userId],
    queryFn: () =>
      AdminCohortsService.memberDetail({ cohortId, userId: userId! }),
    enabled: Boolean(userId),
  })
  return (
    <Dialog open={Boolean(userId)} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{code ?? "受試者"}</DialogTitle>
          <DialogDescription>這位受試者目前所有的紀錄。</DialogDescription>
        </DialogHeader>
        {detail.isPending && <output>正在載入…</output>}
        {detail.isError && (
          <p role="alert" className="text-scam">
            讀不到這位受試者的紀錄。
          </p>
        )}
        {detail.data && <DetailBody detail={detail.data} />}
      </DialogContent>
    </Dialog>
  )
}
