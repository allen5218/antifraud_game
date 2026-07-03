import type { QuizCompleteResponse } from "@/client"

interface QuizSummaryProps {
  result: QuizCompleteResponse
  onRestart: () => void
}

/** 回合結算:成績 + 獎勵 + 弱點彙整 */
export function QuizSummary({ result, onRestart }: QuizSummaryProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 px-6 py-10 text-center">
      <span className="text-5xl">📋</span>
      <h2 className="text-xl font-extrabold">
        {result.correct_count} / {result.total}
      </h2>
      <p className="text-sm text-muted-foreground">
        最佳連對 {result.best_streak}
      </p>
      <p className="text-lg font-bold text-green-600">
        +${result.cash_earned.toLocaleString()} · +{result.xp_earned} XP
      </p>
      {result.weakness_summary.length > 0 && (
        <div className="mt-2 w-full rounded-xl bg-muted p-3 text-left">
          <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            需要加強
          </p>
          <ul className="mt-1 flex flex-wrap gap-1.5">
            {result.weakness_summary.map((w) => (
              <li
                key={w.tag}
                className="rounded-md bg-red-50 px-2 py-0.5 text-xs font-semibold text-red-600 dark:bg-red-950"
              >
                {w.tag} ×{w.count}
              </li>
            ))}
          </ul>
        </div>
      )}
      <button
        type="button"
        onClick={onRestart}
        className="mt-2 w-full rounded-xl bg-foreground py-2.5 text-sm font-bold text-background"
      >
        再來一輪 ›
      </button>
      <a href="/" className="text-xs text-muted-foreground underline">
        回首頁
      </a>
    </div>
  )
}
