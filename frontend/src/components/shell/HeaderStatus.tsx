import { Link } from "@tanstack/react-router"
import { useEconomyMe } from "@/hooks/useEconomy"

export function HeaderStatus() {
  const { data } = useEconomyMe()
  const cash = data?.cash ?? 0
  const streakDays = data?.streak_days ?? 0
  const cashTextColor = cash < 0 ? "text-red-400" : "text-emerald-400"

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between border-b border-white/10 bg-slate-900/90 backdrop-blur-xl px-4 py-3 sm:pt-6">
      <div className="flex items-center gap-2">
        <img
          src="/assets/images/brand-icon-transparent.png"
          alt="反詐大師"
          className="h-6 w-auto object-contain drop-shadow-[0_0_8px_rgba(255,255,255,0.25)]"
        />
        <span className="font-bold text-sm tracking-wide text-white">
          反詐大師
        </span>
      </div>
      <div className="flex items-center gap-1.5 text-xs font-mono">
        <Link
          to="/assets"
          data-testid="hdr-cash"
          className="flex items-center gap-1 rounded-full border border-white/20 bg-white/5 px-2.5 py-1 shadow-[0_0_10px_rgba(255,255,255,0.05)] transition-all hover:border-white/40"
        >
          <span className="text-[10px] text-slate-400 font-sans">資產</span>
          <span className={`font-bold ${cashTextColor}`}>${cash.toLocaleString()}</span>
        </Link>
        <span className="flex items-center gap-1 rounded-full border border-white/20 bg-white/5 px-2.5 py-1 text-slate-200 shadow-[0_0_10px_rgba(255,255,255,0.05)]">
          <span className="text-[10px] text-slate-400 font-sans">連勝</span>
          <span className="font-bold">{streakDays}</span>
        </span>
        <span className="flex items-center gap-1 rounded-full border border-white/20 bg-white/5 px-2.5 py-1 text-slate-200 shadow-[0_0_10px_rgba(255,255,255,0.05)]">
          <span className="font-bold">
            Lv.{Math.min(data?.level ?? 1, 10)}
          </span>
        </span>
      </div>
    </header>
  )
}
