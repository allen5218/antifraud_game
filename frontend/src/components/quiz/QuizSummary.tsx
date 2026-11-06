import { Link } from "@tanstack/react-router"
import { RotateCcw, Sparkles } from "lucide-react"
import type { ReactNode } from "react"
import type { QuizCompleteResponse } from "@/client"
import { RewardBreakdown } from "@/components/progression/RewardBreakdown"
import { formatMoney } from "@/utils/money"

interface QuizSummaryProps {
  result: QuizCompleteResponse
  /** 沒給就不顯示「再來一輪」（每日訓練一天只有一次） */
  onRestart?: () => void
  /** 放在成績下方的額外內容，例如每日訓練的排名入口 */
  children?: ReactNode
}

/** 回合結算：成績、獎勵、這輪漏看的話術 */
export function QuizSummary({ result, onRestart, children }: QuizSummaryProps) {
  const receipt = result.reward_receipt
  const earnedEnergy = BigInt(receipt?.final?.forge_energy ?? "0")
  const earnedGxp = BigInt(receipt?.final?.growth_xp ?? "0")
  const coreAfter = receipt?.core_level_after ?? 0
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
        +${formatMoney(result.cash_earned)} · +{result.xp_earned} XP
      </p>
      {receipt && <RewardBreakdown receipt={receipt} className="my-1" />}
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
      {children}
      {onRestart && (
        <button
          type="button"
          onClick={onRestart}
          className="mt-1 flex w-full items-center justify-center gap-1.5 rounded-xl bg-primary py-2.5 text-sm font-bold text-primary-foreground"
        >
          <RotateCcw aria-hidden className="size-4" />
          再來一輪
        </button>
      )}
      <Link
        to="/progression"
        className="flex w-full items-center justify-center gap-1.5 rounded-xl border border-border bg-surface-2 py-2.5 text-xs font-bold text-foreground hover:bg-surface-3"
      >
        <Sparkles aria-hidden className="size-3.5 text-primary" />
        前往養成與配裝（核心 Lv.{coreAfter}
        {earnedGxp > 0n ? ` · 本輪 +${formatMoney(earnedGxp)} 養成經驗` : ""}
        {earnedEnergy > 0n ? ` / +${formatMoney(earnedEnergy)} 能量` : ""}）
      </Link>
      <Link to="/" className="text-xs text-muted-foreground underline">
        回房間
      </Link>
    </div>
  )
}
