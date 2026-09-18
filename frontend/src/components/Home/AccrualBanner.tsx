import { useClaimAccrual, useEconomyMe } from "@/hooks/useEconomy"

export function AccrualBanner() {
  const { data } = useEconomyMe()
  const pending = data?.pending_accrual ?? 0
  const { mutate: claim, isPending } = useClaimAccrual()

  if (pending <= 0) return null

  return (
    <div className="relative overflow-hidden rounded-2xl border border-amber-500/40 bg-gradient-to-r from-amber-950/80 via-yellow-900/40 to-slate-900 p-3.5 shadow-[0_0_20px_rgba(245,158,11,0.2)] backdrop-blur-md transition-all hover:border-amber-400/60">
      <div className="absolute -right-4 -top-4 h-20 w-20 rounded-full bg-amber-500/10 blur-xl" />
      <div className="relative flex items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-amber-400/40 bg-gradient-to-br from-amber-500 to-amber-700 text-xl shadow-inner">
            🏠
          </div>
          <div>
            <div className="text-[10px] font-bold uppercase tracking-wider text-amber-300/80">
              名下房產離線收益
            </div>
            <div className="text-sm font-extrabold text-amber-200">
              累積資產收益 <span className="text-amber-400 text-base">+${pending.toLocaleString()}</span>
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={() => claim()}
          disabled={isPending}
          className="relative shrink-0 overflow-hidden rounded-xl bg-gradient-to-r from-amber-500 via-amber-400 to-yellow-500 px-3.5 py-2 text-xs font-black text-slate-950 shadow-[0_0_15px_rgba(245,158,11,0.4)] transition-all hover:scale-105 active:scale-95 disabled:opacity-50"
        >
          {isPending ? "領取中..." : "💰 立即領取"}
        </button>
      </div>
    </div>
  )
}

