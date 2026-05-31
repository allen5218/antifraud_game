import type { PropertyTier } from "@/stores/economy"

interface Props {
  tier: PropertyTier
  count?: number
  locked?: boolean
  affordable?: boolean
  onBuy?: () => void
}

const SVG_EMOJI: Record<string, string> = {
  "tier-1": "🏚️",
  "tier-2": "🏠",
  "tier-3": "🏢",
  "tier-4": "🏘️",
  "tier-5": "🏡",
  "tier-6": "🏰",
}

export function PropertyCard({
  tier,
  count,
  locked,
  affordable,
  onBuy,
}: Props) {
  const owned = count !== undefined
  return (
    <div className="flex items-center gap-3 rounded-xl border bg-card p-2 text-xs">
      <div
        aria-hidden="true"
        className="flex h-11 w-11 items-center justify-center rounded-lg bg-muted text-2xl"
      >
        {SVG_EMOJI[tier.svgKey]}
      </div>
      <div className="flex-1">
        <h5 className="text-xs font-bold">
          {tier.name}
          {owned ? ` ×${count}` : ""}
        </h5>
        {locked ? (
          <div className="text-[10px] text-red-600">
            🔒 Lv.{tier.unlockLevel} 解鎖
          </div>
        ) : owned ? (
          <div className="text-[10px] font-bold text-green-600">
            +${tier.dailyIncome}/日
          </div>
        ) : (
          <div className="text-[10px] text-muted-foreground">
            ${tier.price.toLocaleString()} · +${tier.dailyIncome}/日
          </div>
        )}
      </div>
      {!owned && (
        <button
          type="button"
          disabled={locked || !affordable}
          onClick={onBuy}
          className={`rounded-lg px-2.5 py-1 text-[10px] font-bold ${
            locked
              ? "bg-muted text-muted-foreground"
              : !affordable
                ? "bg-red-100 text-red-700"
                : "bg-primary text-primary-foreground"
          }`}
        >
          {locked ? "未解鎖" : !affordable ? "現金不足" : "購買"}
        </button>
      )}
      {owned && (
        <span className="rounded-lg bg-muted px-2.5 py-1 text-[10px] text-muted-foreground">
          已有
        </span>
      )}
    </div>
  )
}
