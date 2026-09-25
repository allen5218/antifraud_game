import { Link } from "@tanstack/react-router"
import { ClipboardList, Target } from "lucide-react"
import type { PracticeProfilePublic } from "@/client"
import { usePracticeProfile } from "@/hooks/usePractice"
import { FRAUD_TYPES, fraudTypeLabel } from "@/lib/fraudTypes"

/**
 * 練習重點卡(首頁、個人頁)。
 *
 * 後端每輪結算後會重新分析作答紀錄,決定五類的出題比例;這張卡把結果攤給玩家看:
 * 多練哪一類、為什麼(note 是後端寫好的一句話)、各類比例。
 * 沒有任何紀錄時改成引導去做前測。
 */
export function PracticeFocusCard({ className = "" }: { className?: string }) {
  const { data, isError, refetch } = usePracticeProfile()
  if (isError && !data) {
    return (
      <section
        data-testid="practice-focus-card"
        className={`rounded-2xl border border-border bg-surface-3 p-4 ${className}`}
      >
        <Heading />
        <p className="mt-1 text-xs text-muted-foreground">
          練習重點暫時讀不到。
        </p>
        <button
          type="button"
          onClick={() => refetch()}
          className="mt-3 rounded-lg border border-border px-3 py-1.5 text-xs font-bold"
        >
          重新讀取
        </button>
      </section>
    )
  }
  if (!data) return null

  if (data.source === "none") {
    return (
      <section
        data-testid="practice-focus-card"
        className={`rounded-2xl border border-border bg-surface-3 p-4 ${className}`}
      >
        <Heading />
        <p className="mt-1 text-xs text-muted-foreground">{data.note}</p>
        <Link
          to="/pretest"
          className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-bold text-primary-foreground transition hover:brightness-110"
        >
          <ClipboardList aria-hidden className="size-3.5" />
          做前測
        </Link>
      </section>
    )
  }

  return (
    <section
      data-testid="practice-focus-card"
      className={`rounded-2xl border border-border bg-surface-3 p-4 ${className}`}
    >
      <Heading />
      <p className="mt-1 text-base font-bold">
        {data.focus_label ? `多練「${data.focus_label}」` : "五類平均練習"}
      </p>
      <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
        {data.note}
      </p>
      <WeightBars profile={data} />
      <p className="mt-3 text-[10px] text-muted-foreground">
        題組、滑卡、情境對抗都照這個比例出題，每玩完一輪會重新分析。
      </p>
    </section>
  )
}

function Heading() {
  return (
    <h2 className="flex items-center gap-1.5 text-[11px] font-bold text-muted-foreground">
      <Target aria-hidden className="size-3.5 text-warning" />
      你的練習重點
    </h2>
  )
}

/**
 * 比例的顯示文字。整數就顯示整數,否則留一位小數。
 * 全部四捨五入到整數的話,常見的 50% + 12.5%×4 會顯示成 50 + 13×4 = 102%。
 */
function formatPercent(weight: number): string {
  const pct = weight * 100
  return Math.abs(pct - Math.round(pct)) < 0.05
    ? String(Math.round(pct))
    : pct.toFixed(1)
}

function WeightBars({ profile }: { profile: PracticeProfilePublic }) {
  return (
    <ul className="mt-3 grid gap-1.5" aria-label="各類出題比例">
      {FRAUD_TYPES.map((slug) => {
        const weight = profile.weights[slug] ?? 0
        const isFocus = slug === profile.focus_type
        return (
          <li key={slug} className="flex items-center gap-2 text-[11px]">
            <span
              className={`w-14 shrink-0 ${isFocus ? "font-bold" : "text-muted-foreground"}`}
            >
              {fraudTypeLabel(slug)}
            </span>
            <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
              <span
                className={`block h-full rounded-full ${isFocus ? "bg-warning" : "bg-primary/70"}`}
                style={{ width: `${weight * 100}%` }}
              />
            </span>
            <span className="w-10 shrink-0 text-right tabular-nums text-muted-foreground">
              {formatPercent(weight)}%
            </span>
          </li>
        )
      })}
    </ul>
  )
}

/** 題組、滑卡、收件匣頂端的小標:這一輪偏重哪一類。沒有重點時不顯示。 */
export function PracticeFocusBadge({ className = "" }: { className?: string }) {
  const { data } = usePracticeProfile()
  if (!data?.focus_label) return null
  return (
    <p
      data-testid="practice-focus-badge"
      className={`flex items-center gap-1.5 rounded-lg bg-warning/15 px-2.5 py-1.5 text-[11px] ${className}`}
    >
      <Target aria-hidden className="size-3.5 shrink-0 text-warning" />
      <span>
        本輪加強：<b>{data.focus_label}</b>
      </span>
    </p>
  )
}
