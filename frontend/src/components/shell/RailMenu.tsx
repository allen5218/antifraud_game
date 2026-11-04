import { Link } from "@tanstack/react-router"
import type { MenuItem } from "@/components/room/logic"
import { MENU_ICONS } from "@/components/room/RoomMenu"

/** 桌機側欄的模式清單：和房間漢堡選單同一份 `menuItems`，名稱下面寫目前狀態 */
export function RailMenu({ items }: { items: MenuItem[] }) {
  return (
    <ul className="flex flex-col gap-0.5">
      {items.map((item) => {
        const Icon = MENU_ICONS[item.id]
        return (
          <li key={item.id}>
            <Link
              to={item.to}
              className={`flex items-start gap-2.5 rounded-lg px-3 py-1.5 text-sm text-muted-foreground transition hover:bg-accent/60 hover:text-foreground ${
                item.done ? "opacity-60" : ""
              }`}
              activeProps={{ className: "bg-accent font-bold text-primary" }}
            >
              <Icon aria-hidden className="mt-0.5 size-4 shrink-0" />
              <span className="flex min-w-0 flex-col">
                <span className="text-foreground">{item.label}</span>
                <span className="truncate text-xs">{item.status}</span>
              </span>
            </Link>
          </li>
        )
      })}
    </ul>
  )
}
