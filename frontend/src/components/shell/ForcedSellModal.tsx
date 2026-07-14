import { useMemo, useState } from "react"
import { useEconomyMe, useLiquidate, useProperties } from "@/hooks/useEconomy"
import { LIQUIDATION_RATIO } from "@/lib/economy"

export function ForcedSellModal() {
  const { data: me } = useEconomyMe()
  const { data: propData } = useProperties()
  const { mutate: liquidate } = useLiquidate()
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [dismissed, setDismissed] = useState(false)

  const cash = me?.cash ?? 0
  const pending = me?.bankruptcy_pending ?? false
  const owned = propData?.owned ?? []

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
  // 全部變賣也補不了缺口（含完全沒有房產）→ 提供答題還債的逃生路徑
  const maxRecoverable = useMemo(
    () =>
      owned.reduce(
        (sum, p) => sum + Math.floor(p.tier.price * LIQUIDATION_RATIO),
        0,
      ),
    [owned],
  )
  const insufficientAssets = maxRecoverable < deficit
  // 資產不足時允許賣掉手上有的（部分清償）；任何情況都不允許空選送出
  const canConfirm =
    selected.size > 0 && (recovered >= deficit || insufficientAssets)

  // 只有「真的破產」（flag 且現金為負）才顯示；避免 DB 手動改現金後
  // 殘留的 bankruptcy_pending 造成 $0 缺口的空視窗
  const isActuallyBankrupt = pending && cash < 0
  if (!isActuallyBankrupt || dismissed) return null

  const toggle = (id: string) =>
    setSelected((s) => {
      const next = new Set(s)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })

  const confirm = () => {
    liquidate([...selected], {
      onSuccess: () => setSelected(new Set()),
    })
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
        {owned.length === 0 ? (
          <div
            data-testid="no-assets-notice"
            className="mb-2 rounded-lg border border-border bg-muted px-2 py-2 text-[11px] text-muted-foreground"
          >
            你目前沒有可變賣的房產。別擔心——完成題組與滑卡訓練獲得的獎金
            會自動用來償還欠款，還清後即可恢復正常遊戲。
          </div>
        ) : (
          <div className="mb-2 text-[10px] text-muted-foreground">
            選擇要變賣的房產：
            {insufficientAssets && (
              <span className="text-red-700">
                （全部變賣仍不足，可先部分清償，剩餘欠款以答題獎金償還）
              </span>
            )}
          </div>
        )}
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
          <div className="flex items-center gap-2">
            {insufficientAssets && (
              <button
                type="button"
                data-testid="go-earn-btn"
                onClick={() => setDismissed(true)}
                className="rounded-lg border border-border bg-muted px-3 py-1.5 text-xs font-bold"
              >
                先去答題還債
              </button>
            )}
            {owned.length > 0 && (
              <button
                type="button"
                disabled={!canConfirm}
                onClick={confirm}
                className="rounded-lg bg-red-700 px-3 py-1.5 text-xs font-bold text-white disabled:opacity-50"
              >
                確認變賣
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
