import { createFileRoute, Link } from "@tanstack/react-router"
import {
  ChevronRight,
  ClipboardList,
  LogOut,
  type LucideIcon,
  Settings,
  ShoppingBag,
} from "lucide-react"
import { PracticeFocusCard } from "@/components/practice/PracticeFocus"
import useAuth from "@/hooks/useAuth"
import { useEconomyMe } from "@/hooks/useEconomy"

export const Route = createFileRoute("/_shell/me")({
  component: Me,
})

const LINKS: {
  to: "/pretest" | "/mascot" | "/settings"
  icon: LucideIcon
  label: string
}[] = [
  { to: "/pretest", icon: ClipboardList, label: "重新做前測" },
  { to: "/mascot", icon: ShoppingBag, label: "吉祥物商店" },
  { to: "/settings", icon: Settings, label: "帳號設定" },
]

const ROW =
  "flex w-full items-center gap-3 rounded-xl border border-border bg-card px-3 py-3 text-sm transition hover:bg-accent"

function Me() {
  const { user, logout } = useAuth()
  const { data: economy } = useEconomyMe()

  return (
    <div className="flex flex-col gap-3">
      <section className="flex items-center gap-3 rounded-2xl border border-border bg-surface-3 p-4">
        <img
          src="/assets/mascot/base.webp"
          alt=""
          aria-hidden="true"
          width={64}
          height={64}
          className="size-16 shrink-0 rounded-2xl object-cover"
        />
        <div className="min-w-0">
          <h2 className="truncate text-lg font-bold">
            {user?.full_name || user?.email || "載入中…"}
          </h2>
          {economy && (
            <p className="text-xs text-muted-foreground">
              Lv.{Math.min(economy.level, 10)} · 連續 {economy.streak_days} 天
            </p>
          )}
        </div>
      </section>

      <PracticeFocusCard />

      <nav className="grid gap-2" aria-label="個人選單">
        {LINKS.map(({ to, icon: Icon, label }) => (
          <Link key={to} to={to} className={ROW}>
            <Icon aria-hidden className="size-4 text-primary" />
            <span className="flex-1">{label}</span>
            <ChevronRight
              aria-hidden
              className="size-4 text-muted-foreground"
            />
          </Link>
        ))}
        <button type="button" onClick={logout} className={ROW}>
          <LogOut aria-hidden className="size-4 text-muted-foreground" />
          <span className="flex-1 text-left">登出</span>
        </button>
      </nav>
    </div>
  )
}
