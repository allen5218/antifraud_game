import { Link, useLocation } from "@tanstack/react-router"
import { useHomeSummary } from "@/hooks/useHomeSummary"
import { cn } from "@/lib/utils"
import { isTabActive, TABS } from "./tabs"

/** 四個分頁的頁面才顯示底部分頁；進到某個玩法後用頁首的「回首頁」回來 */
export function showsTabBar(pathname: string): boolean {
  return TABS.some((t) => pathname === t.to)
}

/**
 * 一般模式的手機底部分頁（桌機用左側 NavRail，同一份 `tabs.ts`）。
 * 放在版面的最下面而不是浮在上面，房間的底排按鈕才不會被蓋住。
 */
export function TabBar() {
  const { pathname } = useLocation()
  const { data } = useHomeSummary()
  if (!showsTabBar(pathname)) return null
  return (
    <nav
      aria-label="分頁"
      className="grid shrink-0 grid-cols-4 border-t bg-background pb-[env(safe-area-inset-bottom)] md:hidden"
    >
      {TABS.map((t) => {
        const active = isTabActive(pathname, t.to)
        const Icon = t.icon
        const badge = t.to === "/scenarios" ? (data?.inbox_pending ?? 0) : 0
        return (
          <Link
            key={t.to}
            to={t.to}
            data-testid={t.testId}
            aria-current={active ? "page" : undefined}
            className={cn(
              "relative flex flex-col items-center gap-0.5 py-2 text-xs",
              active ? "font-bold text-primary" : "text-muted-foreground",
            )}
          >
            <Icon aria-hidden className="size-6" />
            {t.label}
            {badge > 0 && (
              <span className="absolute top-1 left-1/2 ml-2 min-w-5 rounded-full bg-scam px-1 text-center text-[11px] font-bold leading-5 text-white">
                {badge}
              </span>
            )}
          </Link>
        )
      })}
    </nav>
  )
}
