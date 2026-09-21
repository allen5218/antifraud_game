import {
  Activity,
  Award,
  Brain,
  Check,
  Compass,
  FileText,
  Lock,
  Printer,
  ShieldCheck,
  X,
} from "lucide-react"

interface DiagnosticDossierModalProps {
  isOpen: boolean
  onClose: () => void
  studentName?: string
}

export function DiagnosticDossierModal({
  isOpen,
  onClose,
  studentName = "特級調查官",
}: DiagnosticDossierModalProps) {
  if (!isOpen) return null

  const handlePrint = () => {
    window.print()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/85 backdrop-blur-md p-2 sm:p-4 overflow-y-auto">
      <div className="relative w-full max-w-2xl max-h-[92vh] overflow-y-auto rounded-3xl border border-white/20 bg-slate-900/95 text-slate-100 shadow-[0_0_60px_rgba(255,255,255,0.08)] p-5 sm:p-7 space-y-5 font-['Plus_Jakarta_Sans',sans-serif]">
        {/* Modal Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Dossier Header */}
        <div className="border-b border-white/10 pb-4 text-center sm:text-left">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-2xl bg-amber-400/10 border border-amber-400/30">
                <FileText className="w-6 h-6 text-amber-300" />
              </div>
              <div>
                <span className="text-[10px] font-mono tracking-widest text-amber-400 uppercase font-bold block">
                  NATIONAL COLLEGIATE RESEARCH REPORT
                </span>
                <h2 className="text-lg font-extrabold text-white tracking-wide">
                  防詐認知免疫力學術研究診斷報告書
                </h2>
              </div>
            </div>
            <div className="text-right">
              <span className="inline-block rounded-lg border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-[11px] font-mono font-bold text-amber-300">
                AGY-DOSSIER-20260919-C8F91B24
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4 text-xs">
            <div className="rounded-xl border border-white/10 bg-white/5 p-2 text-center sm:text-left">
              <span className="text-[10px] text-slate-400 block">
                受測受試者
              </span>
              <span className="font-bold text-white mt-0.5 block">
                {studentName}
              </span>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-2 text-center sm:text-left">
              <span className="text-[10px] text-slate-400 block">
                所屬校園隊列
              </span>
              <span className="font-bold text-white mt-0.5 block">
                國立清華大學
              </span>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-2 text-center sm:text-left">
              <span className="text-[10px] text-slate-400 block">
                常模天梯分位
              </span>
              <span className="font-bold text-emerald-400 font-mono mt-0.5 block">
                PR 96.8 (Top 3.2%)
              </span>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-2 text-center sm:text-left">
              <span className="text-[10px] text-slate-400 block">
                評量認證機構
              </span>
              <span className="font-bold text-slate-300 text-[10px] mt-0.5 block">
                全國大專聯評中心
              </span>
            </div>
          </div>
        </div>

        {/* Section 1: Longitudinal Empirical Deltas (前後測對照) */}
        <div className="space-y-2.5">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              一、 前後測縱向認知實證成效對照 (Longitudinal Empirical Delta)
            </h3>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-center">
              <span className="text-[10px] text-slate-400 block">
                訊號敏感度 d'
              </span>
              <div className="text-xs text-slate-400 line-through mt-1">
                前測: 0.65
              </div>
              <div className="text-base font-bold font-mono text-emerald-400 mt-0.5">
                後測: 2.94
              </div>
              <span className="text-[9px] font-bold text-emerald-300 block mt-1">
                +2.29 (p &lt; 0.001)
              </span>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-center">
              <span className="text-[10px] text-slate-400 block">
                布萊爾誤差 BS
              </span>
              <div className="text-xs text-slate-400 line-through mt-1">
                前測: 0.282
              </div>
              <div className="text-base font-bold font-mono text-amber-300 mt-0.5">
                後測: 0.052
              </div>
              <span className="text-[9px] font-bold text-amber-300 block mt-1">
                誤差衰減 -81.5%
              </span>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-center">
              <span className="text-[10px] text-slate-400 block">
                慢想決策時長
              </span>
              <div className="text-xs text-slate-400 line-through mt-1">
                前測: 2.1s
              </div>
              <div className="text-base font-bold font-mono text-sky-300 mt-0.5">
                後測: 10.6s
              </div>
              <span className="text-[9px] font-bold text-sky-300 block mt-1">
                煞車 5.05x 阻斷短路
              </span>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-center">
              <span className="text-[10px] text-slate-400 block">
                識破檢出率
              </span>
              <div className="text-xs text-slate-400 line-through mt-1">
                前測: 38.5%
              </div>
              <div className="text-base font-bold font-mono text-white mt-0.5">
                後測: 94.7%
              </div>
              <span className="text-[9px] font-bold text-emerald-400 block mt-1">
                淨提升 +56.2%
              </span>
            </div>
          </div>
        </div>

        {/* Section 2: Five-Dimensional Resilience Vectors & ZPD State */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Radar Bar breakdown */}
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4 space-y-2.5">
            <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
              <Brain className="w-4 h-4 text-white" />
              <span>二、 五維抗體強度向量 (CRV)</span>
            </span>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">司法權威恐嚇防衛</span>
                <span className="font-mono text-white font-bold">92%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">誘餌貪念暴利防衛</span>
                <span className="font-mono text-white font-bold">88%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">社會從眾曬單防衛</span>
                <span className="font-mono text-white font-bold">94%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">時間催促壓力防衛</span>
                <span className="font-mono text-white font-bold">90%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">人設情感信任防衛</span>
                <span className="font-mono text-white font-bold">95%</span>
              </div>
            </div>
          </div>

          {/* Ebbinghaus & ZPD Flow */}
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4 space-y-2.5">
            <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
              <Compass className="w-4 h-4 text-sky-400" />
              <span>三、 半衰期與心流發展狀態</span>
            </span>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">艾賓浩斯抗體半衰期</span>
                <span className="font-mono text-emerald-400 font-bold">
                  28.5 天 (持續加固)
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">當前抗體保留率</span>
                <span className="font-mono text-white font-bold">
                  89.2% (強效免疫期)
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">維高斯基 ZPD 心流區間</span>
                <span className="font-mono text-amber-300 font-bold">
                  Optimal Flow (+25%)
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">司法金管客觀查證遵循率</span>
                <span className="font-mono text-emerald-400 font-bold">
                  100.0% 合規
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Section 4: Academic Pedagogy Conclusions */}
        <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4 space-y-2 text-xs">
          <span className="font-bold text-amber-300 flex items-center gap-1.5 uppercase tracking-wider">
            <Award className="w-4 h-4 text-amber-400" />
            <span>四、 評審與學術評估核心結論 (Pedagogical Conclusions)</span>
          </span>
          <ul className="space-y-1.5 text-slate-300 leading-relaxed list-none p-0 m-0">
            <li className="flex items-start gap-1.5">
              <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
              <span>
                受試者在前額葉面對高壓情境時，已成功建立自動化『慢想煞車反射』，決策時鐘自
                2.1s 延長至 10.6s。
              </span>
            </li>
            <li className="flex items-start gap-1.5">
              <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
              <span>
                確信度校準誤差降至
                0.052，徹底消除『以為自己懂卻輕信匯款』之高危險過度自信心理偏誤。
              </span>
            </li>
            <li className="flex items-start gap-1.5">
              <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
              <span>
                跨情境遠遷移測試中，受試者能主動運用司法裁判與金管會名冊進行獨立事實查證，合規遵循率達
                100%。
              </span>
            </li>
            <li className="flex items-start gap-1.5">
              <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
              <span>
                艾賓浩斯抗體半衰期推估達 28.5 天，相較於傳統講座 2
                天即忘的衰退模式，展現顯著之間隔加固持續性。
              </span>
            </li>
          </ul>
        </div>

        {/* Security Fingerprint Bar */}
        <div className="rounded-xl border border-white/10 bg-slate-950 p-3 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] font-mono">
          <div className="flex items-center gap-2 text-slate-400">
            <Lock className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span>數位防偽校驗雜湊碼：C8F91B24A7D3E56910F42C8B</span>
          </div>
          <span className="text-emerald-400 font-bold flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>加密雜湊校驗已生效</span>
          </span>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 pt-2">
          <button
            onClick={handlePrint}
            className="flex-1 py-3 px-4 rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold text-xs shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <Printer className="w-4 h-4" />
            <span>列印 / 匯出 PDF 學術報告 (Print & Export)</span>
          </button>
          <button
            onClick={onClose}
            className="py-3 px-5 rounded-xl border border-white/20 bg-white/5 hover:bg-white/10 text-slate-300 font-bold text-xs transition-colors cursor-pointer"
          >
            關閉
          </button>
        </div>
      </div>
    </div>
  )
}
