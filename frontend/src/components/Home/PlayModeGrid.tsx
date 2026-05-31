import { useEconomyMe } from "@/hooks/useEconomy"

const MODES = [
  { icon: "📝", label: "題組訓練", desc: "5 種詐騙類型", unlockLevel: 1 },
  { icon: "🃏", label: "滑卡劇情", desc: "165 一日工作", unlockLevel: 1 },
  { icon: "⚡", label: "每日訓練", desc: "Lv.5 解鎖", unlockLevel: 5 },
  { icon: "🏆", label: "排行榜", desc: "Lv.5 解鎖", unlockLevel: 5 },
]

// TODO(Phase 2): make unlocked cards navigate to their game-start routes
// (/quick/quiz, /quick/swipe, etc.) once those routes exist.
export function PlayModeGrid() {
  const { data } = useEconomyMe()
  const level = data?.level ?? 1
  return (
    <ul className="grid grid-cols-2 gap-2 list-none p-0 m-0">
      {MODES.map((m) => {
        const locked = level < m.unlockLevel
        return (
          <li
            key={m.label}
            aria-disabled={locked}
            aria-label={locked ? `${m.label}（尚未解鎖）` : m.label}
            className={`rounded-xl border bg-card p-3 ${locked ? "opacity-55" : ""}`}
            data-testid={`mode-${m.label}`}
          >
            <div className="text-xl">{m.icon}</div>
            <div className="mt-1 text-xs font-bold">{m.label}</div>
            <div className="text-[10px] text-muted-foreground">{m.desc}</div>
          </li>
        )
      })}
    </ul>
  )
}
