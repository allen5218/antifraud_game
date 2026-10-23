import { Link } from "@tanstack/react-router"
import {
  Award,
  BookOpen,
  CalendarDays,
  ClipboardList,
  Mail,
  MessageCircle,
  Trophy,
  Tv,
} from "lucide-react"
import type { MenuItem } from "./logic"

const ICONS = {
  phone: MessageCircle,
  tv: Tv,
  letters: Mail,
  calendar: CalendarDays,
  bookshelf: Award,
  leaderboard: Trophy,
  badges: Award,
  team: BookOpen,
  survey: ClipboardList,
} as const

export function RoomMenu({
  items,
  onNavigate,
}: {
  items: MenuItem[]
  onNavigate: () => void
}) {
  return (
    <div className="absolute inset-x-3 bottom-24 z-40 max-h-[46%] overflow-y-auto rounded-2xl border bg-card p-2 text-card-foreground shadow-lg">
      <ul className="flex flex-col">
        {items.map((item) => {
          const Icon = ICONS[item.id]
          return (
            <li key={item.id}>
              <Link
                to={item.to}
                onClick={onNavigate}
                className={`flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm ${
                  item.done ? "opacity-50" : ""
                }`}
              >
                <Icon aria-hidden className="size-4 shrink-0" />
                <span className="font-bold">{item.label}</span>
                <span className="ml-auto text-xs text-muted-foreground">
                  {item.status}
                </span>
              </Link>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
