import { Skeleton } from "@/components/ui/skeleton"
import { useAssets } from "@/hooks/useEconomy"

export function AssetSummaryCard() {
  const { data } = useAssets()
  // 還沒讀到時不要先顯示「$ 0」，看起來像錢不見了
  if (!data) {
    return (
      <div
        data-testid="asset-summary-loading"
        className="mb-3 flex flex-col gap-2 rounded-2xl border bg-surface-3 p-3"
      >
        <Skeleton className="h-3 w-12" />
        <Skeleton className="h-7 w-32" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-full" />
      </div>
    )
  }
  const cash = data?.cash ?? 0
  const propertyValue = data?.property_value ?? 0
  const dailyIncome = data?.daily_income ?? 0
  const totalNetWorth = data?.total_net_worth ?? 0
  const ownedCount = data?.owned_count ?? 0

  return (
    <div className="mb-3 rounded-2xl border bg-surface-3 p-3 text-card-foreground">
      <div className="text-[10px] opacity-70">總身家</div>
      <div className="text-xl font-extrabold">
        $ {totalNetWorth.toLocaleString()}
      </div>
      <div className="mt-1 flex justify-between text-[11px]">
        <span>現金</span>
        <span>$ {cash.toLocaleString()}</span>
      </div>
      <div className="flex justify-between text-[11px]">
        <span>房產（{ownedCount} 間）</span>
        <span>$ {propertyValue.toLocaleString()}</span>
      </div>
      <div className="flex justify-between text-[11px]">
        <span>每日被動收入</span>
        <span className="text-legit">
          + $ {dailyIncome.toLocaleString()} / 天
        </span>
      </div>
    </div>
  )
}
