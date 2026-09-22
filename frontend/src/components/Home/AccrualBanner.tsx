import { House } from "lucide-react"
import { useClaimAccrual, useEconomyMe } from "@/hooks/useEconomy"

export function AccrualBanner() {
  const { data } = useEconomyMe()
  const pending = data?.pending_accrual ?? 0
  const { mutate: claim, isPending } = useClaimAccrual()

  if (pending <= 0) return null

  return (
    // 原本寫死 border-green-300 / bg-green-50 / bg-green-600,在深色模式下會變成
    // 一塊淺綠色亮片。改用主題的 legit 語意色,兩種配色都成立。
    <div className="mb-3 flex items-center justify-between gap-2 rounded-xl border border-legit/40 bg-legit/10 px-3 py-2 text-xs">
      <span className="flex items-center gap-1.5">
        <House aria-hidden className="size-3.5 text-legit" />
        你不在的時候房子收了 <b>+${pending.toLocaleString()}</b>
      </span>
      <button
        type="button"
        onClick={() => claim()}
        disabled={isPending}
        className="shrink-0 rounded-full bg-legit px-3 py-1 text-[10px] font-bold text-legit-foreground transition hover:brightness-110 disabled:opacity-50"
      >
        領取
      </button>
    </div>
  )
}
