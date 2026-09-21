import { Building2 } from "lucide-react"
import { useClaimAccrual, useEconomyMe } from "@/hooks/useEconomy"

export function AccrualBanner() {
  const { data } = useEconomyMe()
  const pending = data?.pending_accrual ?? 0
  const { mutate: claim, isPending } = useClaimAccrual()

  if (pending <= 0) return null

  return (
    <div className="flex items-center justify-between rounded-2xl border border-white/15 bg-slate-900/80 px-4 py-3 shadow-[0_0_15px_rgba(255,255,255,0.04)] backdrop-blur-xl">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-white/15 bg-white/5 text-emerald-400">
          <Building2 className="size-4" />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-300">
            房產離線收益
          </span>
          <span className="font-mono text-sm font-bold text-emerald-400">
            +${pending.toLocaleString()}
          </span>
        </div>
      </div>
      <button
        type="button"
        onClick={() => claim()}
        disabled={isPending}
        className="rounded-xl border border-white/20 bg-white px-3.5 py-1.5 text-xs font-bold text-slate-950 transition-all hover:bg-slate-200 active:scale-95 disabled:opacity-50"
      >
        {isPending ? "領取中" : "領取"}
      </button>
    </div>
  )
}
