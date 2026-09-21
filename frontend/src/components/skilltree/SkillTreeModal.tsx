import {
  Eye,
  GitFork,
  RefreshCw,
  Search,
  ShieldCheck,
  TrendingUp,
  X,
} from "lucide-react"
import { useEconomyMe } from "@/hooks/useEconomy"
import {
  useResetSkills,
  useSkillsOverview,
  useUpgradeSkill,
} from "@/hooks/useSkills"

interface SkillTreeModalProps {
  isOpen: boolean
  onClose: () => void
}

export function SkillTreeModal({ isOpen, onClose }: SkillTreeModalProps) {
  const { data: economy } = useEconomyMe()
  const { data: overview, isLoading } = useSkillsOverview()
  const upgradeMutation = useUpgradeSkill()
  const resetMutation = useResetSkills()

  if (!isOpen) return null

  const availableSp = overview?.available_sp ?? 0
  const skills = overview?.skills ?? []

  const handleUpgrade = (skillId: string) => {
    if (upgradeMutation.isPending) return
    upgradeMutation.mutate(skillId)
  }

  const handleReset = () => {
    if (resetMutation.isPending) return
    if (window.confirm("確定花費 500 現金重置所有已分配的技能天賦點數嗎？")) {
      resetMutation.mutate()
    }
  }

  const renderIcon = (type: string) => {
    switch (type) {
      case "eye":
        return <Eye className="w-5 h-5 text-white" />
      case "search":
        return <Search className="w-5 h-5 text-white" />
      case "shield":
        return <ShieldCheck className="w-5 h-5 text-white" />
      case "trending":
        return <TrendingUp className="w-5 h-5 text-white" />
      default:
        return <GitFork className="w-5 h-5 text-white" />
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
              <h2 className="text-base font-bold text-white tracking-wide">
                防詐偵探天賦樹
              </h2>
              <p className="text-xs text-slate-400">
                強化查核路徑，獲取通關獎勵並提升資產加成
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 flex items-center justify-center text-slate-300 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Skill Points Summary */}
        <div className="bg-white/5 px-4 py-3 border-b border-white/10 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="text-slate-300 font-medium">可用天賦點數：</span>
            <span className="text-sm font-mono text-white font-bold">
              {availableSp} SP
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-slate-400">
              等級:{" "}
              <span className="text-white font-mono font-bold">
                Lv.{economy?.level ?? 1}
              </span>
            </span>
            <button
              onClick={handleReset}
              disabled={
                resetMutation.isPending || (overview?.spent_sp ?? 0) === 0
              }
              className="px-2 py-0.5 rounded border border-white/15 bg-white/5 hover:bg-white/10 text-[11px] text-slate-300 hover:text-white flex items-center gap-1 transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              title="花費 500 現金重置點數"
            >
              <RefreshCw
                className={`w-3 h-3 ${resetMutation.isPending ? "animate-spin" : ""}`}
              />
              洗點 (500元)
            </button>
          </div>
        </div>

        {/* Skill Tree List */}
        <div className="p-4 overflow-y-auto space-y-2.5 flex-1">
          {isLoading && (
            <div className="py-8 text-center text-xs text-slate-400">
              載入防詐偵探天賦數據中...
            </div>
          )}

          {!isLoading &&
            skills.map((skill) => {
              const isMax = skill.level >= skill.max_level
              const canAfford = availableSp >= skill.sp_cost && !isMax

              return (
                <div
                  key={skill.id}
                  className="bg-white/5 rounded-xl p-3.5 border border-white/15 flex items-start gap-3 hover:border-white/30 transition-all shadow-[0_0_15px_rgba(255,255,255,0.03)]"
                >
                  <div className="p-2.5 rounded-lg border border-white/15 bg-white/5">
                    {renderIcon(skill.icon_type)}
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
                        Lv.{skill.level}/{skill.max_level}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 mt-1">
                      {skill.description}
                    </p>
                    <div className="mt-2 flex items-center justify-between text-xs">
                      <span className="text-slate-300 font-medium">
                        加成效果: {skill.bonus_text}
                      </span>
                      <button
                        disabled={!canAfford || upgradeMutation.isPending}
                        onClick={() => handleUpgrade(skill.id)}
                        className={`px-3 py-1 rounded-lg font-bold text-xs transition-all cursor-pointer ${
                          isMax
                            ? "bg-white/10 text-slate-500 border border-white/10 cursor-not-allowed"
                            : canAfford
                              ? "bg-white text-slate-950 hover:bg-slate-200 shadow-[0_0_12px_rgba(255,255,255,0.15)]"
                              : "bg-white/5 text-slate-500 border border-white/10 cursor-not-allowed"
                        }`}
                      >
                        {isMax ? "已滿級" : `升級 (${skill.sp_cost} SP)`}
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
        </div>

        {/* Footer info */}
        <div className="p-3 bg-slate-950 text-center text-[11px] text-slate-400 border-t border-white/10">
          提示：完成章節、升級角色與破獲情境案件均可獲取可用天賦點數（SP）
        </div>
      </div>
    </div>
  )
}
