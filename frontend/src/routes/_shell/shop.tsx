import { createFileRoute } from "@tanstack/react-router"
import { mascotItemsQuery } from "@/components/shop/mascotApi"
import { ShopPage } from "@/components/shop/ShopPage"
import { economyMeQuery, propertiesQuery } from "@/hooks/useEconomy"
import { preloadImages, propertyArtSrc, warmQueries } from "@/lib/prefetch"

export const Route = createFileRoute("/_shell/shop")({
  loader: ({ context: { queryClient } }) => {
    warmQueries(queryClient, [economyMeQuery])
    // 商店卡片的圖跟著清單一起先抓，進頁面時不會一張張冒出來
    queryClient
      .ensureQueryData(mascotItemsQuery)
      .then((data) => preloadImages(data.items.map((item) => item.image_url)))
      .catch(() => {})
    queryClient
      .ensureQueryData(propertiesQuery)
      .then((data) =>
        preloadImages(data.tiers.map((tier) => propertyArtSrc(tier.svg_key))),
      )
      .catch(() => {})
  },
  component: ShopPage,
})
