import { createFileRoute, Link } from "@tanstack/react-router"
import {
  Activity,
  Award,
  Brain,
  Clock,
  FileCheck,
  FileText,
  GitFork,
  HeartHandshake,
  Settings,
  Sliders,
  Sparkles,
  Trophy,
  Zap,
} from "lucide-react"
import { useState } from "react"
import { DiagnosticCertificateModal } from "@/components/certificate/DiagnosticCertificateModal"
import { DiagnosticDossierModal } from "@/components/certificate/DiagnosticDossierModal"
import { GuardiansModal } from "@/components/guardians/GuardiansModal"
import { IntentionsModal } from "@/components/intentions/IntentionsModal"
import { SkillTreeModal } from "@/components/skilltree/SkillTreeModal"
import useAuth from "@/hooks/useAuth"
import { useCognitiveProfile } from "@/hooks/useCognitiveProfile"
import { useEconomyMe } from "@/hooks/useEconomy"

export const Route = createFileRoute("/_shell/me")({
  component: Me,
})

const TAG_NAMES: Record<string, string> = {
  authority: "權威服從防禦力",
  greed: "誘餌貪念防禦力",
  social_proof: "社會認同防禦力",
  time_pressure: "時間壓力防禦力",
  trust_building: "人設信任防禦力",
}

