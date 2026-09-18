import { useState } from "react"
import { Link } from "@tanstack/react-router"
import { useEconomyMe } from "@/hooks/useEconomy"
import { SkillTreeModal } from "@/components/skilltree/SkillTreeModal"
import { FraudCaseMuseum } from "@/components/museum/FraudCaseMuseum"

const MODES = [
  {
    tag: "快測",
    badge: "測驗",
    label: "題組訓練",
    desc: "判斷/話術/配對 混合題",
    unlockLevel: 1,
    href: "/quick/quiz",
  },
  {
    tag: "情境",
    badge: "模擬",
    label: "滑卡劇情",
    desc: "左滑詐騙 · 右滑正當",
    unlockLevel: 1,
    href: "/quick/swipe",
  },
  {
    tag: "天賦",
    badge: "加成",
    label: "防詐天賦樹",
    desc: "解鎖強化與收益加成",
    unlockLevel: 1,
    isSkillTree: true,
  },
  {
    tag: "案件",
    badge: "司法",
    label: "真實案件館",
    desc: "10 篇官方起訴判決實錄",
    unlockLevel: 1,
    isMuseum: true,
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
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            遊戲玩法模式
          </h3>
          <span className="text-[10px] text-slate-500 font-mono">SELECT MODE</span>
        </div>

        <ul className="grid grid-cols-2 gap-2.5 list-none p-0 m-0">
          {MODES.map((m) => {
            const locked = level < m.unlockLevel
            const content = (
              <div className="relative flex flex-col justify-between h-full">
                <div className="flex items-start justify-between">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/20 bg-white/5 text-xs font-bold text-white shadow-[0_0_10px_rgba(255,255,255,0.05)]">
                    {m.tag}
                  </div>
                  <span className="rounded-full border border-white/20 bg-white/5 px-2 py-0.5 text-[9px] font-semibold tracking-wide text-slate-300">
                    {m.badge}
                  </span>
                </div>
                <div className="mt-3">
                  <div className="text-sm font-bold text-white group-hover:text-white flex items-center justify-between">
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
                className={`group relative overflow-hidden rounded-2xl border border-white/20 bg-slate-900/80 p-3.5 cursor-pointer shadow-[0_0_20px_rgba(255,255,255,0.06)] backdrop-blur-xl transition-all duration-300 hover:border-white/40 hover:shadow-[0_0_25px_rgba(255,255,255,0.12)] active:scale-95 ${
                  locked ? "opacity-40 grayscale cursor-not-allowed" : ""
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

