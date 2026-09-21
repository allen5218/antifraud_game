import { Link } from "@tanstack/react-router"
import {
  ChevronRight,
  HeartHandshake,
  Layers,
  Scale,
  Sliders,
  Sparkles,
  Zap,
} from "lucide-react"
import { useState } from "react"
import { GuardiansModal } from "@/components/guardians/GuardiansModal"
import { FraudCaseMuseum } from "@/components/museum/FraudCaseMuseum"
import { SkillTreeModal } from "@/components/skilltree/SkillTreeModal"
import { useEconomyMe } from "@/hooks/useEconomy"

const MODES = [
  {
    icon: Zap,
    label: "題組訓練",
    iconColor: "text-amber-400",
    iconBg: "bg-amber-400/10 border-amber-400/20",
    unlockLevel: 1,
    href: "/quick/quiz",
  },
  {
    icon: Layers,
    label: "滑卡辨識",
    iconColor: "text-emerald-400",
    iconBg: "bg-emerald-400/10 border-emerald-400/20",
    unlockLevel: 1,
    href: "/quick/swipe",
  },
  {
    icon: Sparkles,
    label: "防詐天賦",
    iconColor: "text-purple-400",
    iconBg: "bg-purple-400/10 border-purple-400/20",
    unlockLevel: 1,
    isSkillTree: true,
  },
  {
    icon: HeartHandshake,
    label: "社區守護",
    iconColor: "text-rose-400",
    iconBg: "bg-rose-400/10 border-rose-400/20",
    unlockLevel: 1,
    isGuardians: true,
  },
  {
    icon: Scale,
    label: "真實案件",
    iconColor: "text-cyan-400",
    iconBg: "bg-cyan-400/10 border-cyan-400/20",
    unlockLevel: 1,
    isMuseum: true,
  },
  {
    icon: Sliders,
    label: "實驗沙盒",
    iconColor: "text-sky-400",
    iconBg: "bg-sky-400/10 border-sky-400/20",
    unlockLevel: 5,
    href: "/sandbox",
  },
]

export function PlayModeGrid() {
  const { data } = useEconomyMe()
  const level = data?.level ?? 1
  const [showSkillTree, setShowSkillTree] = useState(false)
  const [showMuseum, setShowMuseum] = useState(false)
  const [showGuardians, setShowGuardians] = useState(false)

  return (
    <>
      <div className="space-y-2.5">
        <div className="flex items-center justify-between px-1">
          <span className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">
            探索模組
          </span>
        </div>

        <ul className="grid grid-cols-2 gap-2.5 list-none p-0 m-0">
          {MODES.map((m) => {
            const locked = level < m.unlockLevel
            const Icon = m.icon
            const content = (
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div
                    className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border ${m.iconBg} ${m.iconColor}`}
                  >
                    <Icon className="size-4" />
                  </div>
                  <span className="text-xs font-bold text-white group-hover:text-white truncate">
                    {m.label}
                  </span>
                </div>
                <ChevronRight className="size-3.5 text-slate-500 group-hover:text-slate-300 group-hover:translate-x-0.5 transition-all shrink-0" />
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
                  if (m.isGuardians) setShowGuardians(true)
                }}
                className={`group relative flex items-center rounded-2xl border-[1.5px] border-white/22 bg-slate-900/90 px-3 py-2.5 cursor-pointer glow-card backdrop-blur-xl transition-all duration-200 active:scale-98 ${
                  locked ? "opacity-55 opacity-40 grayscale cursor-not-allowed" : ""
                }`}
                data-testid={`mode-${m.label}`}
              >
                {!locked && m.href ? (
                  <Link to={m.href} className="w-full">
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
      <SkillTreeModal
        isOpen={showSkillTree}
        onClose={() => setShowSkillTree(false)}
      />
      <FraudCaseMuseum
        isOpen={showMuseum}
        onClose={() => setShowMuseum(false)}
      />
      <GuardiansModal
        isOpen={showGuardians}
        onClose={() => setShowGuardians(false)}
      />
    </>
  )
}
