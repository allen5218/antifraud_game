import { Link, useLocation } from "@tanstack/react-router"

const TABS = [
  { to: "/", icon: "🏠", label: "首頁", testId: "tab-home" },
  { to: "/scenarios", icon: "💬", label: "情境", testId: "tab-scenarios" },
  { to: "/assets", icon: "🏘️", label: "資產", testId: "tab-assets" },
  { to: "/me", icon: "🐱", label: "我", testId: "tab-me" },
] as const

export function BottomTabs() {
  const { pathname } = useLocation()
  return (
    <nav className="sticky bottom-0 z-20 grid grid-cols-4 border-t border-slate-800/80 bg-slate-900/90 backdrop-blur-md py-2 px-1">
      {TABS.map((t) => {
        const active =
          t.to === "/"
            ? pathname === "/"
            : pathname === t.to || pathname.startsWith(`${t.to}/`)
        return (
          <Link
            key={t.to}
            to={t.to}
            data-testid={t.testId}
            className={`flex flex-col items-center gap-1 py-1 px-2 rounded-xl transition-all ${
              active
                ? "font-bold text-emerald-400 bg-emerald-950/40 border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.15)] scale-105"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <span className="text-xl leading-none">{t.icon}</span>
            <span className="text-[10px] tracking-wide">{t.label}</span>
          </Link>
        )
      })}
    </nav>
  )
}
