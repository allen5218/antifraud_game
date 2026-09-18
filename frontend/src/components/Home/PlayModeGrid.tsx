import { useState } from "react"
import { Link } from "@tanstack/react-router"
import { useEconomyMe } from "@/hooks/useEconomy"
import { SkillTreeModal } from "@/components/skilltree/SkillTreeModal"
import { FraudCaseMuseum } from "@/components/museum/FraudCaseMuseum"

const MODES = [
  {
    icon: "⚡",
    badge: "極速考驗",
    label: "題組訓練",
    desc: "判斷/話術/配對 混合題",
    unlockLevel: 1,
    href: "/quick/quiz",
    cardBg: "from-cyan-950/60 via-slate-900 to-slate-950 border-cyan-500/40 hover:border-cyan-400 hover:shadow-[0_0_20px_rgba(6,182,212,0.3)]",
    iconBg: "from-cyan-500 to-blue-600 text-white shadow-[0_0_15px_rgba(6,182,212,0.5)]",
    badgeBg: "bg-cyan-500/20 text-cyan-300 border-cyan-400/30",
  },
  {
    icon: "🃏",
    badge: "165 模擬",
    label: "滑卡劇情",
    desc: "左滑詐騙 · 右滑正當",
    unlockLevel: 1,
    href: "/quick/swipe",
    cardBg: "from-fuchsia-950/60 via-slate-900 to-slate-950 border-fuchsia-500/40 hover:border-fuchsia-400 hover:shadow-[0_0_20px_rgba(217,70,239,0.3)]",
    iconBg: "from-fuchsia-500 to-purple-600 text-white shadow-[0_0_15px_rgba(217,70,239,0.5)]",
    badgeBg: "bg-fuchsia-500/20 text-fuchsia-300 border-fuchsia-400/30",
  },
  {
    icon: "🌳",
    badge: "強化加成",
    label: "防詐天賦樹",
    desc: "解鎖學習與收益 Bonus",
    unlockLevel: 1,
    isSkillTree: true,
    cardBg: "from-emerald-950/60 via-slate-900 to-slate-950 border-emerald-500/40 hover:border-emerald-400 hover:shadow-[0_0_20px_rgba(16,185,129,0.3)]",
    iconBg: "from-emerald-500 to-teal-600 text-white shadow-[0_0_15px_rgba(16,185,129,0.5)]",
    badgeBg: "bg-emerald-500/20 text-emerald-300 border-emerald-400/30",
  },
  {
    icon: "🏛️",
    badge: "真實判決",
    label: "真實案件館",
    desc: "165/司法起訴書檔案",
    unlockLevel: 1,
    isMuseum: true,
    cardBg: "from-amber-950/60 via-slate-900 to-slate-950 border-amber-500/40 hover:border-amber-400 hover:shadow-[0_0_20px_rgba(245,158,11,0.3)]",
    iconBg: "from-amber-500 to-orange-600 text-white shadow-[0_0_15px_rgba(245,158,11,0.5)]",
    badgeBg: "bg-amber-500/20 text-amber-300 border-amber-400/30",
  },
]

export function PlayModeGrid() {
  const { data } = useEconomyMe()
  const level = data?.level ?? 1
  const [showSkillTree, setShowSkillTree] = useState(false)
  const [showMuseum, setShowMuseum] = useState(false)

  return (
    <>
      <div className="space-y-2">
        <div className="flex items-center justify-between px-1">
          <h3 className="text-xs font-black uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <span>🎮</span> 遊戲玩法模式
          </h3>
          <span className="text-[10px] text-slate-500 font-mono">SELECT MODE</span>
        </div>

        <ul className="grid grid-cols-2 gap-2.5 list-none p-0 m-0">
          {MODES.map((m) => {
            const locked = level < m.unlockLevel
            const content = (
              <div className="relative flex flex-col justify-between h-full">
                <div className="flex items-start justify-between">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br text-lg border border-white/20 ${m.iconBg}`}>
                    {m.icon}
                  </div>
                  <span className={`rounded-full border px-2 py-0.5 text-[9px] font-black tracking-wide ${m.badgeBg}`}>
                    {m.badge}
                  </span>
                </div>
                <div className="mt-3">
                  <div className="text-sm font-black text-slate-100 group-hover:text-white flex items-center justify-between">
                    <span>{m.label}</span>
                    <span className="text-xs opacity-0 group-hover:opacity-100 transition-opacity">›</span>
                  </div>
                  <div className="mt-0.5 text-[11px] font-medium text-slate-400 line-clamp-1">
                    {m.desc}
                  </div>
                </div>
              </div>
            )

            return (
              <li
                key={m.label}
                aria-disabled={locked}
                aria-label={locked ? `${m.label}（尚未解鎖）` : m.label}
                onClick={() => {
                  if (m.isSkillTree) setShowSkillTree(true)
                  if (m.isMuseum) setShowMuseum(true)
                }}
                className={`group relative overflow-hidden rounded-2xl border bg-gradient-to-br p-3.5 cursor-pointer transition-all duration-300 active:scale-95 ${m.cardBg} ${
                  locked ? "opacity-50 grayscale cursor-not-allowed" : ""
                }`}
                data-testid={`mode-${m.label}`}
              >
                {!locked && m.href ? (
                  <Link to={m.href} className="block h-full">
                    {content}
                  </Link>
                ) : (
                  content
                )}
              </li>
            )
          })}
        </ul>
      </div>

      {/* Interactive Modals */}
      <SkillTreeModal isOpen={showSkillTree} onClose={() => setShowSkillTree(false)} />
      <FraudCaseMuseum isOpen={showMuseum} onClose={() => setShowMuseum(false)} />
    </>
  )
}

