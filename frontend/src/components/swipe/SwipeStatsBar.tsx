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
      <span data-testid="swipe-alertness" className="text-red-600">
        ❤️ {alertness}/{maxAlertness}
      </span>
      <span className="flex gap-3">
        <span>🔥 連勝 {streak}</span>
        <span>
          {progress} / {total}
        </span>
      </span>
    </div>
  )
}
