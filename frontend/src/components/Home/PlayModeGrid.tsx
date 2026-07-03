import { Link } from "@tanstack/react-router"
import { useEconomyMe } from "@/hooks/useEconomy"

const MODES = [
  {
    icon: "📝",
    label: "題組訓練",
    desc: "5 種詐騙類型",
    unlockLevel: 1,
    href: "/quick/quiz",
  },
  {
    icon: "🃏",
    label: "滑卡劇情",
    desc: "165 一日工作",
    unlockLevel: 1,
    href: "/quick/swipe",
  },
  { icon: "⚡", label: "每日訓練", desc: "Lv.5 解鎖", unlockLevel: 5 },
  { icon: "🏆", label: "排行榜", desc: "Lv.5 解鎖", unlockLevel: 5 },
]

export function PlayModeGrid() {
  const { data } = useEconomyMe()
  const level = data?.level ?? 1
  return (
    <ul className="grid grid-cols-2 gap-2 list-none p-0 m-0">
      {MODES.map((m) => {
        const locked = level < m.unlockLevel
        const inner = (
          <>
            <div className="text-xl">{m.icon}</div>
            <div className="mt-1 text-xs font-bold">{m.label}</div>
            <div className="text-[10px] text-muted-foreground">{m.desc}</div>
          </>
        )
        return (
          <li
            key={m.label}
            aria-disabled={locked}
            aria-label={locked ? `${m.label}（尚未解鎖）` : m.label}
            className={`rounded-xl border bg-card p-3 ${locked ? "opacity-55" : ""}`}
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
