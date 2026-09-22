import { Link } from "@tanstack/react-router"
import {
  CalendarCheck,
  Layers,
  Lock,
  type LucideIcon,
  Trophy,
  WalletCards,
} from "lucide-react"
import { useEconomyMe } from "@/hooks/useEconomy"

interface Mode {
  icon: LucideIcon
  label: string
  desc: string
  unlockLevel: number
  href?: "/quick/quiz" | "/quick/swipe"
}

const MODES: Mode[] = [
  {
    icon: Layers,
    label: "題組訓練",
    desc: "5 種詐騙類型",
    unlockLevel: 1,
    href: "/quick/quiz",
  },
  {
    icon: WalletCards,
    label: "滑卡劇情",
    desc: "165 一日工作",
    unlockLevel: 1,
    href: "/quick/swipe",
  },
  { icon: CalendarCheck, label: "每日訓練", desc: "Lv.5 解鎖", unlockLevel: 5 },
  { icon: Trophy, label: "排行榜", desc: "Lv.5 解鎖", unlockLevel: 5 },
]

export function PlayModeGrid() {
  const { data } = useEconomyMe()
  const level = data?.level ?? 1
  return (
    <ul className="grid grid-cols-2 gap-2 list-none p-0 m-0 md:grid-cols-4 md:gap-3">
      {MODES.map((m) => {
        const locked = level < m.unlockLevel
        const Icon = locked ? Lock : m.icon
        const inner = (
          <>
            <Icon
              aria-hidden
              className={`size-5 ${locked ? "text-muted-foreground" : "text-primary"}`}
            />
            <div className="mt-2 text-xs font-bold">{m.label}</div>
            <div className="text-[10px] text-muted-foreground">{m.desc}</div>
          </>
        )
        return (
          <li
            key={m.label}
            aria-disabled={locked}
            aria-label={locked ? `${m.label}（尚未解鎖）` : m.label}
            data-locked={locked}
            // 可玩與鎖定用「不同表面 + 邊框」區分,而不是只把整張卡調淡——
            // 只靠 opacity 會讓鎖定的卡看起來像沒載入完。
            className={
              locked
                ? "rounded-xl border border-border/50 bg-surface-2 p-3 opacity-55"
                : "rounded-xl border border-border bg-surface-3 p-3 transition hover:border-primary/60 hover:bg-accent"
            }
            data-testid={`mode-${m.label}`}
          >
            {!locked && m.href ? (
              <Link to={m.href} className="block">
                {inner}
              </Link>
            ) : (
              inner
            )}
          </li>
        )
      })}
    </ul>
  )
}
