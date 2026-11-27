import { useQuery } from "@tanstack/react-query"
import {
  createFileRoute,
  Outlet,
  redirect,
  useRouterState,
} from "@tanstack/react-router"
import { BirthYearGate } from "@/components/shell/BirthYearGate"
import { ForcedSellModal } from "@/components/shell/ForcedSellModal"
import { NavRail } from "@/components/shell/NavRail"
import { PageHeader, pageTitle } from "@/components/shell/PageHeader"
import { showsTabBar, TabBar } from "@/components/shell/TabBar"
import { currentUserQuery, isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/_shell")({
  component: Shell,
  beforeLoad: async () => {
    if (!isLoggedIn()) throw redirect({ to: "/login" })
  },
})

function Shell() {
  // 用已經載入完成的網址：點了別頁、那頁還在載入時，頁首與內距先不換，房間不會被擠下去
  const pathname = useRouterState({
    select: (state) => (state.resolvedLocation ?? state.location).pathname,
  })
  const { data: user } = useQuery({
    ...currentUserQuery,
    enabled: isLoggedIn(),
  })
  const elder = user?.elder_mode === true
  // 房間鋪滿整個畫面：一般模式在 /room（分頁「經營」）；年長者介面做好前，年長者的首頁也是房間
  const isRoom = pathname === "/room" || (pathname === "/" && elder)
  const tabs = !elder && showsTabBar(pathname)
  return (
    // 桌機左側 NavRail；手機在四個分頁的頁面有底部分頁（年長者沒有）。
    // 首頁與房間不加頂欄；其他頁用頁首的「回首頁」。
    <div
      className="mx-auto flex h-dvh w-full max-w-md bg-background md:max-w-6xl"
      // 加到主畫面後內容會畫到瀏海與底部橫條底下；房間自己處理（牆畫到邊、按鈕避開），
      // 底部分頁自己留底部的內距，其他頁留內距
      style={
        isRoom
          ? undefined
          : {
              paddingTop: "env(safe-area-inset-top)",
              paddingBottom: tabs ? undefined : "env(safe-area-inset-bottom)",
            }
      }
    >
      <NavRail />
      <div className="flex min-w-0 flex-1 flex-col">
        {!isRoom && pathname !== "/" && (
          <PageHeader title={pageTitle(pathname)} />
        )}
        <main
          className={
            isRoom
              ? "flex-1 overflow-y-auto"
              : "flex-1 overflow-y-auto p-4 md:p-6"
          }
        >
          <Outlet />
        </main>
        {!elder && <TabBar />}
      </div>
      <ForcedSellModal />
      <BirthYearGate />
    </div>
  )
}
