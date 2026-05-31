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
    <nav className="sticky bottom-0 z-20 grid grid-cols-4 border-t bg-background py-2">
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
            className={`flex flex-col items-center gap-0.5 text-[10px] ${
              active ? "font-bold text-primary" : "text-muted-foreground"
            }`}
          >
            <span className="text-xl leading-none">{t.icon}</span>
            <span>{t.label}</span>
          </Link>
        )
      })}
    </nav>
  )
}
