import { Link, useLocation } from "@tanstack/react-router"
import { isTabActive, TABS } from "./tabs"

/**
 * 桌機版側邊導覽。
 *
 * 底部分頁是手機的慣例（拇指可及），橫跨整個桌機螢幕會很怪；桌機把導覽移到左側,
 * 內容區才拿得回水平空間。兩邊共用 tabs.ts 的同一份定義。
 */
export function NavRail() {
  const { pathname } = useLocation()
  return (
    <nav
      aria-label="主導覽"
      className="hidden w-52 shrink-0 flex-col gap-1 border-r bg-surface-2 p-3 md:flex"
    >
      <span className="mb-3 px-2 text-lg font-bold">ScamGym</span>
      {TABS.map((t) => {
        const active = isTabActive(pathname, t.to)
        const Icon = t.icon
        return (
          <Link
            key={t.to}
            to={t.to}
            data-testid={`rail-${t.testId}`}
            className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition ${
              active
                ? "bg-accent font-bold text-primary"
                : "text-muted-foreground hover:bg-accent/60 hover:text-foreground"
            }`}
          >
            <Icon aria-hidden className="size-4.5" />
            <span>{t.label}</span>
          </Link>
        )
      })}
    </nav>
  )
}
