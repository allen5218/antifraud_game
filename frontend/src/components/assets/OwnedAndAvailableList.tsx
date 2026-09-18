import { useState } from "react"
import type { PropertyTierPublic } from "@/client"
import { useBuyProperty, useEconomyMe, useProperties } from "@/hooks/useEconomy"
import { HouseTaskModal } from "./HouseTaskModal"
import { MyHomeSection } from "./MyHomeSection"
import { PropertyCard } from "./PropertyCard"
import { VehicleSection } from "./VehicleSection"

export function OwnedAndAvailableList() {
  const { data: me } = useEconomyMe()
  const { data: propData } = useProperties()
  const { mutate: buyProperty } = useBuyProperty()
  const [houseTaskOpen, setHouseTaskOpen] = useState(false)
  const [pendingTierId, setPendingTierId] = useState<number | null>(null)

  const cash = me?.cash ?? 0
  const level = me?.level ?? 1
  const tiers = propData?.tiers ?? []
  const owned = propData?.owned ?? []

  const handleBuy = (tierId: number) => {
    // 尚未持有任何房產的新購屋者，先開啟購屋查證任務
    if (owned.length === 0) {
      setPendingTierId(tierId)
      setHouseTaskOpen(true)
      return
    }
    buyProperty(tierId)
  }

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
            已擁有房產
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

      {/* 我的家園生活裝飾展示區 */}
      <MyHomeSection />

      {/* 代步車輛資產區 */}
      <VehicleSection />

      <div className="mb-1 mt-4 text-[10px] uppercase tracking-wider text-muted-foreground">
        可購買房產
      </div>
      <div className="flex flex-col gap-2">
        {tiers.map((tier) => (
          <PropertyCard
            key={tier.id}
            tier={tier}
            locked={level < tier.unlock_level}
            affordable={cash >= tier.price}
            onBuy={() => handleBuy(tier.id)}
          />
        ))}
      </div>

      <HouseTaskModal
        open={houseTaskOpen}
        onClose={() => setHouseTaskOpen(false)}
        onSuccessBuy={() => {
          if (pendingTierId) {
            buyProperty(pendingTierId)
            setPendingTierId(null)
          }
        }}
      />
    </>
  )
}
