import { Link } from "@tanstack/react-router"
import { useEconomyStore } from "@/stores/economy"

export function HeaderStatus() {
  const { cash, streak, level } = useEconomyStore()
  const cashColor = cash < 0 ? "text-red-600" : "text-foreground"

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between border-b bg-background px-4 py-3">
      <span className="font-bold">反詐騙</span>
      <div className="flex gap-2 text-xs">
        <Link
          to="/assets"
          data-testid="hdr-cash"
          className={`flex items-center gap-1 rounded-full bg-muted px-2 py-1 ${cashColor}`}
        >
          <span>💰</span>
          <span className="font-medium">{cash.toLocaleString()}</span>
        </Link>
        <span className="flex items-center gap-1 rounded-full bg-muted px-2 py-1">
          <span>🔥</span>
          <span className="font-medium">{streak}</span>
        </span>
        <span className="flex items-center gap-1 rounded-full bg-muted px-2 py-1">
          <span>⭐</span>
          <span className="font-medium">Lv.{level}</span>
        </span>
      </div>
    </header>
  )
}
