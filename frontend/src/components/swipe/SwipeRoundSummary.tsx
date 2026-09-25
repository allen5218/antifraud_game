import { RotateCcw } from "lucide-react"
import type { SwipeCompleteResponse } from "@/client"

export function SwipeRoundSummary({
  result,
  onRestart,
}: {
  result: SwipeCompleteResponse
  onRestart?: () => void
}) {
  const top = result.weakness_summary[0]
  return (
    <div className="rounded-xl border bg-card p-4">
      <div className="mb-3 text-base font-bold">這一輪結束了</div>
      <div className="grid grid-cols-3 gap-2">
        <Metric
          label="獎勵"
          value={`+$${result.cash_earned}`}
          accent="text-legit"
        />
        <Metric label="經驗" value={`+${result.xp_earned} XP`} />
        <Metric label="最佳連勝" value={String(result.best_streak)} />
      </div>
      {top && (
        <div className="mt-3 rounded-md border border-warning/40 bg-warning/15 px-3 py-2 text-xs">
          這輪最常漏看的話術：<b>{top.label}</b>
        </div>
      )}
      {onRestart && (
        <button
          type="button"
          onClick={onRestart}
          className="mt-4 flex w-full items-center justify-center gap-1.5 rounded-xl bg-primary py-2.5 text-sm font-bold text-primary-foreground"
        >
          <RotateCcw aria-hidden className="size-4" />
          再來一輪
        </button>
      )}
    </div>
  )
}

function Metric({
  label,
  value,
  accent,
}: {
  label: string
  value: string
  accent?: string
}) {
  return (
    <div className="rounded-md bg-muted p-2">
      <div className="text-[10px] text-muted-foreground">{label}</div>
      <div className={`text-base font-bold ${accent ?? ""}`}>{value}</div>
    </div>
  )
}
