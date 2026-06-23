interface WeaknessItem {
  tag: string
  count: number
}

interface SwipeResult {
  correct_count: number
  total: number
  best_streak: number
  cash_earned: number
  xp_earned: number
  weakness_summary: WeaknessItem[]
}

export function SwipeRoundSummary({ result }: { result: SwipeResult }) {
  const top = result.weakness_summary[0]
  return (
    <div className="rounded-xl border bg-card p-4">
      <div className="mb-3 text-base font-bold">本輪結束 · 結算</div>
      <div className="grid grid-cols-3 gap-2">
        <Metric
          label="獎勵"
          value={`+$${result.cash_earned}`}
          accent="text-green-700"
        />
        <Metric label="經驗" value={`+${result.xp_earned} XP`} />
        <Metric label="最佳連勝" value={String(result.best_streak)} />
      </div>
      {top && (
        <div className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-800">
          這輪最常被「{top.tag}」話術騙過
        </div>
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
