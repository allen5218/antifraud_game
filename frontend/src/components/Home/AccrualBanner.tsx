import { useClaimAccrual, useEconomyMe } from "@/hooks/useEconomy"

export function AccrualBanner() {
  const { data } = useEconomyMe()
  const pending = data?.pending_accrual ?? 0
  const { mutate: claim, isPending } = useClaimAccrual()

  if (pending <= 0) return null

  return (
    <div className="mb-3 flex items-center justify-between rounded-xl border border-green-300 bg-green-50 px-3 py-2 text-xs">
      <span>
        🏠 你不在的時候房子收了 <b>+${pending.toLocaleString()}</b>
      </span>
      <button
        type="button"
        onClick={() => claim()}
        disabled={isPending}
        className="rounded-full bg-green-600 px-3 py-1 text-[10px] font-bold text-white disabled:opacity-50"
      >
        領取
      </button>
    </div>
  )
}
