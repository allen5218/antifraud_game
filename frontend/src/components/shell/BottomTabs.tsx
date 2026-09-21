import { Link, useLocation } from "@tanstack/react-router"
import { Building2, Home, MessageSquare, User } from "lucide-react"

const TABS = [
  { to: "/", icon: Home, label: "首頁", testId: "tab-home" },
  {
    to: "/scenarios",
    icon: MessageSquare,
    label: "聊天",
    testId: "tab-scenarios",
  },
  { to: "/assets", icon: Building2, label: "資產", testId: "tab-assets" },
  { to: "/me", icon: User, label: "個人", testId: "tab-me" },
] as const

export function BottomTabs() {
  const { pathname } = useLocation()
  return (
    <nav className="sticky bottom-0 z-20 grid grid-cols-4 border-t-[1.5px] border-white/20 bg-slate-950/95 backdrop-blur-xl py-2 px-2 shadow-[0_-4px_20px_rgba(0,0,0,0.4)]">
      {TABS.map((t) => {
        const active =
          t.to === "/"
            ? pathname === "/"
            : pathname === t.to || pathname.startsWith(`${t.to}/`)
        const Icon = t.icon
        return (
          <Link
            key={t.to}
            to={t.to}
            data-testid={t.testId}
            className={`flex flex-col items-center gap-1 py-1.5 px-2 rounded-xl transition-all ${
              active
                ? "font-bold text-white bg-white/15 border-[1.5px] border-white/40 glow-badge scale-105"
                : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
            }`}
          >
            <Icon className="w-4 h-4" />
            <span className="text-[11px] tracking-wide">{t.label}</span>
          </Link>
        )
      })}
    </nav>
  )
}
