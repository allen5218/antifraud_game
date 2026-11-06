import { Link, useLocation } from "@tanstack/react-router"
import { menuItems } from "@/components/room/logic"
import { useHomeSummary } from "@/hooks/useHomeSummary"
import { RailMenu } from "./RailMenu"
import { isTabActive, TABS } from "./tabs"

/**
 * 桌機版側邊導覽。
 *
 * 底部分頁是手機的慣例（拇指可及），橫跨整個桌機螢幕會很怪；桌機把導覽移到左側,
 * 內容區才拿得回水平空間。兩邊共用 tabs.ts 的同一份定義。
 * 分頁下面列出房間漢堡選單的各個模式與狀態（同一份 `menuItems`），桌機不用回房間開選單。
 */
export function NavRail() {
  const { pathname } = useLocation()
  const { data } = useHomeSummary()
  return (
    <nav
      aria-label="主導覽"
      className="hidden w-56 shrink-0 flex-col gap-1 overflow-y-auto border-r bg-surface-2 p-3 md:flex"
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
      {data && (
        <>
          <p className="mt-4 px-3 text-xs font-bold text-muted-foreground">
            練習與功能
          </p>
          <RailMenu items={menuItems(data)} />
        </>
      )}
    </nav>
  )
}
