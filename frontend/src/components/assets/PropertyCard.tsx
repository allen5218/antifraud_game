import {
  Building,
  Building2,
  Castle,
  Home,
  Lock,
  Warehouse,
} from "lucide-react"
import type { PropertyTierPublic } from "@/client"

interface Props {
  tier: PropertyTierPublic
  count?: number
  locked?: boolean
  affordable?: boolean
  onBuy?: () => void
}

function getPropertyIcon(svgKey: string) {
  switch (svgKey) {
    case "tier-1":
      return <Warehouse className="w-5 h-5 text-slate-300" />
    case "tier-2":
      return <Home className="w-5 h-5 text-slate-300" />
    case "tier-3":
      return <Building className="w-5 h-5 text-slate-300" />
    case "tier-4":
      return <Building2 className="w-5 h-5 text-slate-300" />
    case "tier-5":
      return <Home className="w-5 h-5 text-emerald-400" />
    case "tier-6":
      return <Castle className="w-5 h-5 text-amber-400" />
    default:
      return <Home className="w-5 h-5 text-slate-300" />
  }
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
        className="flex h-11 w-11 items-center justify-center rounded-lg bg-muted"
      >
        {getPropertyIcon(tier.svg_key)}
      </div>
      <div className="flex-1">
        <h5 className="text-xs font-bold">
          {tier.name}
          {owned ? ` ×${count}` : ""}
        </h5>
        {locked ? (
          <div className="text-[10px] text-red-600 flex items-center gap-1">
            <Lock className="w-3 h-3" />
            <span>Lv.{tier.unlock_level} 解鎖</span>
          </div>
        ) : owned ? (
          <div className="text-[10px] font-bold text-green-600">
            +${tier.daily_income}/日
          </div>
        ) : (
          <div className="text-[10px] text-muted-foreground">
            ${tier.price.toLocaleString()} · +${tier.daily_income}/日
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