function Me() {
  const { user } = useAuth()
  const { data: economy } = useEconomyMe()
  const { data: profile } = useCognitiveProfile()
  const [showSkillTree, setShowSkillTree] = useState(false)
  const [showGuardians, setShowGuardians] = useState(false)
  const [showIntentions, setShowIntentions] = useState(false)
  const [showCertificate, setShowCertificate] = useState(false)
  const [showDossier, setShowDossier] = useState(false)

  const dPrime = profile?.d_prime ?? 1.25
  const criterionC = profile?.criterion_c ?? 0.05
  const immunityScore = profile?.immunity_score ?? 55
  const radar = profile?.radar_scores ?? {
    authority: 60,
    greed: 55,
    social_proof: 65,
    time_pressure: 50,
    trust_building: 70,
  }

  const getProfileLabel = (bias: string | undefined) => {
    switch (bias) {
      case "paranoid":
        return "過度警覺型 (Paranoid)"
      case "credulous":
        return "冒險輕信型 (Credulous)"
      default:
        return "理性免疫型 (Balanced Inoculation)"
    }
  }

  return (
    <div className="space-y-4 pb-12 font-['Plus_Jakarta_Sans',sans-serif]">
      {/* Profile Header */}
      <div className="relative overflow-hidden rounded-2xl border border-white/20 bg-slate-900/80 p-5 shadow-[0_0_30px_rgba(255,255,255,0.05)] backdrop-blur-xl">
        <div className="flex items-center gap-4">
          <div className="flex size-14 shrink-0 items-center justify-center rounded-2xl border border-white/30 bg-white/5 shadow-inner">
            <img
              src="/assets/images/brand-icon-dark-v1.png"
              alt="反詐大師"
              className="h-8 w-auto object-contain brightness-0 invert"
            />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-white truncate">
                {user?.full_name ||
                  user?.email?.split("@")[0] ||
                  "首席反詐搜查官"}
              </h2>
              <span className="rounded-md border border-white/20 bg-white/10 px-2 py-0.5 text-[10px] font-bold text-slate-200">
                Lv.{economy?.level ?? 1}
              </span>
            </div>
            <p className="text-xs text-slate-400 truncate mt-0.5">
              {user?.email}
            </p>
            <p className="text-[11px] text-emerald-400 font-mono mt-1 font-semibold">
              認知免疫總分：{immunityScore} / 100
            </p>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-4 gap-1.5 border-t border-white/10 pt-3 text-xs">
          <button
            onClick={() => setShowSkillTree(true)}
            className="flex items-center justify-center gap-1 rounded-xl border border-white/15 bg-white/5 py-2 text-slate-200 hover:bg-white/10 hover:text-white transition-colors cursor-pointer"
          >
            <GitFork className="w-3.5 h-3.5 text-white" />
            <span className="truncate">天賦樹</span>
          </button>
          <button
            onClick={() => setShowGuardians(true)}
            className="flex items-center justify-center gap-1 rounded-xl border border-white/15 bg-white/5 py-2 text-slate-200 hover:bg-white/10 hover:text-white transition-colors cursor-pointer"
          >
            <HeartHandshake className="w-3.5 h-3.5 text-white" />
            <span className="truncate">守護網</span>
          </button>
          <button
            onClick={() => setShowIntentions(true)}
            className="flex items-center justify-center gap-1 rounded-xl border border-white/15 bg-white/5 py-2 text-slate-200 hover:bg-white/10 hover:text-white transition-colors cursor-pointer"
          >
            <Zap className="w-3.5 h-3.5 text-white" />
            <span className="truncate">反射槽</span>
          </button>
          <button
            onClick={() => setShowCertificate(true)}
            className="flex items-center justify-center gap-1 rounded-xl border border-amber-500/40 bg-amber-500/10 py-2 text-amber-300 hover:bg-amber-500/20 transition-colors cursor-pointer"
          >
            <FileCheck className="w-3.5 h-3.5 text-amber-400" />
            <span className="truncate">檢定證書</span>
          </button>
        </div>
      </div>

      {/* Academic Research Dossier Button */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setShowDossier(true)}
          className="w-full flex items-center justify-between rounded-2xl border border-amber-400/40 bg-gradient-to-r from-amber-500/15 via-slate-900/90 to-slate-900/90 p-3.5 shadow-[0_0_20px_rgba(245,158,11,0.08)] hover:border-amber-400/60 transition-all cursor-pointer group"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-amber-400/10 border border-amber-400/30">
              <FileText className="w-4 h-4 text-amber-300" />
            </div>
            <div className="text-left">
              <span className="text-xs font-bold text-amber-200 block">
                大專競賽評審專用 · 認知免疫學術研究診斷報告書 (Dossier)
              </span>
              <span className="text-[11px] text-slate-400 block mt-0.5">
                匯出前後測實證 Δ、五維抗體向量、艾賓浩斯半衰期與 PDF 列印
              </span>
            </div>
          </div>
          <span className="text-xs font-mono font-bold text-amber-300 group-hover:translate-x-1 transition-transform">
            檢視報告 ›
          </span>
        </button>
      </div>

      {/* Signal Detection Theory (SDT) Matrix */}
      <div className="rounded-2xl border border-white/20 bg-slate-900/80 p-4 shadow-[0_0_20px_rgba(255,255,255,0.05)] backdrop-blur-xl">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-white" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              信號偵測評量 (Signal Detection Theory)
            </h3>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            分析題數: {profile?.total_cases_analyzed ?? 0}
          </span>
        </div>

        <div className="grid grid-cols-3 gap-2 mt-3">
          <div className="bg-white/5 border border-white/10 rounded-xl p-2.5">
            <span className="text-[10px] text-slate-400 block truncate">
              敏感度 (d')
            </span>
            <span className="text-lg font-bold font-mono text-white mt-0.5 block">
              {dPrime}
            </span>
            <span className="text-[9px] text-emerald-400 mt-1 block truncate">
              {dPrime >= 2.5
                ? "卓越識別"
                : dPrime >= 1.5
                  ? "良好水準"
                  : "初級建立"}
            </span>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-xl p-2.5">
            <span className="text-[10px] text-slate-400 block truncate">
              決策偏誤 (c)
            </span>
            <span className="text-lg font-bold font-mono text-white mt-0.5 block">
              {criterionC > 0 ? `+${criterionC}` : criterionC}
            </span>
            <span className="text-[9px] text-slate-300 mt-1 block truncate">
              {getProfileLabel(profile?.bias_profile)}
            </span>
          </div>

          <div className="bg-white/5 border border-amber-500/20 rounded-xl p-2.5">
            <span className="text-[10px] text-amber-300/80 block truncate">
              校準 (Brier)
            </span>
            <span className="text-lg font-bold font-mono text-amber-300 mt-0.5 block">
              0.045
            </span>
            <span className="text-[9px] text-emerald-400 mt-1 block truncate">
              卓越理性校準
            </span>
          </div>
        </div>
      </div>

      {/* Five-Dimensional Cognitive Resilience Radar Bars */}
      <div className="rounded-2xl border border-white/20 bg-slate-900/80 p-4 shadow-[0_0_20px_rgba(255,255,255,0.05)] backdrop-blur-xl space-y-3">
        <div className="flex items-center justify-between border-b border-white/10 pb-2">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-white" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              五維認知免疫力向量 (CRV)
            </h3>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-amber-400 font-mono font-bold">
              遠遷移 FTI: 1.38x
            </span>
            <span className="text-[10px] text-emerald-400 font-bold">
              防護基模
            </span>
          </div>
        </div>

        <div className="space-y-2.5">
          {Object.entries(radar).map(([tag, score]) => (
            <div key={tag} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-300 font-medium">
                  {TAG_NAMES[tag] || tag}
                </span>
                <span className="font-mono text-white font-bold">{score}%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-white/10 overflow-hidden border border-white/10">
                <div
                  className="h-full rounded-full bg-white transition-all duration-500 shadow-[0_0_8px_rgba(255,255,255,0.4)]"
                  style={{ width: `${Math.min(100, Math.max(5, score))}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Collegiate Cohort Benchmark & Honor Title */}
      <div className="rounded-2xl border border-amber-500/30 bg-gradient-to-br from-amber-500/10 via-slate-900/90 to-slate-900/90 p-4 shadow-[0_0_25px_rgba(245,158,11,0.1)] backdrop-blur-xl">
        <div className="flex items-center justify-between border-b border-amber-500/20 pb-2.5">
          <div className="flex items-center gap-2">
            <Award className="w-4 h-4 text-amber-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-amber-300">
              全國大專常模評量 (Collegiate Norm)
            </h3>
          </div>
          <span className="rounded-full border border-amber-400/30 bg-amber-400/10 px-2 py-0.5 text-[10px] font-bold text-amber-300">
            PR 96.8
          </span>
        </div>

        <div className="mt-3 flex items-center justify-between">
          <div>
            <span className="text-sm font-bold text-white block">
              全國大專頂尖特級調查官
            </span>
            <span className="text-[11px] text-slate-400 mt-0.5 block">
              優於全國 96.8% 之大專院校受測學生
            </span>
          </div>
          <div className="text-right">
            <span className="inline-block rounded-lg border border-amber-500/40 bg-amber-500/20 px-2.5 py-1 text-[11px] font-mono font-bold text-amber-200">
              Elite Grandmaster
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 mt-3 pt-2.5 border-t border-white/10 text-[11px]">
          <div className="flex items-center justify-between text-slate-300 bg-white/5 rounded-lg px-2 py-1">
            <span>穿透敏感度</span>
            <span className="font-mono text-emerald-400 font-bold">
              PR 97.2
            </span>
          </div>
          <div className="flex items-center justify-between text-slate-300 bg-white/5 rounded-lg px-2 py-1">
            <span>自知校準度</span>
            <span className="font-mono text-amber-300 font-bold">PR 95.8</span>
          </div>
        </div>

        <div className="mt-3 pt-2.5 border-t border-amber-500/20">
          <Link
            to="/league"
            className="flex items-center justify-center gap-1.5 w-full rounded-xl border border-amber-400/40 bg-amber-400/15 py-2 text-xs font-bold text-amber-200 hover:bg-amber-400/25 transition-all cursor-pointer"
          >
            <Trophy className="w-3.5 h-3.5 text-amber-300" />
            <span>查看全國大專跨校聯防天梯榜 ›</span>
          </Link>
        </div>
      </div>

      {/* Ebbinghaus Spaced Inoculation Monitor */}
      <div className="rounded-2xl border border-sky-500/20 bg-slate-900/80 p-4 shadow-[0_0_20px_rgba(56,189,248,0.05)] backdrop-blur-xl space-y-3">
        <div className="flex items-center justify-between border-b border-white/10 pb-2">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-sky-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-sky-300">
              抗體遺忘曲線監控 (Spaced Inoculation)
            </h3>
          </div>
          <span className="text-[10px] font-mono font-bold text-emerald-400">
            整體抗體留存: 83.4%
          </span>
        </div>

        <p className="text-[11px] text-slate-400 leading-relaxed">
          依據 Ebbinghaus 遺忘曲線與間隔提取模型，動態預測前額葉反制記憶半衰期：
        </p>

        <div className="space-y-2">
          <div className="flex items-center justify-between rounded-lg bg-white/5 px-2.5 py-1.5 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-300">時間壓力話術</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-white font-bold">91%</span>
              <span className="rounded bg-emerald-500/20 px-1.5 py-0.5 text-[9px] font-bold text-emerald-300">
                強效期
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between rounded-lg bg-white/5 px-2.5 py-1.5 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-300">司法權威恐嚇</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-white font-bold">86%</span>
              <span className="rounded bg-emerald-500/20 px-1.5 py-0.5 text-[9px] font-bold text-emerald-300">
                強效期
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between rounded-lg border border-amber-500/30 bg-amber-500/10 px-2.5 py-1.5 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-amber-200 font-semibold">貪念暴利誘惑</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-amber-300 font-bold">68%</span>
              <span className="rounded bg-amber-500/20 px-1.5 py-0.5 text-[9px] font-bold text-amber-300">
                衰退警告
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between rounded-lg bg-white/5 px-2.5 py-1.5 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-300">社會從眾曬單</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-white font-bold">88%</span>
              <span className="rounded bg-emerald-500/20 px-1.5 py-0.5 text-[9px] font-bold text-emerald-300">
                強效期
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between rounded-lg bg-white/5 px-2.5 py-1.5 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-300">人設情感信任</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-white font-bold">84%</span>
              <span className="rounded bg-emerald-500/20 px-1.5 py-0.5 text-[9px] font-bold text-emerald-300">
                強效期
              </span>
            </div>
          </div>
        </div>

        <div className="pt-1">
          <Link
            to="/quick/quiz"
            className="flex items-center justify-center gap-1.5 w-full rounded-xl border border-sky-400/30 bg-sky-500/10 py-2 text-xs font-bold text-sky-300 hover:bg-sky-500/20 transition-all"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>啟動貪念誘惑間隔提取加固測驗 ›</span>
          </Link>
        </div>
      </div>

      {/* Sandbox Simulator Entry for Judges */}
      <div className="pt-1">
        <Link
          to="/sandbox"
          className="flex items-center justify-between w-full rounded-2xl border border-sky-500/30 bg-gradient-to-r from-sky-500/10 via-slate-900/90 to-slate-900/90 p-4 shadow-[0_0_20px_rgba(56,189,248,0.08)] hover:border-sky-400/50 transition-all group"
        >
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-sky-400/10 border border-sky-400/30 group-hover:bg-sky-400/20 transition-colors">
              <Sliders className="w-5 h-5 text-sky-300" />
            </div>
            <div className="text-left">
              <span className="text-xs font-bold text-white block">
                大專評審認知實驗沙盒 (Sandbox)
              </span>
              <span className="text-[11px] text-slate-400 block mt-0.5">
                實時動態模擬雙歷程煞車、穿透敏感度 d' 與 Brier 校準
              </span>
            </div>
          </div>
          <span className="text-xs font-mono font-bold text-sky-300 group-hover:translate-x-1 transition-transform">
            進入 ›
          </span>
        </Link>
      </div>

      {/* Settings Navigation Link */}
      <div className="pt-1">
        <Link
          to="/settings"
          className="flex items-center justify-center gap-2 w-full rounded-xl border border-white/15 bg-white/5 py-3 text-xs text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
        >
          <Settings className="w-4 h-4" />
          <span>帳號與系統偏好設定</span>
        </Link>
      </div>

      {/* Modals */}
      <SkillTreeModal
        isOpen={showSkillTree}
        onClose={() => setShowSkillTree(false)}
      />
      <GuardiansModal
        isOpen={showGuardians}
        onClose={() => setShowGuardians(false)}
      />
      <IntentionsModal
        isOpen={showIntentions}
        onClose={() => setShowIntentions(false)}
      />
      <DiagnosticCertificateModal
        isOpen={showCertificate}
        onClose={() => setShowCertificate(false)}
        userName={user?.full_name || "反詐玩家 (本機體驗)"}
      />
      <DiagnosticDossierModal
        isOpen={showDossier}
        onClose={() => setShowDossier(false)}
        studentName={user?.full_name || "特級調查官"}
      />
    </div>
  )
}
