import { useMemo, useState } from "react"
import { LIQUIDATION_RATIO, useEconomyStore } from "@/stores/economy"

// NOTE (Phase 1 mock): assumes the player's total liquidatable assets can cover the deficit.
// The "sold everything but still in debt" and "no assets owned" cases would leave this
// non-dismissable modal with a permanently-disabled confirm button. The real bankruptcy
// resolution (sell-all → mark bankruptcy, dismiss, keep negative cash per spec §4.5) is
// implemented in Phase 2 when this modal is wired to the economy API. The Phase-1 DEV
// trigger uses a solvable amount on purpose.
export function ForcedSellModal() {
  const cash = useEconomyStore((s) => s.cash)
  const pending = useEconomyStore((s) => s.bankruptcyPending)
  const owned = useEconomyStore((s) => s.ownedProperties)
  const liquidate = useEconomyStore((s) => s.liquidateProperties)
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const deficit = Math.abs(Math.min(0, cash))
  const recovered = useMemo(
    () =>
      owned
        .filter((p) => selected.has(p.id))
        .reduce(
          (sum, p) => sum + Math.floor(p.tier.price * LIQUIDATION_RATIO),
          0,
        ),
    [owned, selected],
  )
  const canConfirm = recovered >= deficit

  if (!pending) return null

  const toggle = (id: string) =>
    setSelected((s) => {
      const next = new Set(s)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })

  const confirm = () => {
    liquidate([...selected])
    setSelected(new Set())
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="forced-sell-title"
      className="fixed inset-0 z-50 flex items-end bg-black/50"
    >
      <div className="w-full rounded-t-2xl bg-background p-4">
        <h3
          id="forced-sell-title"
          className="mb-1 flex items-center gap-1 text-sm font-extrabold text-red-700"
        >
          ⚠️ 你被詐騙了
        </h3>
        <p className="mb-2 text-[11px] text-muted-foreground">
          在「真實情境」的對話中，你匯了款項到對方指定帳戶。
        </p>
        <div className="mb-3 rounded-lg border border-red-200 bg-red-50 px-2 py-1.5 text-[11px]">
          <b>現金不足 ${deficit.toLocaleString()}</b>
          <div className="text-muted-foreground">
            需變賣資產補足。賣價為原價 60%。
          </div>
        </div>
        <div className="mb-2 text-[10px] text-muted-foreground">
          選擇要變賣的房產：
        </div>
        <div className="flex flex-col gap-1.5">
          {owned.map((p) => {
            const sellPrice = Math.floor(p.tier.price * LIQUIDATION_RATIO)
            const isSel = selected.has(p.id)
            return (
              <label
                key={p.id}
                data-testid={`sell-row-${p.id}`}
                className={`flex items-center gap-2 rounded-lg border px-2 py-1.5 text-[11px] ${
                  isSel ? "border-red-500 bg-red-50" : "border-border bg-muted"
                }`}
              >
                <input
                  type="checkbox"
                  checked={isSel}
                  onChange={() => toggle(p.id)}
                  className="h-4 w-4"
                />
                <span aria-hidden="true" className="text-xl">
                  🏠
                </span>
                <div className="flex-1">
                  <div className="text-xs font-bold">{p.tier.name}</div>
                  <div className="text-[10px]">
                    <s className="text-muted-foreground">
                      原價 ${p.tier.price.toLocaleString()}
                    </s>
                    {" · "}
                    <span className="font-bold text-red-700">
                      回收 ${sellPrice.toLocaleString()}
                    </span>
                  </div>
                </div>
              </label>
            )
          })}
        </div>
        <div className="mt-3 flex items-center justify-between text-[11px]">
          <span>
            已勾選回收 <b>${recovered.toLocaleString()}</b> / 缺口 $
            {deficit.toLocaleString()}
          </span>
          <button
            type="button"
            disabled={!canConfirm}
            onClick={confirm}
            className="rounded-lg bg-red-700 px-3 py-1.5 text-xs font-bold text-white disabled:opacity-50"
          >
            確認變賣
          </button>
        </div>
      </div>
    </div>
  )
}
