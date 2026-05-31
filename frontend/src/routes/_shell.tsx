import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"
import { BottomTabs } from "@/components/shell/BottomTabs"
import { ForcedSellModal } from "@/components/shell/ForcedSellModal"
import { HeaderStatus } from "@/components/shell/HeaderStatus"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/_shell")({
  component: Shell,
  beforeLoad: async () => {
    if (!isLoggedIn()) throw redirect({ to: "/login" })
  },
})

function Shell() {
  return (
    <div className="mx-auto flex h-dvh max-w-md flex-col bg-background">
      <HeaderStatus />
      <main className="flex-1 overflow-y-auto p-4">
        <Outlet />
      </main>
      <BottomTabs />
      <ForcedSellModal />
    </div>
  )
}
