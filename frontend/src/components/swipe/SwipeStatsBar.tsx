import { Flame, Heart } from "lucide-react"

interface Props {
  alertness: number
  maxAlertness: number
  streak: number
  progress: number
  total: number
}

export function SwipeStatsBar({
  alertness,
  maxAlertness,
  streak,
  progress,
  total,
}: Props) {
  return (
    <div className="flex items-center justify-between text-xs text-muted-foreground">
      <span
        data-testid="swipe-alertness"
        className="flex items-center gap-1 font-semibold text-scam"
      >
        <Heart aria-hidden className="size-3.5 fill-current" />
        <span className="sr-only">警覺值</span>
        {alertness}/{maxAlertness}
      </span>
      <span className="flex gap-3">
        <span className="flex items-center gap-1">
          <Flame aria-hidden className="size-3.5 text-warning" />
          連勝 {streak}
        </span>
        <span>
          {progress} / {total}
        </span>
      </span>
    </div>
  )
}
