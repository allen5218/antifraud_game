import { useState } from "react"
import { Link } from "@tanstack/react-router"
import { useEconomyMe } from "@/hooks/useEconomy"
import { SkillTreeModal } from "@/components/skilltree/SkillTreeModal"
import { FraudCaseMuseum } from "@/components/museum/FraudCaseMuseum"

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
  { icon: "🌳", label: "防詐天賦樹", desc: "強化學習與加成", unlockLevel: 1, isSkillTree: true },
  { icon: "🏛️", label: "真實案件館", desc: "裁判書/起訴實錄", unlockLevel: 1, isMuseum: true },
]

export function PlayModeGrid() {
  const { data } = useEconomyMe()
  const level = data?.level ?? 1
  const [showSkillTree, setShowSkillTree] = useState(false)
  const [showMuseum, setShowMuseum] = useState(false)

  return (
    <>
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
              onClick={() => {
                if (m.isSkillTree) setShowSkillTree(true)
                if (m.isMuseum) setShowMuseum(true)
              }}
              className={`rounded-xl border bg-card p-3 cursor-pointer hover:border-amber-500/50 transition-all ${
                locked ? "opacity-55" : ""
              }`}
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

      {/* Interactive Modals */}
      <SkillTreeModal isOpen={showSkillTree} onClose={() => setShowSkillTree(false)} />
      <FraudCaseMuseum isOpen={showMuseum} onClose={() => setShowMuseum(false)} />
    </>
  )
}
