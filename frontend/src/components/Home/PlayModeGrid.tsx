import { Link } from "@tanstack/react-router"
import {
  CalendarCheck,
  ClipboardCheck,
  Lock,
  type LucideIcon,
  MessagesSquare,
  ScanText,
  Trophy,
  WalletCards,
} from "lucide-react"
import { useEconomyMe } from "@/hooks/useEconomy"

interface Mode {
  icon: LucideIcon
  label: string
  desc: string
  unlockLevel: number
  href:
    | "/quick/quiz"
    | "/quick/swipe"
    | "/scenarios"
    | "/exam"
    | "/daily"
    | "/leaderboard"
}

/** 首頁主要的四個入口。 */
const PRIMARY: Mode[] = [
  {
    icon: WalletCards,
    label: "滑卡訓練",
    desc: "直覺判斷",
    unlockLevel: 1,
    href: "/quick/swipe",
  },
  {
    icon: ScanText,
    label: "訊息判讀訓練",
    desc: "辨識話術、知道怎麼查證",
    unlockLevel: 1,
    href: "/quick/quiz",
  },
  {
    icon: MessagesSquare,
    label: "情境對抗訓練",
    desc: "臨場判斷",
    unlockLevel: 1,
    href: "/scenarios",
  },
  {
    icon: ClipboardCheck,
    label: "檢測",
    desc: "四關考完，70 分過關",
    unlockLevel: 1,
    href: "/exam",
  },
]

/** 每天一次的練習與排名，放在四個入口下面，解鎖條件維持 Lv.5。 */
const SECONDARY: Mode[] = [
  {
    icon: CalendarCheck,
    label: "每日訓練",
    desc: "每天 10 題",
    unlockLevel: 5,
    href: "/daily",
  },
  {
    icon: Trophy,
    label: "排行榜",
    desc: "今日與本週排名",
    unlockLevel: 5,
    href: "/leaderboard",
  },
]

export function PlayModeGrid() {
  const { data } = useEconomyMe()
  const level = data?.level ?? 1
  return (
    <div className="flex flex-col gap-4">
      <ul
        data-testid="home-primary-entries"
        className="m-0 grid list-none grid-cols-1 gap-2 p-0 md:grid-cols-2"
      >
        {PRIMARY.map((mode) => (
          <ModeCard key={mode.href} mode={mode} level={level} prominent />
        ))}
      </ul>
      <section
        data-testid="home-secondary-entries"
        aria-label="每日訓練與排行榜"
      >
        <h2 className="mb-2 text-[11px] font-bold text-muted-foreground">
          每日訓練與排行榜
        </h2>
        <ul className="m-0 grid list-none grid-cols-2 gap-2 p-0">
          {SECONDARY.map((mode) => (
            <ModeCard key={mode.href} mode={mode} level={level} />
          ))}
        </ul>
      </section>
    </div>
  )
}

function ModeCard({
  mode,
  level,
  prominent = false,
}: {
  mode: Mode
  level: number
  prominent?: boolean
}) {
  const locked = level < mode.unlockLevel
  const Icon = locked ? Lock : mode.icon
  const inner = (
    <div className={prominent ? "flex items-start gap-3" : undefined}>
      <Icon
        aria-hidden
        className={
          prominent
            ? `mt-0.5 size-5 shrink-0 ${locked ? "text-muted-foreground" : "text-primary"}`
            : `size-5 ${locked ? "text-muted-foreground" : "text-primary"}`
        }
      />
      <div className={prominent ? "min-w-0" : "mt-2"}>
        <div className={prominent ? "text-sm font-bold" : "text-xs font-bold"}>
          {mode.label}
        </div>
        <div
          className={
            prominent
              ? "mt-0.5 text-xs leading-snug text-muted-foreground"
              : "text-[10px] text-muted-foreground"
          }
        >
          {locked ? `Lv.${mode.unlockLevel} 解鎖` : mode.desc}
        </div>
      </div>
    </div>
  )
  return (
    <li
      aria-disabled={locked}
      aria-label={locked ? `${mode.label}（尚未解鎖）` : mode.label}
      data-locked={locked}
      // 可玩與鎖定用「不同表面 + 邊框」區分,而不是只把整張卡調淡——
      // 只靠 opacity 會讓鎖定的卡看起來像沒載入完。
      className={
        locked
          ? "rounded-xl border border-border/50 bg-surface-2 p-3 opacity-55"
          : "rounded-xl border border-border bg-surface-3 p-3 transition hover:border-primary/60 hover:bg-accent"
      }
      data-testid={`mode-${mode.label}`}
    >
      {locked ? (
        inner
      ) : (
        <Link to={mode.href} className="block">
          {inner}
        </Link>
      )}
    </li>
  )
}
