import { useEconomyStore } from "@/stores/economy"

export function AssetSummaryCard() {
  const cash = useEconomyStore((s) => s.cash)
  const owned = useEconomyStore((s) => s.ownedProperties)
  const propertyValue = owned.reduce((sum, p) => sum + p.tier.price, 0)
  const dailyIncome = owned.reduce((sum, p) => sum + p.tier.dailyIncome, 0)
  const total = cash + propertyValue

  return (
    <div className="mb-3 rounded-2xl bg-slate-800 p-3 text-white">
      <div className="text-[10px] opacity-70">總身家</div>
      <div className="text-xl font-extrabold">$ {total.toLocaleString()}</div>
      <div className="mt-1 flex justify-between text-[11px]">
        <span>現金</span>
        <span>$ {cash.toLocaleString()}</span>
      </div>
      <div className="flex justify-between text-[11px]">
        <span>房產 ({owned.length} 間)</span>
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
