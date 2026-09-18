import { Link } from "@tanstack/react-router"
import { useEconomyMe } from "@/hooks/useEconomy"

export function HeaderStatus() {
  const { data } = useEconomyMe()
  const cash = data?.cash ?? 0
  const streakDays = data?.streak_days ?? 0
  const cashColor = cash < 0 ? "text-red-400 bg-red-950/80 border-red-500/40" : "text-emerald-400 bg-emerald-950/60 border-emerald-500/30 shadow-[0_0_12px_rgba(16,185,129,0.2)]"

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between border-b border-slate-800/80 bg-slate-900/90 backdrop-blur-md px-4 py-3 sm:pt-6">
      <div className="flex items-center gap-2">
        <span className="text-xl">🛡️</span>
        <span className="font-extrabold text-sm tracking-wider bg-gradient-to-r from-emerald-400 to-sky-400 bg-clip-text text-transparent">
          反詐大師
        </span>
      </div>
      <div className="flex items-center gap-1.5 text-xs font-mono">
        <Link
          to="/assets"
          data-testid="hdr-cash"
          className={`flex items-center gap-1 rounded-full border px-2.5 py-1 transition-all hover:scale-105 ${cashColor}`}
        >
          <span>💰</span>
          <span className="font-bold">${cash.toLocaleString()}</span>
        </Link>
        <span className="flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-950/60 text-amber-300 px-2.5 py-1">
          <span>🔥</span>
          <span className="font-bold">{streakDays}</span>
        </span>
        <span className="flex items-center gap-1 rounded-full border border-indigo-500/30 bg-indigo-950/60 text-indigo-300 px-2.5 py-1">
          <span>⭐</span>
          <span className="font-bold">
            Lv.{Math.min(data?.level ?? 1, 10)}
          </span>
        </span>
      </div>
    </header>
  )
}
