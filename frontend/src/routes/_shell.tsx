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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-0 sm:p-4 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-950/40 via-slate-950 to-slate-950">
      <div className="relative w-full max-w-md h-dvh sm:h-[880px] flex flex-col bg-slate-900/80 backdrop-blur-xl border-0 sm:border border-slate-800/80 sm:rounded-[36px] shadow-[0_0_50px_-12px_rgba(16,185,129,0.25)] overflow-hidden">
        {/* Top Camera Notch Decorator for Mobile Frame */}
        <div className="hidden sm:block absolute top-2 left-1/2 -translate-x-1/2 w-28 h-4 bg-slate-950 rounded-full z-30 border border-slate-800/50 shadow-inner" />
        
        <HeaderStatus />
        <main className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
          <Outlet />
        </main>
        <BottomTabs />
        <ForcedSellModal />
      </div>
    </div>
  )
}
