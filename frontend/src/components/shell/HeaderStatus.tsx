import { Link } from "@tanstack/react-router"
import { useEconomyMe } from "@/hooks/useEconomy"

export function HeaderStatus() {
  const { data, isPending, isError } = useEconomyMe()
  const hasData = !isPending && !isError && !!data
  const cash = hasData ? data.cash : null
  const streakDays = hasData ? data.streak_days : null
  const level = hasData ? Math.min(data.level ?? 1, 10) : null
  const cashTextColor = cash !== null && cash < 0 ? "text-red-400" : "text-emerald-400"

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between border-b-[1.5px] border-white/20 bg-slate-900/95 backdrop-blur-2xl px-4 py-3 sm:pt-6">
      <div className="flex items-center gap-2">
        <img
          src="/assets/images/brand-icon-transparent.png"
          alt="反詐大師"
          className="h-6 w-auto object-contain drop-shadow-[0_0_10px_rgba(255,255,255,0.35)]"
        />
        <span className="font-bold text-sm tracking-wide text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.2)]">
          反詐大師
        </span>
      </div>
      <div className="flex items-center gap-1.5 text-xs font-mono">
        <Link
          to="/assets"
          data-testid="hdr-cash"
          className={`flex items-center gap-1 rounded-full border-[1.5px] border-white/25 bg-white/10 px-2.5 py-1 glow-badge transition-all hover:border-white/50 ${cashTextColor}`}
        >
          <span className="text-[10px] text-slate-300 font-sans">資產</span>
          <span className="font-bold">
            {cash !== null ? `$${cash.toLocaleString()}` : "—"}
          </span>
        </Link>
        <span className="flex items-center gap-1 rounded-full border-[1.5px] border-white/25 bg-white/10 px-2.5 py-1 text-slate-100 glow-badge">
          <span className="text-[10px] text-slate-300 font-sans">連勝</span>
          <span className="font-bold">{streakDays !== null ? streakDays : "—"}</span>
        </span>
        <span className="flex items-center gap-1 rounded-full border-[1.5px] border-white/25 bg-white/10 px-2.5 py-1 text-slate-100 glow-badge">
          <span className="font-bold">{level !== null ? `Lv.${level}` : "—"}</span>
        </span>
      </div>
    </header>
  )
}
