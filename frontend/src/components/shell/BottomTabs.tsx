import { Link, useLocation } from "@tanstack/react-router"
import { isTabActive, TABS } from "./tabs"

/** 手機版導覽。桌機改用 NavRail（見 _shell.tsx），所以這裡在 md 以上隱藏。 */
export function BottomTabs() {
  const { pathname } = useLocation()
  return (
    <nav className="sticky bottom-0 z-20 grid grid-cols-4 border-t bg-background py-2 md:hidden">
      {TABS.map((t) => {
        const active = isTabActive(pathname, t.to)
        const Icon = t.icon
        return (
          <Link
            key={t.to}
            to={t.to}
            data-testid={t.testId}
            className={`flex flex-col items-center gap-0.5 text-[10px] ${
              active ? "font-bold text-primary" : "text-muted-foreground"
            }`}
          >
            <Icon aria-hidden className="size-5" />
            <span>{t.label}</span>
          </Link>
        )
      })}
    </nav>
  )
}
