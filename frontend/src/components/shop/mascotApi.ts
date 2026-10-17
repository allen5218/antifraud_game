import { MascotService, type MascotShopItem } from "@/client"

export type { MascotShopItem }

// 「展示」沿用後端的 equip 端點：同一時間只會有一隻展示中
export const mascotApi = {
  list: () => MascotService.listMascotItems(),
  purchase: (id: string) => MascotService.purchaseItem({ itemId: id }),
  display: (id: string) => MascotService.toggleEquip({ itemId: id }),
}
