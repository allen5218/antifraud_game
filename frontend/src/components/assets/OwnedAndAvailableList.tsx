import { MOCK_TIERS, useEconomyStore } from "@/stores/economy"
import { PropertyCard } from "./PropertyCard"

export function OwnedAndAvailableList() {
  const cash = useEconomyStore((s) => s.cash)
  const level = useEconomyStore((s) => s.level)
  const owned = useEconomyStore((s) => s.ownedProperties)

  const ownedByTier = owned.reduce<Map<number, number>>((m, p) => {
    m.set(p.tier.id, (m.get(p.tier.id) ?? 0) + 1)
    return m
  }, new Map())

  return (
    <>
      {ownedByTier.size > 0 && (
        <>
          <div className="mb-1 mt-2 text-[10px] uppercase tracking-wider text-muted-foreground">
            已擁有
          </div>
          <div className="flex flex-col gap-2">
            {[...ownedByTier]
              .sort(([a], [b]) => a - b)
              .map(([tierId, count]) => {
                const tier = MOCK_TIERS.find((t) => t.id === tierId)
                if (!tier) return null
                return <PropertyCard key={tierId} tier={tier} count={count} />
              })}
          </div>
        </>
      )}
      <div className="mb-1 mt-4 text-[10px] uppercase tracking-wider text-muted-foreground">
        可購買
      </div>
      <div className="flex flex-col gap-2">
        {MOCK_TIERS.map((tier) => (
          <PropertyCard
            key={tier.id}
            tier={tier}
            locked={level < tier.unlockLevel}
            affordable={cash >= tier.price}
          />
        ))}
      </div>
    </>
  )
}
