import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { LearnHome } from "@/components/learn/LearnHome"
import { RoomScene } from "@/components/room/RoomScene"
import { currentUserQuery } from "@/hooks/useAuth"
import { cardSummaryQuery } from "@/hooks/useCards"
import { economyMeQuery, propertiesQuery } from "@/hooks/useEconomy"
import { homeSummaryQuery } from "@/hooks/useHomeSummary"
import { warmQueries } from "@/lib/prefetch"

export const Route = createFileRoute("/_shell/")({
  // loader 不會被切到房間的程式檔裡：剛打開網站時，資料和畫面的程式同時下載
  loader: ({ context: { queryClient } }) => {
    warmQueries(queryClient, [
      currentUserQuery,
      homeSummaryQuery,
      cardSummaryQuery,
      economyMeQuery,
      propertiesQuery,
    ])
  },
  // 舊版選單「重看導覽」帶 ?tour=1 回首頁；現在導覽在房間（/room）
  validateSearch: (search: Record<string, unknown>): { tour?: 1 } =>
    search.tour ? { tour: 1 } : {},
  component: Home,
})

/**
 * 首頁：一般模式是 Lingvist 式的練習首頁；50 歲以上的年長者介面還沒做好前先維持房間。
 * 舊連結帶 ?tour=1 的直接開房間看導覽。
 */
export function Home() {
  const { data: user } = useQuery(currentUserQuery)
  const { tour } = Route.useSearch()
  if (!user) return null
  if (user.elder_mode || tour) return <RoomScene />
  return <LearnHome />
}
