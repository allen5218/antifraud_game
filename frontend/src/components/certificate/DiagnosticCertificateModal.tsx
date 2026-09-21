import { Award, CheckCircle2, Printer, Shield, X } from "lucide-react"

interface DiagnosticCertificateModalProps {
  isOpen: boolean
  onClose: () => void
  userName?: string
}

export function DiagnosticCertificateModal({
  isOpen,
  onClose,
  userName = "反詐玩家",
}: DiagnosticCertificateModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 overflow-y-auto">
      <div className="relative w-full max-w-xl rounded-2xl border border-amber-500/40 bg-gradient-to-b from-[#0d121f] via-[#080c14] to-[#04060c] p-6 text-white shadow-[0_0_50px_rgba(245,158,11,0.15)] my-8">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 rounded-full p-1.5 text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
          aria-label="關閉證書"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Certificate Header with Seal */}
        <div className="text-center space-y-1.5 border-b border-amber-500/20 pb-4">
          <div className="inline-flex items-center justify-center p-2.5 rounded-full border border-amber-400/40 bg-amber-400/10 mb-1">
            <Shield className="w-7 h-7 text-amber-300" />
          </div>
          <div className="text-[10px] tracking-widest uppercase font-mono text-amber-400 font-bold">
            ACADEMIC COGNITIVE DEFENSE INOCULATION CERTIFICATE
          </div>
          <h2 className="text-lg font-bold text-slate-100 tracking-wide">
            全國大專院校認知防衛與資訊安全檢定證書
          </h2>
          <p className="text-[11px] text-slate-400 font-mono">
            字號：AGY-CERT-20260918-B488AC · 評核標準：審慎理性防衛級
          </p>
        </div>

        {/* Recipient & Honors */}
        <div className="py-4 text-center space-y-1 border-b border-white/10">
          <p className="text-xs text-slate-400">茲證明受試者</p>
          <h3 className="text-xl font-bold text-white tracking-wider">
            {userName}
          </h3>
          <div className="inline-flex items-center gap-2 mt-1 px-3 py-1 rounded-full border border-amber-500/40 bg-amber-500/20 text-xs font-bold text-amber-200">
            <Award className="w-3.5 h-3.5 text-amber-300" />
            <span>全國大專頂尖特級調查官 · PR 96.8</span>
          </div>
          <p className="text-[11px] text-slate-400 pt-1">
            已完成嚴肅認知疫苗接種、雙歷程慢想煞車診斷與司法行政交叉查證訓練，具備卓越詐騙穿透與決策校準能力。
          </p>
        </div>

        {/* Certified Empirical Metrics Grid */}
        <div className="py-4 space-y-2.5 border-b border-white/10">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block text-center">
            客觀實證評量矩陣（SIGNAL DETECTION & CALIBRATION METRICS）
          </span>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="rounded-xl border border-white/10 bg-white/5 p-2">
              <span className="text-[10px] text-slate-400 block">
                敏感度 (d')
              </span>
              <span className="text-base font-bold font-mono text-emerald-400 block mt-0.5">
                2.94
              </span>
              <span className="text-[9px] text-slate-400 block">
                PR 97.2 卓越
              </span>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-2">
              <span className="text-[10px] text-slate-400 block">
                決策偏倚 (c)
              </span>
              <span className="text-base font-bold font-mono text-white block mt-0.5">
                +0.04
              </span>
              <span className="text-[9px] text-slate-400 block">
                客觀理性平衡
              </span>
            </div>
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-2">
              <span className="text-[10px] text-amber-300/80 block">
                校準 (Brier)
              </span>
              <span className="text-base font-bold font-mono text-amber-300 block mt-0.5">
                0.061
              </span>
              <span className="text-[9px] text-emerald-400 block">
                自知良性區間
              </span>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div className="rounded-lg bg-white/5 px-2 py-1.5">
              <span className="text-[10px] text-slate-400 block">
                慢想決策煞車
              </span>
              <span className="font-mono text-white font-bold">+5.85 秒</span>
            </div>
            <div className="rounded-lg bg-white/5 px-2 py-1.5">
              <span className="text-[10px] text-slate-400 block">
                跨域遠遷移 FTI
              </span>
              <span className="font-mono text-amber-300 font-bold">1.38x</span>
            </div>
            <div className="rounded-lg bg-white/5 px-2 py-1.5">
              <span className="text-[10px] text-slate-400 block">
                客觀事實查證率
              </span>
              <span className="font-mono text-emerald-400 font-bold">
                100% 達成
              </span>
            </div>
          </div>
        </div>

        {/* Theoretical Framework Compliance */}
        <div className="py-3 space-y-1.5 text-xs border-b border-white/10">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
            學術防衛框架認證背書
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-[11px] text-slate-300">
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>McGuire (1964) 認知疫苗三階話術解構</span>
            </div>
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>Kahneman (2011) 雙歷程冷靜診斷煞車</span>
            </div>
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>Lichtenstein (1977) 確信度自知校準</span>
            </div>
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>司法院與金管會 100% 獨立查證合規</span>
            </div>
          </div>
        </div>

        {/* Footer with Security Hash & Action */}
        <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
          <div className="text-center sm:text-left font-mono text-[10px] text-slate-400">
            <div>防偽數位簽章驗證碼 (SHA-256)：</div>
            <div className="text-slate-300">7F9B-4D2A-E81C-063F-A952</div>
          </div>
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              onClick={() => window.print()}
              className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 rounded-xl border border-white/20 bg-white/10 px-3.5 py-2 text-xs font-bold text-white hover:bg-white/20 transition-all cursor-pointer"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>匯出列印</span>
            </button>
            <button
              onClick={onClose}
              className="flex-1 sm:flex-none rounded-xl bg-amber-400 text-slate-950 font-bold px-4 py-2 hover:bg-amber-300 transition-all cursor-pointer"
            >
              完成檢視
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
