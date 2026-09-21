import { HeartHandshake, Mail, Shield, X } from "lucide-react"
import { useGuardiansOverview } from "@/hooks/useGuardians"

interface GuardiansModalProps {
  isOpen: boolean
  onClose: () => void
}

export function GuardiansModal({ isOpen, onClose }: GuardiansModalProps) {
  const { data: overview, isLoading } = useGuardiansOverview()

  if (!isOpen) return null

  const guardians = overview?.guardians ?? []
  const totalCases = overview?.total_protected_cases ?? 0

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200 font-['Plus_Jakarta_Sans',sans-serif]">
      <div className="bg-slate-900 text-white rounded-2xl border border-white/20 w-full max-w-xl overflow-hidden shadow-[0_0_30px_rgba(255,255,255,0.08)] flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 bg-slate-950/80 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/20 bg-white/5 text-white shadow-[0_0_10px_rgba(255,255,255,0.05)]">
              <HeartHandshake className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-wide">
                社區守護網絡 (Community Guardians)
              </h2>
              <p className="text-xs text-slate-400">
                守護易受騙長輩與學生，建立情感牽絆並解鎖感謝信
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

        {/* Stats banner */}
        <div className="bg-white/5 px-5 py-3 border-b border-white/10 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-emerald-400" />
            <span className="text-slate-300 font-medium">
              累計解救與保護人次：
            </span>
            <span className="text-sm font-mono text-white font-bold">
              {totalCases} 次
            </span>
          </div>
          <div className="text-slate-400">
            常設守護委託人: <span className="text-white font-bold">3 位</span>
          </div>
        </div>

        {/* Guardians list */}
        <div className="p-4 overflow-y-auto space-y-3.5 flex-1">
          {isLoading && (
            <div className="py-12 text-center text-xs text-slate-400">
              載入社區守護網絡數據中...
            </div>
          )}

          {!isLoading &&
            guardians.map((npc) => (
              <div
                key={npc.id}
                className="bg-white/5 rounded-xl p-4 border border-white/15 hover:border-white/30 transition-all shadow-[0_0_15px_rgba(255,255,255,0.03)] flex flex-col gap-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-sm text-white tracking-wide">
                        {npc.name}
                      </h3>
                      <span className="text-[10px] bg-white/10 border border-white/15 px-2 py-0.5 rounded text-slate-300">
                        {npc.title}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                      {npc.background}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="text-xs font-mono font-bold text-white bg-white/10 px-2.5 py-1 rounded-lg border border-white/20">
                      信任度 Lv.{npc.level} ({npc.trust_score} pt)
                    </span>
                    <p className="text-[11px] text-slate-400 mt-1">
                      已守護 {npc.cases_protected} 次
                    </p>
                  </div>
                </div>

                {/* Thank you letters */}
                {npc.unlocked_letters.length > 0 && (
                  <div className="mt-1 bg-black/40 border border-white/10 rounded-lg p-3 space-y-1.5">
                    <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-300">
                      <Mail className="w-3.5 h-3.5 text-white" />
                      已收到的感謝信：
                    </div>
                    {npc.unlocked_letters.map((letter, idx) => (
                      <p
                        key={idx}
                        className="text-xs text-slate-300 italic pl-5 border-l-2 border-white/20"
                      >
                        "{letter}"
                      </p>
                    ))}
                  </div>
                )}
              </div>
            ))}
        </div>

        {/* Footer */}
        <div className="p-3 bg-slate-950 text-center text-[11px] text-slate-400 border-t border-white/10">
          提示：在情境對話（Scenario）中成功舉報詐騙或保護委託人，即可提升對應人物好感度
        </div>
      </div>
    </div>
  )
}
