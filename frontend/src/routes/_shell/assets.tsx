import { createFileRoute } from "@tanstack/react-router"
import { AssetSummaryCard } from "@/components/assets/AssetSummaryCard"
import { OwnedAndAvailableList } from "@/components/assets/OwnedAndAvailableList"

export const Route = createFileRoute("/_shell/assets")({
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
