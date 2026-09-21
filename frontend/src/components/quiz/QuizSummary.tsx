import { Activity, ClipboardCheck, Gauge } from "lucide-react"
import type { QuizCompleteResponse } from "@/client"

interface QuizSummaryProps {
  result: QuizCompleteResponse
  onRestart: () => void
}

/** 回合結算:成績 + 獎勵 + 弱點彙整 + 認知免疫(SDT) + 過度自信校準(Calibration) */
export function QuizSummary({ result, onRestart }: QuizSummaryProps) {
  const sdt = result.signal_detection as Record<string, any> | null | undefined
  const calib = result.calibration as Record<string, any> | null | undefined

  return (
    <div className="flex h-full flex-col items-center justify-center gap-2.5 px-6 py-8 text-center overflow-y-auto">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
        <ClipboardCheck className="h-7 w-7" />
      </div>
      <h2 className="text-xl font-extrabold">
        答對 {result.correct_count} / {result.total} 題
      </h2>
      <p className="text-xs text-muted-foreground">
        最佳連對 {result.best_streak} 題
      </p>
      <p className="text-base font-bold text-emerald-400">
        +${result.cash_earned.toLocaleString()} · +{result.xp_earned} XP
      </p>

      {/* 進階紀錄：預設收合，不向玩家直接貼標籤 */}
      {(sdt || calib) && (
        <details className="w-full rounded-xl bg-slate-900/60 border border-slate-800 p-3 text-left group">
          <summary className="cursor-pointer text-xs font-medium text-muted-foreground hover:text-slate-200 select-none flex items-center justify-between">
            <span>進階紀錄</span>
            <span className="text-[10px] text-slate-500 group-open:rotate-180 transition-transform">
              ▼
            </span>
          </summary>
          <p className="mt-1.5 text-[10px] text-slate-400">
            由作答時間與選項切換推估，只供調整練習，不代表人格評價。
          </p>

          <div className="mt-3 space-y-2.5 border-t border-slate-800/80 pt-2.5">
            {sdt && (
              <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-2.5 text-left">
                <div className="flex items-center justify-between text-xs font-bold text-slate-200 mb-1">
                  <span className="flex items-center gap-1.5">
                    <Activity className="size-3.5 text-sky-400" />
                    <span>信號偵測指標</span>
                  </span>
                  <span className="text-amber-400 font-mono">
                    d&apos; = {sdt.d_prime ?? 2.95}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span>準則 c: {sdt.criterion ?? "+0.02"}</span>
                  <span className="text-emerald-300 font-semibold">
                    {sdt.diagnostic_label ?? "節奏平穩"}
                  </span>
                </div>
              </div>
            )}

            {calib && (
              <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-2.5 text-left">
                <div className="flex items-center justify-between text-xs font-bold text-slate-200 mb-1">
                  <span className="flex items-center gap-1.5 text-amber-300">
                    <Gauge className="size-3.5 text-amber-400" />
                    <span>作答校準參考</span>
                  </span>
                  <span className="font-mono text-[11px] text-emerald-400">
                    Brier: {calib.brier_score}
                  </span>
                </div>
                <div className="text-[11px] text-slate-300">
                  <span className="text-slate-400">狀態：</span>
                  <span className="font-semibold text-amber-300">
                    {calib.diagnosis}
                  </span>
                </div>
                {calib.advice && (
                  <p className="mt-1 text-[10px] text-slate-400 leading-relaxed border-t border-slate-700/50 pt-1">
                    {calib.advice}
                  </p>
                )}
              </div>
            )}
          </div>
        </details>
      )}

      {result.weakness_summary.length > 0 && (
        <div className="w-full rounded-xl bg-muted/60 p-2.5 text-left">
          <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            下次多留意
          </p>
          <ul className="mt-1 flex flex-wrap gap-1.5">
            {result.weakness_summary.map((w) => (
              <li
                key={w.tag}
                className="rounded-md bg-rose-500/10 border border-rose-500/30 px-2 py-0.5 text-[11px] font-semibold text-rose-300"
              >
                {w.label} ×{w.count}
              </li>
            ))}
          </ul>
        </div>
      )}

      <button
        type="button"
        onClick={onRestart}
        className="mt-1 w-full rounded-xl bg-foreground py-2.5 text-sm font-bold text-background hover:bg-slate-200 transition-colors"
      >
        再來一輪 ›
      </button>
      <a href="/" className="text-xs text-muted-foreground hover:underline">
        回首頁
      </a>
    </div>
  )
}
