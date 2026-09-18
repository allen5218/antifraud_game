import { useState } from "react"
import { Eye, GitFork, Search, ShieldCheck, TrendingUp, X } from "lucide-react"
import { useEconomyMe } from "@/hooks/useEconomy"

export interface SkillNode {
  id: string
  name: string
  category: "洞察" | "查核" | "護盾" | "槓桿"
  level: number
  maxLevel: number
  description: string
  bonusText: string
  cost: number
  iconType: "eye" | "search" | "shield" | "trending"
}

const INITIAL_SKILLS: SkillNode[] = [
  {
    id: "insight_1",
    name: "紅旗敏銳度",
    category: "洞察",
    level: 1,
    maxLevel: 5,
    description: "在對話中自動標示『時間壓力』與『限時匯款』等詐騙詞彙",
    bonusText: "答對連勝獎勵 +15%",
    cost: 100,
    iconType: "eye",
  },
  {
    id: "audit_1",
    name: "官方查核特快車",
    category: "查核",
    level: 1,
    maxLevel: 3,
    description: "解鎖 LINE 防詐 Bot 直接轉傳分析，查證時間縮短 50%",
    bonusText: "查證工具冷卻時間 -50%",
    cost: 150,
    iconType: "search",
  },
  {
    id: "shield_1",
    name: "資產防禦護盾",
    category: "護盾",
    level: 0,
    maxLevel: 3,
    description: "如果不幸在情境受騙，強制觸發保險補償",
    bonusText: "誤判損失降低 50%",
    cost: 200,
    iconType: "shield",
  },
  {
    id: "yield_1",
    name: "複利產權槓桿",
    category: "槓桿",
    level: 0,
    maxLevel: 5,
    description: "獲得防詐大師認證，提升所有房屋被動租金收益",
    bonusText: "全資產收益槓桿 +25%",
    cost: 300,
    iconType: "trending",
  },
]

interface SkillTreeModalProps {
  isOpen: boolean
  onClose: () => void
}

export function SkillTreeModal({ isOpen, onClose }: SkillTreeModalProps) {
  const { data: economy } = useEconomyMe()
  const [skills, setSkills] = useState<SkillNode[]>(INITIAL_SKILLS)
  const [userPoints, setUserPoints] = useState<number>(500) // Default starting skill points

  if (!isOpen) return null

  const handleUpgrade = (skillId: string) => {
    setSkills((prev) =>
      prev.map((s) => {
        if (s.id === skillId && s.level < s.maxLevel && userPoints >= s.cost) {
          setUserPoints((pts) => pts - s.cost)
          return { ...s, level: s.level + 1 }
        }
        return s
      })
    )
  }

  const renderIcon = (type: SkillNode["iconType"]) => {
    switch (type) {
      case "eye":
        return <Eye className="w-5 h-5 text-white" />
      case "search":
        return <Search className="w-5 h-5 text-white" />
      case "shield":
        return <ShieldCheck className="w-5 h-5 text-white" />
      case "trending":
        return <TrendingUp className="w-5 h-5 text-white" />
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 text-white rounded-2xl border border-white/20 w-full max-w-lg overflow-hidden shadow-[0_0_30px_rgba(255,255,255,0.08)] flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-4 bg-slate-950/80 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/20 bg-white/5 text-white shadow-[0_0_10px_rgba(255,255,255,0.05)]">
              <GitFork className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-wide">防詐偵探天賦樹</h2>
              <p className="text-xs text-slate-400">強化查核路徑，獲取通關獎勵並提升資產加成</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 flex items-center justify-center text-slate-300 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Skill Points Summary */}
        <div className="bg-white/5 px-4 py-3 border-b border-white/10 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="text-slate-300 font-medium">可用洞察點數：</span>
            <span className="text-sm font-mono text-white font-bold">{userPoints} pts</span>
          </div>
          <div className="text-slate-400">
            等級: <span className="text-white font-mono font-bold">Lv.{economy?.level ?? 1}</span>
          </div>
        </div>

        {/* Skill Tree List */}
        <div className="p-4 overflow-y-auto space-y-2.5 flex-1">
          {skills.map((skill) => {
            const isMax = skill.level >= skill.maxLevel
            const canAfford = userPoints >= skill.cost && !isMax

            return (
              <div
                key={skill.id}
                className="bg-white/5 rounded-xl p-3.5 border border-white/15 flex items-start gap-3 hover:border-white/30 transition-all shadow-[0_0_15px_rgba(255,255,255,0.03)]"
              >
                <div className="p-2.5 rounded-lg border border-white/15 bg-white/5">
                  {renderIcon(skill.iconType)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="font-bold text-sm text-slate-100 flex items-center gap-2">
                      {skill.name}
                      <span className="text-[10px] bg-white/10 border border-white/15 px-2 py-0.5 rounded text-slate-300">
                        {skill.category}
                      </span>
                    </h3>
                    <span className="text-xs font-mono text-slate-300 font-bold">
                      Lv.{skill.level}/{skill.maxLevel}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 mt-1">{skill.description}</p>
                  <div className="mt-2 flex items-center justify-between text-xs">
                    <span className="text-slate-300 font-medium">加成效果: {skill.bonusText}</span>
                    <button
                      disabled={!canAfford}
                      onClick={() => handleUpgrade(skill.id)}
                      className={`px-3 py-1 rounded-lg font-bold text-xs transition-all ${
                        isMax
                          ? "bg-white/10 text-slate-500 border border-white/10 cursor-not-allowed"
                          : canAfford
                            ? "bg-white text-slate-950 hover:bg-slate-200 shadow-[0_0_12px_rgba(255,255,255,0.15)]"
                            : "bg-white/5 text-slate-500 border border-white/10 cursor-not-allowed"
                      }`}
                    >
                      {isMax ? "已滿級" : `升級 (${skill.cost} pts)`}
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Footer info */}
        <div className="p-3 bg-slate-950 text-center text-[11px] text-slate-400 border-t border-white/10">
          提示：在題組與情境對話中完成查核即可累積洞察點數
        </div>
      </div>
    </div>
  )
}
