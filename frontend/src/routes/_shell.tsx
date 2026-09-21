import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"
import { BottomTabs } from "@/components/shell/BottomTabs"
import { ForcedSellModal } from "@/components/shell/ForcedSellModal"
import { HeaderStatus } from "@/components/shell/HeaderStatus"
import { NavRail } from "@/components/shell/NavRail"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/_shell")({
  component: Shell,
  beforeLoad: async () => {
    if (!isLoggedIn()) throw redirect({ to: "/login" })
  },
})

function Shell() {
  return (
    // 手機:頂欄 + 捲動內容 + 底部分頁(拇指可及)。
    // 桌機(md 以上):左側導覽 + 寬內容區——底部分頁橫跨整個桌機螢幕會很怪,
    // 而原本的 max-w-md 會讓桌機只剩中間一條窄欄、兩側全空。
    <div className="mx-auto flex h-dvh w-full max-w-md bg-background md:max-w-6xl">
      <NavRail />
      <div className="flex min-w-0 flex-1 flex-col">
        <HeaderStatus />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
        <BottomTabs />
      </div>
      <ForcedSellModal />
    </div>
  )
}
