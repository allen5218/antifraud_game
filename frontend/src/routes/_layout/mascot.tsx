import { createFileRoute } from "@tanstack/react-router"
import { useCallback, useEffect, useState } from "react"
import { MascotService, ScoreService } from "@/client"
import { MascotPreview } from "@/components/Mascot/MascotPreview"
import { ShopItem } from "@/components/Mascot/ShopItem"

export const Route = createFileRoute("/_layout/mascot")({
  component: MascotShopPage,
  head: () => ({
    meta: [{ title: "吉祥物商店 - ScamGym 識詐練習場" }],
  }),
})

interface ShopItemData {
  id: string
  name: string
  category: string
  cost: number
  image_url: string
  owned: boolean
  equipped: boolean
}

function MascotShopPage() {
  const [items, setItems] = useState<ShopItemData[]>([])
  const [totalScore, setTotalScore] = useState(0)
  const [loading, setLoading] = useState(true)

  const loadData = useCallback(async () => {
    try {
      const [itemsData, scoreData] = await Promise.all([
        MascotService.listMascotItems(),
        ScoreService.getMyScore(),
      ])
      setItems((itemsData as any).items ?? [])
      setTotalScore((scoreData as any).total_score ?? 0)
    } catch {
      // 靜默處理
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handlePurchase = async (itemId: string) => {
    try {
      await MascotService.purchaseItem({ itemId })
      await loadData()
    } catch {
      // 靜默處理
    }
  }

  const handleToggleEquip = async (itemId: string) => {
    try {
      await MascotService.toggleEquip({ itemId })
      await loadData()
    } catch {
      // 靜默處理
    }
  }

  const equippedItems = items
    .filter((i) => i.equipped)
    .map((i) => ({ name: i.name, image_url: i.image_url }))

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold">吉祥物商店</h1>
        <p className="text-muted-foreground">
          用遊戲積分買配件，幫你的防詐小衛士換裝。
        </p>
        <p className="mt-1 text-sm font-medium">
          目前積分：<span className="text-primary">{totalScore}</span>
        </p>
      </div>

      <MascotPreview equippedItems={equippedItems} />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
        {items.map((item) => (
          <ShopItem
            key={item.id}
            name={item.name}
            category={item.category}
            cost={item.cost}
            imageUrl={item.image_url}
            owned={item.owned}
            equipped={item.equipped}
            canAfford={totalScore >= item.cost}
            onPurchase={() => handlePurchase(item.id)}
            onToggleEquip={() => handleToggleEquip(item.id)}
          />
        ))}
      </div>

      {items.length === 0 && (
        <p className="py-10 text-center text-muted-foreground">
          商店目前沒有商品。
        </p>
      )}
    </div>
  )
}
