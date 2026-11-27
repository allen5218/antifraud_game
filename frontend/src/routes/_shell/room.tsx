import { createFileRoute } from "@tanstack/react-router"
import { RoomScene } from "@/components/room/RoomScene"
import { economyMeQuery, propertiesQuery } from "@/hooks/useEconomy"
import { homeSummaryQuery } from "@/hooks/useHomeSummary"
import { warmQueries } from "@/lib/prefetch"

/** 房間（分頁「經營」）：房產、吉祥物、商店與所有舊玩法的入口，新手導覽也在這裡。 */
export const Route = createFileRoute("/_shell/room")({
  loader: ({ context: { queryClient } }) => {
    warmQueries(queryClient, [
      homeSummaryQuery,
      economyMeQuery,
      propertiesQuery,
    ])
  },
  // 選單「重看導覽」帶 ?tour=1
  validateSearch: (search: Record<string, unknown>): { tour?: 1 } =>
    search.tour ? { tour: 1 } : {},
  component: RoomScene,
})
