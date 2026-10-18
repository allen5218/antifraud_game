import type { RoomBadge as Badge } from "./logic"

/** 手機 App 那種紅色標記：有數量顯示數字，只是「有新的」顯示圓點 */
export function RoomBadge({
  badge,
  testId,
}: {
  badge: Badge
  testId?: string
}) {
  if ("count" in badge) {
    return (
      <span
        data-testid={testId}
        className="pointer-events-none absolute -top-2 -right-2 flex h-5 min-w-5 items-center justify-center rounded-full bg-scam px-1.5 text-[11px] font-bold text-scam-foreground shadow ring-2 ring-card"
      >
        {badge.count > 99 ? "99+" : badge.count}
      </span>
    )
  }
  return (
    <span
      data-testid={testId}
      className="pointer-events-none absolute -top-1 -right-1 size-3.5 rounded-full bg-scam shadow ring-2 ring-card"
    />
  )
}
