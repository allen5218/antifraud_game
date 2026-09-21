import { useAssets } from "@/hooks/useEconomy"

export function AssetSummaryCard() {
  const { data } = useAssets()
  const cash = data?.cash ?? 0
  const propertyValue = data?.property_value ?? 0
  const dailyIncome = data?.daily_income ?? 0
  const totalNetWorth = data?.total_net_worth ?? 0
  const ownedCount = data?.owned_count ?? 0

  return (
    <div className="rounded-2xl border border-white/15 bg-slate-900/80 p-4 shadow-[0_0_15px_rgba(255,255,255,0.04)] backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <div>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            總身家
          </span>
          <div className="text-xl font-mono font-bold text-white mt-0.5">
            ${totalNetWorth.toLocaleString()}
          </div>
        </div>
        <div className="text-right">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            每日被動收益
          </span>
          <div className="text-sm font-mono font-bold text-emerald-400 mt-0.5">
            + $ {dailyIncome.toLocaleString()}/天
          </div>
        </div>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
        <div className="flex items-center justify-between rounded-xl border border-white/5 bg-white/5 px-3 py-2">
          <span className="text-slate-400 text-[11px]">現金</span>
          <span className="font-mono font-bold text-slate-200">
            ${cash.toLocaleString()}
          </span>
        </div>
        <div className="flex items-center justify-between rounded-xl border border-white/5 bg-white/5 px-3 py-2">
          <span className="text-slate-400 text-[11px]">
            房產 ({ownedCount})
          </span>
          <span className="font-mono font-bold text-slate-200">
            ${propertyValue.toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  )
}
