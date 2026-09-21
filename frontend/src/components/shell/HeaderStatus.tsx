import { Link } from "@tanstack/react-router"
import { Coins, Flame, Star } from "lucide-react"
import { useEconomyMe } from "@/hooks/useEconomy"

export function HeaderStatus() {
  const { data } = useEconomyMe()
  const cash = data?.cash ?? 0
  const streakDays = data?.streak_days ?? 0
  // text-red-600 在深色模式下對比不足;destructive 是主題色,兩種配色都調過
  const cashColor = cash < 0 ? "text-destructive" : "text-foreground"

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between border-b bg-background px-4 py-3">
      <span className="font-bold md:hidden">ScamGym</span>
      {/* 桌機的字標在 NavRail 上,這裡留空撐開版面 */}
      <span className="hidden md:block" />
      <div className="flex gap-2 text-xs">
        <Link
          to="/assets"
          data-testid="hdr-cash"
          className={`flex items-center gap-1 rounded-full bg-muted px-2 py-1 ${cashColor}`}
        >
          <Coins aria-hidden className="size-3.5" />
          <span className="font-medium">{cash.toLocaleString()}</span>
        </Link>
        <span className="flex items-center gap-1 rounded-full bg-muted px-2 py-1">
          <Flame aria-hidden className="size-3.5 text-warning" />
          <span className="font-medium">{streakDays}</span>
        </span>
        <span className="flex items-center gap-1 rounded-full bg-muted px-2 py-1">
          <Star aria-hidden className="size-3.5 text-primary" />
          <span className="font-medium">
            Lv.{Math.min(data?.level ?? 1, 10)}
          </span>
        </span>
      </div>
    </header>
  )
}
