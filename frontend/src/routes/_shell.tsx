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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-0 sm:p-4 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900/80 via-slate-950 to-slate-950">
      <div className="relative w-full max-w-lg md:max-w-xl h-dvh sm:h-[840px] sm:max-h-[calc(100vh-2rem)] flex flex-col bg-slate-900/95 backdrop-blur-2xl border-0 sm:border-[1.5px] border-white/25 sm:rounded-3xl glow-shell overflow-hidden">
        <HeaderStatus />
        <main className="flex-1 overflow-y-auto p-4 space-y-3.5">
          <Outlet />
        </main>
        <BottomTabs />
        <ForcedSellModal />
      </div>
    </div>
  )
}
