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
        className="text-rose-500 flex items-center gap-1 font-bold"
      >
        <Heart className="w-3.5 h-3.5 fill-rose-500 text-rose-500" />
        <span>
          {alertness}/{maxAlertness}
        </span>
      </span>
      <span className="flex items-center gap-3">
        <span className="flex items-center gap-1 text-amber-400 font-bold">
          <Flame className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
          <span>連勝 {streak}</span>
        </span>
        <span className="font-mono text-slate-400">
          {progress} / {total}
        </span>
      </span>
    </div>
  )
}
