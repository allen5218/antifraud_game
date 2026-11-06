import { Link } from "@tanstack/react-router"
import { Trophy } from "lucide-react"
import { useCollections } from "@/hooks/useCollections"

export function RoomHonors() {
  const { data } = useCollections()
  const displayed = data?.collectibles.filter((c) => c.displayed) ?? []
  if (!data || (!displayed.length && !data.active_title)) return null
  return (
    <Link
      to="/progression"
      aria-label="管理房間榮譽"
      className="absolute bottom-24 right-3 z-20 max-w-44 rounded-xl border border-border bg-card/95 p-3 text-xs text-card-foreground shadow"
    >
      <div className="flex items-center gap-1 font-bold text-warning">
        <Trophy className="size-4" />
        {data.active_title ?? "我的榮譽"}
      </div>
      {displayed.map((c) => (
        <p key={c.item_key} className="mt-1">
          {c.name}
        </p>
      ))}
    </Link>
  )
}
