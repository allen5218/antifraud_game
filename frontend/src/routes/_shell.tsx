import {
  createFileRoute,
  Outlet,
  redirect,
  useRouterState,
} from "@tanstack/react-router"
import { ForcedSellModal } from "@/components/shell/ForcedSellModal"
import { NavRail } from "@/components/shell/NavRail"
import { PageHeader, pageTitle } from "@/components/shell/PageHeader"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/_shell")({
  component: Shell,
  beforeLoad: async () => {
    if (!isLoggedIn()) throw redirect({ to: "/login" })
  },
})

function Shell() {
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })
  const isHome = pathname === "/"
  return (
    // 桌機左側 NavRail 保留。首頁是房間，不加頂欄與內距；其他頁用「回房間」。
    <div className="mx-auto flex h-dvh w-full max-w-md bg-background md:max-w-6xl">
      <NavRail />
      <div className="flex min-w-0 flex-1 flex-col">
        {!isHome && <PageHeader title={pageTitle(pathname)} />}
        <main
          className={
            isHome
              ? "flex-1 overflow-y-auto"
              : "flex-1 overflow-y-auto p-4 md:p-6"
          }
        >
          <Outlet />
        </main>
      </div>
      <ForcedSellModal />
    </div>
  )
}
