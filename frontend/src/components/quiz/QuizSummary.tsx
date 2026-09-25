import { Link } from "@tanstack/react-router"
import { RotateCcw } from "lucide-react"
import type { QuizCompleteResponse } from "@/client"

interface QuizSummaryProps {
  result: QuizCompleteResponse
  onRestart: () => void
}

/** 回合結算：成績、獎勵、這輪漏看的話術 */
export function QuizSummary({ result, onRestart }: QuizSummaryProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 px-6 py-10 text-center">
      <img
        src="/assets/misc/quiz-summary.webp"
        alt=""
        aria-hidden="true"
        width={96}
        height={96}
        className="size-24 rounded-2xl object-cover"
      />
      <h2 className="text-xl font-extrabold">
        {result.correct_count} / {result.total}
      </h2>
      <p className="text-sm text-muted-foreground">
        最多連續答對 {result.best_streak} 題
      </p>
      <p className="text-lg font-bold text-legit">
        +${result.cash_earned.toLocaleString()} · +{result.xp_earned} XP
      </p>
      {result.weakness_summary.length > 0 && (
        <div className="mt-2 w-full rounded-xl bg-muted p-3 text-left">
          <p className="text-[11px] font-bold text-muted-foreground">
            這輪漏看的話術
          </p>
          <ul className="mt-1 flex flex-wrap gap-1.5">
            {result.weakness_summary.map((w) => (
              <li
                key={w.tag}
                className="rounded-md bg-scam/15 px-2 py-0.5 text-xs font-semibold text-scam"
              >
                {w.label} ×{w.count}
              </li>
            ))}
          </ul>
        </div>
      )}
      <p className="text-[11px] text-muted-foreground">
        接下來的題目會依照這輪的結果調整。
      </p>
      <button
        type="button"
        onClick={onRestart}
        className="mt-1 flex w-full items-center justify-center gap-1.5 rounded-xl bg-primary py-2.5 text-sm font-bold text-primary-foreground"
      >
        <RotateCcw aria-hidden className="size-4" />
        再來一輪
      </button>
      <Link to="/" className="text-xs text-muted-foreground underline">
        回首頁
      </Link>
    </div>
  )
}
