import { useAssets } from "@/hooks/useEconomy"

export function AssetSummaryCard() {
  const { data } = useAssets()
  const cash = data?.cash ?? 0
  const propertyValue = data?.property_value ?? 0
  const dailyIncome = data?.daily_income ?? 0
  const totalNetWorth = data?.total_net_worth ?? 0
  const ownedCount = data?.owned_count ?? 0

  return (
    <div className="mb-3 rounded-2xl bg-slate-800 p-3 text-white">
      <div className="text-[10px] opacity-70">總身家</div>
      <div className="text-xl font-extrabold">
        $ {totalNetWorth.toLocaleString()}
      </div>
      <div className="mt-1 flex justify-between text-[11px]">
        <span>現金</span>
        <span>$ {cash.toLocaleString()}</span>
      </div>
      <div className="flex justify-between text-[11px]">
        <span>房產 ({ownedCount} 間)</span>
        <span>$ {propertyValue.toLocaleString()}</span>
      </div>
      <div className="flex justify-between text-[11px]">
        <span>每日被動收入</span>
        <span className="text-green-400">
          + $ {dailyIncome.toLocaleString()} / 天
        </span>
      </div>
    </div>
  )
}
