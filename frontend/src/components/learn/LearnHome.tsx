import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { ChevronRight, Flame, GraduationCap, Play } from "lucide-react"
import type { CardSummary, HomeSummary } from "@/client"
import { mascotLine, mascotPose, poseImage } from "@/components/room/logic"
import { cardSummaryQuery } from "@/hooks/useCards"
import { useHomeSummary } from "@/hooks/useHomeSummary"
import { FRAUD_TYPE_LABELS } from "@/lib/fraudTypes"
import { cn } from "@/lib/utils"

/**
 * 一般模式的首頁（Lingvist 式）：今天的目標、一顆大的「繼續練習」、各類學會幾招。
 * 有要先做的事（試測、前測、檢測、補考、作業、問卷）時，吉祥物在最上面提醒，
 * 文字與連結和房間吉祥物同一份（`room/logic.ts` 的 `mascotLine`）。
 */
export function LearnHome() {
  const { data: summary } = useQuery(cardSummaryQuery)
  const { data: home } = useHomeSummary()
  return (
    <div data-testid="home-hero" className="mx-auto max-w-md space-y-5">
      {home && <Reminder home={home} />}
      {summary ? (
        <>
          <GoalCard summary={summary} />
          <ContinueButton summary={summary} />
          <Topics summary={summary} />
        </>
      ) : (
        <div className="h-64 animate-pulse rounded-3xl bg-surface-2" />
      )}
    </div>
  )
}

function Reminder({ home }: { home: HomeSummary }) {
  const line = mascotLine(home)
  // 只是一般的鼓勵（沒有要去哪裡）就不佔版面
  const urgent =
    line.action !== undefined ||
    Boolean(home.exam_active_attempt_id) ||
    Boolean(home.retake)
  if (!urgent) return null
  return (
    <div
      data-testid="home-reminder"
      className="flex items-center gap-3 rounded-2xl border border-primary/40 bg-primary/10 p-3"
    >
      <img
        src={poseImage(home.mascot_image_url, mascotPose(home, true))}
        alt=""
        className="size-14 shrink-0"
      />
      <p className="flex-1 text-base">{line.text}</p>
      {line.action && (
        <Link
          to={line.action.to}
          className="shrink-0 rounded-xl bg-primary px-4 py-2 font-bold text-primary-foreground"
        >
          {line.action.label}
        </Link>
      )}
    </div>
  )
}

function GoalCard({ summary }: { summary: CardSummary }) {
  const ratio = Math.min(1, summary.today_done / summary.daily_goal)
  const done = summary.today_done >= summary.daily_goal
  return (
    <section
      aria-label="今天的目標"
      className="rounded-3xl border border-border bg-card p-5 shadow-sm"
    >
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm text-muted-foreground">今天的目標</p>
          <p className="mt-1 text-3xl font-extrabold tabular-nums">
            {summary.today_done}
            <span className="text-lg font-bold text-muted-foreground">
              ／{summary.daily_goal} 張
            </span>
          </p>
          {done && (
            <p className="mt-1 text-sm font-semibold text-legit">完成了</p>
          )}
        </div>
        <Ring ratio={ratio} />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3">
        <Stat
          icon={<Flame aria-hidden className="size-5 text-warning" />}
          label="連續練習"
          value={`${summary.streak_days} 天`}
        />
        <Stat
          icon={<GraduationCap aria-hidden className="size-5 text-primary" />}
          label="學會的招數"
          value={`${summary.learned}／${summary.total} 招`}
        />
      </div>
    </section>
  )
}

function Ring({ ratio }: { ratio: number }) {
  const r = 30
  const c = 2 * Math.PI * r
  return (
    <svg
      viewBox="0 0 72 72"
      className="size-20 shrink-0 -rotate-90"
      role="img"
      aria-label={`完成 ${Math.round(ratio * 100)}%`}
    >
      <circle
        cx="36"
        cy="36"
        r={r}
        className="fill-none stroke-surface-3"
        strokeWidth="8"
      />
      <circle
        cx="36"
        cy="36"
        r={r}
        className="fill-none stroke-primary transition-all"
        strokeWidth="8"
        strokeLinecap="round"
        strokeDasharray={c}
        strokeDashoffset={c * (1 - ratio)}
      />
    </svg>
  )
}

function Stat({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: string
}) {
  return (
    <div className="flex items-center gap-2 rounded-2xl bg-surface-2 px-3 py-2">
      {icon}
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="font-bold tabular-nums">{value}</p>
      </div>
    </div>
  )
}

function ContinueButton({ summary }: { summary: CardSummary }) {
  const hint =
    summary.due_now > 0
      ? `有 ${summary.due_now} 張該複習了`
      : summary.today_done >= summary.daily_goal
        ? "想多練也可以"
        : null
  return (
    <div className="space-y-2">
      <Link
        to="/learn"
        data-testid="continue-practice"
        className="flex h-16 items-center justify-center gap-2 rounded-3xl bg-primary text-xl font-extrabold text-primary-foreground shadow-md"
      >
        <Play aria-hidden className="size-6 fill-current" />
        繼續練習
      </Link>
      {hint && (
        <p className="text-center text-sm text-muted-foreground">{hint}</p>
      )}
    </div>
  )
}

function Topics({ summary }: { summary: CardSummary }) {
  return (
    <section aria-label="只練某一類" className="space-y-2">
      <h2 className="px-1 text-base font-bold">只練某一類</h2>
      <ul className="space-y-2">
        {summary.topics.map((t) => {
          const ratio = t.total ? t.learned / t.total : 0
          return (
            <li key={t.fraud_type}>
              <Link
                to="/learn"
                search={{ topic: t.fraud_type }}
                data-testid={`topic-${t.fraud_type}`}
                className="flex items-center gap-3 rounded-2xl border border-border bg-card px-4 py-3 hover:bg-surface-2"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="font-bold">
                      {FRAUD_TYPE_LABELS[t.fraud_type] ?? "防詐常識"}
                    </span>
                    <span className="text-sm tabular-nums text-muted-foreground">
                      學會 {t.learned}／{t.total} 招
                    </span>
                  </div>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-surface-2">
                    <div
                      className={cn(
                        "h-full rounded-full",
                        ratio >= 1 ? "bg-legit" : "bg-primary",
                      )}
                      style={{ width: `${ratio * 100}%` }}
                    />
                  </div>
                </div>
                <ChevronRight
                  aria-hidden
                  className="size-5 shrink-0 text-muted-foreground"
                />
              </Link>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
