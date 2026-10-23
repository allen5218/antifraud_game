import { createFileRoute, Link } from "@tanstack/react-router"
import {
  ChevronRight,
  ClipboardList,
  LogOut,
  type LucideIcon,
  QrCode,
  Settings,
  ShoppingBag,
  UsersRound,
} from "lucide-react"
import { PracticeFocusCard } from "@/components/practice/PracticeFocus"
import { MascotAvatar } from "@/components/room/MascotAvatar"
import useAuth, { currentUserQuery } from "@/hooks/useAuth"
import { economyMeQuery, useEconomyMe } from "@/hooks/useEconomy"
import { homeSummaryQuery } from "@/hooks/useHomeSummary"
import { practiceProfileQuery } from "@/hooks/usePractice"
import { warmQueries } from "@/lib/prefetch"

export const Route = createFileRoute("/_shell/me")({
  loader: ({ context: { queryClient } }) => {
    warmQueries(queryClient, [
      currentUserQuery,
      economyMeQuery,
      practiceProfileQuery,
      homeSummaryQuery,
    ])
  },
  component: Me,
})

const LINKS: {
  to: "/pretest" | "/shop" | "/settings"
  icon: LucideIcon
  label: string
}[] = [
  { to: "/pretest", icon: ClipboardList, label: "重新做前測" },
  { to: "/shop", icon: ShoppingBag, label: "商店" },
  { to: "/settings", icon: Settings, label: "帳號設定" },
]

const ADMIN_LINKS: {
  to: "/admin/cohorts" | "/admin"
  icon: LucideIcon
  label: string
}[] = [
  { to: "/admin/cohorts", icon: QrCode, label: "試測管理" },
  { to: "/admin", icon: UsersRound, label: "帳號管理" },
]

const ROW =
  "flex w-full items-center gap-3 rounded-xl border border-border bg-card px-3 py-3 text-sm transition hover:bg-accent"

function Me() {
  const { user, logout } = useAuth()
  const { data: economy } = useEconomyMe()

  return (
    <div className="flex flex-col gap-3">
      <section className="flex items-center gap-3 rounded-2xl border border-border bg-surface-3 p-4">
        <MascotAvatar className="size-16 shrink-0 rounded-2xl" />
        <div className="min-w-0">
          <h2 className="truncate text-lg font-bold">
            {user?.full_name || user?.email || "載入中…"}
          </h2>
          {user?.is_guest && user.participant_code && (
            <p className="text-sm text-muted-foreground">
              受試編號：{user.participant_code}
            </p>
          )}
          {economy && (
            <p className="text-xs text-muted-foreground">
              Lv.{Math.min(economy.level, 10)} · 連續 {economy.streak_days} 天
            </p>
          )}
        </div>
      </section>

      <PracticeFocusCard />

      {user?.is_superuser && (
        <nav className="grid gap-2" aria-label="管理">
          {ADMIN_LINKS.map(({ to, icon: Icon, label }) => (
            <Link key={to} to={to} className={ROW}>
              <Icon aria-hidden className="size-4 text-primary" />
              <span className="flex-1 font-bold">{label}</span>
              <ChevronRight
                aria-hidden
                className="size-4 text-muted-foreground"
              />
            </Link>
          ))}
        </nav>
      )}

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
