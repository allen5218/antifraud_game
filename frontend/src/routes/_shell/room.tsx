import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { EstatePage } from "@/components/estate/EstatePage"
import { showsRoomScene } from "@/components/estate/roomView"
import { RoomScene } from "@/components/room/RoomScene"
import { currentUserQuery } from "@/hooks/useAuth"
import { economyMeQuery } from "@/hooks/useEconomy"
import { estateQuery } from "@/hooks/useEstate"
import { homeSummaryQuery, useHomeSummary } from "@/hooks/useHomeSummary"
import { warmQueries } from "@/lib/prefetch"

type RoomSearch = { tour?: 1; view?: "house" }

/**
 * 分頁「經營」：放置經營（房產自己收租）。
 * 「我的家」（`?view=house`）、新手導覽（還沒看過或 `?tour=1`）和年長者仍是原本的房間。
 */
export const Route = createFileRoute("/_shell/room")({
  loader: ({ context: { queryClient } }) => {
    // GET /estate 會把經理收的租金入帳，但不建立牌局也不開始計時，可以先載入
    warmQueries(queryClient, [homeSummaryQuery, economyMeQuery, estateQuery])
  },
  validateSearch: (search: Record<string, unknown>): RoomSearch => ({
    ...(search.tour ? { tour: 1 as const } : {}),
    ...(search.view === "house" ? { view: "house" as const } : {}),
  }),
  component: RoomRoute,
})

function RoomRoute() {
  const { tour, view } = Route.useSearch()
  const { data: user } = useQuery(currentUserQuery)
  const { data: home } = useHomeSummary()
  if (!user) return null
  if (
    showsRoomScene({
      elder: user.elder_mode === true,
      tour,
      view,
      tourPending: home?.tour_pending,
    })
  ) {
    return <RoomScene />
  }
  return <EstatePage />
}
