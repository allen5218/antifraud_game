import { createFileRoute } from "@tanstack/react-router"
import { AssetSummaryCard } from "@/components/assets/AssetSummaryCard"
import { OwnedAndAvailableList } from "@/components/assets/OwnedAndAvailableList"
import {
  assetsQuery,
  economyMeQuery,
  propertiesQuery,
} from "@/hooks/useEconomy"
import { preloadImages, propertyArtSrc, warmQueries } from "@/lib/prefetch"

export const Route = createFileRoute("/_shell/assets")({
  loader: ({ context: { queryClient } }) => {
    warmQueries(queryClient, [economyMeQuery, assetsQuery])
    queryClient
      .ensureQueryData(propertiesQuery)
      .then((data) =>
        preloadImages(data.tiers.map((tier) => propertyArtSrc(tier.svg_key))),
      )
      .catch(() => {})
  },
  component: Assets,
})

function Assets() {
  return (
    <>
      <AssetSummaryCard />
      <OwnedAndAvailableList />
    </>
  )
}
