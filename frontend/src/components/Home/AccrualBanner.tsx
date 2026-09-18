import { useClaimAccrual, useEconomyMe } from "@/hooks/useEconomy"

export function AccrualBanner() {
  const { data } = useEconomyMe()
  const pending = data?.pending_accrual ?? 0
  const { mutate: claim, isPending } = useClaimAccrual()

  if (pending <= 0) return null

  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/20 bg-slate-900/80 p-3.5 shadow-[0_0_20px_rgba(255,255,255,0.06)] backdrop-blur-xl transition-all hover:border-white/40">
      <div className="relative flex items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/20 bg-white/5 text-sm font-bold text-white shadow-[0_0_10px_rgba(255,255,255,0.05)]">
            房產
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              名下房產離線收益
            </div>
            <div className="text-sm font-bold text-white">
              累積資產收益 <span className="font-mono text-base text-emerald-400">+${pending.toLocaleString()}</span>
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={() => claim()}
          disabled={isPending}
          className="relative shrink-0 rounded-xl border border-white/30 bg-white px-4 py-2 text-xs font-bold text-slate-950 shadow-[0_0_15px_rgba(255,255,255,0.15)] transition-all hover:bg-slate-100 active:scale-95 disabled:opacity-50"
        >
          {isPending ? "領取中..." : "立即領取"}
        </button>
      </div>
    </div>
  )
}

