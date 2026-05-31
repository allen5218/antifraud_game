import type { PropertyTierPublic } from "@/client"
import { useBuyProperty, useEconomyMe, useProperties } from "@/hooks/useEconomy"
import { PropertyCard } from "./PropertyCard"

export function OwnedAndAvailableList() {
  const { data: me } = useEconomyMe()
  const { data: propData } = useProperties()
  const { mutate: buyProperty } = useBuyProperty()

  const cash = me?.cash ?? 0
  const level = me?.level ?? 1
  const tiers = propData?.tiers ?? []
  const owned = propData?.owned ?? []

  // 按 tier id 統計已擁有數量，直接從 owned[].tier 取得 tier 物件（避免二次查表）
  const ownedByTier = new Map<
    number,
    { tier: PropertyTierPublic; count: number }
  >()
  for (const p of owned) {
    const entry = ownedByTier.get(p.tier.id)
    if (entry) entry.count += 1
    else ownedByTier.set(p.tier.id, { tier: p.tier, count: 1 })
  }

  return (
    <>
      {ownedByTier.size > 0 && (
        <>
          <div className="mb-1 mt-2 text-[10px] uppercase tracking-wider text-muted-foreground">
            已擁有
          </div>
          <div className="flex flex-col gap-2">
            {[...ownedByTier.values()]
              .sort((a, b) => a.tier.id - b.tier.id)
              .map(({ tier, count }) => (
                <PropertyCard key={tier.id} tier={tier} count={count} />
              ))}
          </div>
        </>
      )}
      <div className="mb-1 mt-4 text-[10px] uppercase tracking-wider text-muted-foreground">
        可購買
      </div>
      <div className="flex flex-col gap-2">
        {tiers.map((tier) => (
          <PropertyCard
            key={tier.id}
            tier={tier}
            locked={level < tier.unlock_level}
            affordable={cash >= tier.price}
            onBuy={() => buyProperty(tier.id)}
          />
        ))}
      </div>
    </>
  )
}
