import { createFileRoute } from "@tanstack/react-router"
import { RoomScene } from "@/components/room/RoomScene"
import { economyMeQuery, propertiesQuery } from "@/hooks/useEconomy"
import { homeSummaryQuery } from "@/hooks/useHomeSummary"
import { warmQueries } from "@/lib/prefetch"

export const Route = createFileRoute("/_shell/")({
  // loader 不會被切到房間的程式檔裡：剛打開網站時，資料和房間的程式同時下載
  loader: ({ context: { queryClient } }) => {
    warmQueries(queryClient, [
      homeSummaryQuery,
      economyMeQuery,
      propertiesQuery,
    ])
  },
  component: Home,
})

export function Home() {
  return <RoomScene />
}
