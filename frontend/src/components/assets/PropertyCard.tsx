import { Lock } from "lucide-react"
import type { PropertyTierPublic } from "@/client"

interface Props {
  tier: PropertyTierPublic
  count?: number
  locked?: boolean
  affordable?: boolean
  onBuy?: () => void
}

/**
 * 房產插圖。
 *
 * 原本是 emoji（常數叫 SVG_EMOJI、欄位叫 svg_key——插圖一直是原本的打算，
 * emoji 只是佔位）。emoji 在不同平台長相不同，六個等級也看不出「越換越好」的遞進。
 * 圖檔都壓成 256px WebP，整組約 40KB。
 */
function artSrc(svgKey: string): string {
  return `/assets/property/${svgKey}.webp`
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
      <img
        src={artSrc(tier.svg_key)}
        alt=""
        aria-hidden="true"
        width={56}
        height={56}
        loading="lazy"
        className={`size-14 shrink-0 rounded-lg object-cover ${
          locked ? "grayscale opacity-60" : ""
        }`}
      />
      <div className="flex-1">
        <h5 className="text-xs font-bold">
          {tier.name}
          {owned ? ` ×${count}` : ""}
        </h5>
        {locked ? (
          // 這些原本是 text-red-600 / text-green-600 / bg-red-100,在深色模式下
          // 對比不足或直接變成亮色塊;改用主題語意色,兩種配色都成立。
          <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
            <Lock aria-hidden className="size-3" />
            Lv.{tier.unlock_level} 解鎖
          </div>
        ) : owned ? (
          <div className="text-[10px] font-bold text-legit">
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
          className={`shrink-0 rounded-lg px-2.5 py-1 text-[10px] font-bold transition ${
            locked
              ? "bg-muted text-muted-foreground"
              : !affordable
                ? "bg-scam/15 text-scam"
                : "bg-primary text-primary-foreground hover:brightness-110"
          }`}
        >
          {locked ? "未解鎖" : !affordable ? "現金不足" : "購買"}
        </button>
      )}
      {owned && (
        <span className="shrink-0 rounded-lg bg-muted px-2.5 py-1 text-[10px] text-muted-foreground">
          已有
        </span>
      )}
    </div>
  )
}
