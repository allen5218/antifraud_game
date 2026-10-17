import { useState } from "react"
import type { MascotShopItem } from "./mascotApi"

export function MascotCard({
  item,
  error,
  pending,
  onBuy,
  onDisplay,
}: {
  item: MascotShopItem
  error?: string
  pending?: boolean
  onBuy: () => void
  onDisplay: () => void
}) {
  const [broken, setBroken] = useState(false)
  const label = item.displayed ? "展示中" : item.owned ? "展示" : "購買"
  return (
    <article className="flex flex-col gap-2 rounded-xl border bg-card p-3">
      {broken ? (
        <div
          aria-hidden="true"
          className="aspect-square w-full rounded-lg bg-surface-2"
        />
      ) : (
        <img
          src={item.image_url}
          alt=""
          aria-hidden="true"
          width={160}
          height={160}
          loading="lazy"
          onError={() => setBroken(true)}
          className="aspect-square w-full rounded-lg bg-surface-2 object-cover"
        />
      )}
      <h3 className="text-sm font-bold">{item.name}</h3>
      <p className="text-xs text-muted-foreground">
        {item.cost > 0 ? `$${item.cost.toLocaleString()}` : "免費"}
      </p>
      {error ? <p className="text-xs font-bold text-scam">{error}</p> : null}
      <button
        type="button"
        disabled={item.displayed || pending}
        onClick={() => (item.owned ? onDisplay() : onBuy())}
        className="rounded-lg bg-primary px-2.5 py-1.5 text-xs font-bold text-primary-foreground disabled:bg-muted disabled:text-muted-foreground"
      >
        {label}
      </button>
    </article>
  )
}
