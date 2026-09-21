import { createFileRoute } from "@tanstack/react-router"
import {
  Check,
  Clock,
  Eye,
  RefreshCw,
  Scale,
  Search,
  ShieldCheck,
  Sliders,
  Sparkles,
  Zap,
} from "lucide-react"
import { useState } from "react"

export const Route = createFileRoute("/_shell/sandbox")({
  component: CognitiveSandboxPage,
})

interface ArchetypeConfig {
  key: string
  name: string
  subtitle: string
  baseD: number
  baseLat: number
  baseBrier: number
}

const ARCHETYPES: ArchetypeConfig[] = [
  {
    key: "impulsive_shopper",
    name: "衝動網購族",
    subtitle: "青年大學生典型 · 易受時間壓力與限時暴利驅使",
    baseD: 0.85,
    baseLat: 2.2,
    baseBrier: 0.28,
  },
  {
    key: "trusting_senior",
    name: "盲從長輩族",
    subtitle: "樂齡長者典型 · 極易受假冒司法檢警威懾",
    baseD: 0.6,
    baseLat: 3.4,
    baseBrier: 0.35,
  },
  {
    key: "sceptic_analyst",
    name: "草木皆兵懷疑者",
    subtitle: "高焦慮典型 · 容易誤判正當商業行為",
    baseD: 1.75,
    baseLat: 5.2,
    baseBrier: 0.13,
  },
  {
    key: "master_investigator",
    name: "特級認知調查官",
    subtitle: "已完成 30 輪認知疫苗接種 · 具備全場域抗體",
    baseD: 2.85,
    baseLat: 7.8,
    baseBrier: 0.055,
  },
]

function CognitiveSandboxPage() {
  const [selectedArchetype, setSelectedArchetype] =
    useState<string>("impulsive_shopper")
  const [pressureLevel, setPressureLevel] = useState<number>(3)
  const [cialdiniLens, setCialdiniLens] = useState<boolean>(true)
  const [system2Brake, setSystem2Brake] = useState<boolean>(true)
  const [reflexCard, setReflexCard] = useState<boolean>(true)
  const [officialVerify, setOfficialVerify] = useState<boolean>(true)

  const profile =
    ARCHETYPES.find((a) => a.key === selectedArchetype) || ARCHETYPES[0]

  // 計算動態介入數值
  let interventionsCount = 0
  let addedD = 0.0
  let addedLat = 0.0

  if (cialdiniLens) {
    addedD += 0.4
    addedLat += 1.4
    interventionsCount += 1
  }
  if (system2Brake) {
    addedD += 0.6
    addedLat += 3.2
    interventionsCount += 1
  }
  if (reflexCard) {
    addedD += 0.45
    addedLat += 1.8
    interventionsCount += 1
  }
  if (officialVerify) {
    addedD += 0.85
    addedLat += 2.5
    interventionsCount += 1
  }

  const pressurePenalty = (pressureLevel - 1) * 0.1
  const simD = Math.max(0.2, profile.baseD - pressurePenalty + addedD)
  const simLat = profile.baseLat + addedLat
  const latMultiplier = (simLat / profile.baseLat).toFixed(2)

  // 檢出率 (Logistic 映射)
  const prob = 1.0 / (1.0 + Math.exp(-(simD - 1.25) * 1.8))
  const detectionPct = Math.round(prob * 1000) / 10

  // Brier 校準
  const brierDecay = 1.0 - 0.18 * interventionsCount
  const simBrier = Math.max(0.045, profile.baseBrier * brierDecay).toFixed(3)

  // 資產存續率
  const assetPreservation = Math.min(
    100.0,
    Math.max(
      15.0,
      Math.round((detectionPct * 0.95 + (officialVerify ? 4 : 0)) * 10) / 10,
    ),
  )

  const resetAll = () => {
    setSelectedArchetype("impulsive_shopper")
    setPressureLevel(3)
    setCialdiniLens(true)
    setSystem2Brake(true)
    setReflexCard(true)
    setOfficialVerify(true)
  }

  return (
    <div className="space-y-4 pb-12 font-['Plus_Jakarta_Sans',sans-serif]">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-amber-500/30 bg-gradient-to-br from-amber-500/10 via-slate-900/90 to-slate-900/90 p-5 shadow-[0_0_25px_rgba(245,158,11,0.08)] backdrop-blur-xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-amber-400/10 border border-amber-400/30">
              <Sliders className="w-5 h-5 text-amber-300" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-wide">
                認知實驗動態沙盒（Cognitive Simulation Sandbox）
              </h2>
              <p className="text-xs text-slate-400">
                大專生競賽評審實時操控室 ·
                動態驗證雙歷程煞車與訊號穿透敏感度變化
              </p>
            </div>
          </div>
          <button
            onClick={resetAll}
            className="flex items-center gap-1 text-[11px] font-bold rounded-lg border border-white/20 bg-white/5 px-2.5 py-1 text-slate-300 hover:bg-white/15 transition-all cursor-pointer"
          >
            <RefreshCw className="w-3 h-3" />
            <span>重設參數</span>
          </button>
        </div>
      </div>

      {/* Control Panel 1: Player Archetype */}
      <div className="rounded-2xl border border-white/20 bg-slate-900/80 p-4 shadow-sm backdrop-blur-xl space-y-2.5">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
          <Scale className="w-4 h-4 text-white" />
          <span>1. 選擇受試者行為原型 (Player Archetype)</span>
        </span>
        <div className="grid grid-cols-2 gap-2">
          {ARCHETYPES.map((a) => {
            const isSelected = selectedArchetype === a.key
            return (
              <button
                key={a.key}
                onClick={() => setSelectedArchetype(a.key)}
                className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                  isSelected
                    ? "border-amber-400/60 bg-amber-400/15 shadow-[0_0_15px_rgba(245,158,11,0.15)]"
                    : "border-white/10 bg-white/5 hover:bg-white/10"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span
                    className={`text-xs font-bold ${isSelected ? "text-amber-200" : "text-white"}`}
                  >
                    {a.name}
                  </span>
                  {isSelected && (
                    <Check className="w-3.5 h-3.5 text-amber-400" />
                  )}
                </div>
                <p className="text-[10px] text-slate-400 mt-1 line-clamp-1">
                  {a.subtitle}
                </p>
              </button>
            )
          })}
        </div>
      </div>

      {/* Control Panel 2: Weakness Pressure Level */}
      <div className="rounded-2xl border border-white/20 bg-slate-900/80 p-4 shadow-sm backdrop-blur-xl space-y-2.5">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
            <Zap className="w-4 h-4 text-white" />
            <span>2. 詐騙話術施壓烈度 (Weakness Pressure Level)</span>
          </span>
          <span className="text-xs font-mono font-bold text-amber-300">
            Level {pressureLevel} / 5 (
            {pressureLevel >= 4
              ? "極限威脅"
              : pressureLevel >= 2
                ? "標準話術"
                : "輕度試水"}
            )
          </span>
        </div>
        <div className="grid grid-cols-5 gap-1.5">
          {[1, 2, 3, 4, 5].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setPressureLevel(lvl)}
              className={`py-2 text-xs font-mono font-bold rounded-lg border transition-all cursor-pointer ${
                pressureLevel === lvl
                  ? "border-rose-500 bg-rose-500/20 text-rose-300 shadow-[0_0_10px_rgba(244,63,94,0.3)]"
                  : "border-white/10 bg-white/5 text-slate-400 hover:bg-white/10"
              }`}
            >
              L{lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Control Panel 3: Four Cognitive Interventions */}
      <div className="rounded-2xl border border-white/20 bg-slate-900/80 p-4 shadow-sm backdrop-blur-xl space-y-2.5">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>3. 認知介入防禦組件 (Cognitive Interventions)</span>
          </span>
          <span className="text-[10px] font-bold text-emerald-400">
            已激活 {interventionsCount} / 4 項介入
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {/* Cialdini Lens */}
          <button
            onClick={() => setCialdiniLens(!cialdiniLens)}
            className={`p-3 rounded-xl border flex items-center justify-between text-left transition-all cursor-pointer ${
              cialdiniLens
                ? "border-emerald-500/50 bg-emerald-500/10 text-white"
                : "border-white/10 bg-white/5 text-slate-400"
            }`}
          >
            <div className="flex items-center gap-2">
              <Eye
                className={`w-4 h-4 ${cialdiniLens ? "text-emerald-400" : "text-slate-500"}`}
              />
              <div>
                <span className="text-xs font-bold block">說服心理透視鏡</span>
                <span className="text-[10px] text-slate-400 block">
                  Cialdini 7 Weapons
                </span>
              </div>
            </div>
            <div
              className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                cialdiniLens
                  ? "border-emerald-400 bg-emerald-400"
                  : "border-slate-600"
              }`}
            >
              {cialdiniLens && (
                <Check className="w-3 h-3 text-slate-950 font-bold" />
              )}
            </div>
          </button>

          {/* System 2 Brake */}
          <button
            onClick={() => setSystem2Brake(!system2Brake)}
            className={`p-3 rounded-xl border flex items-center justify-between text-left transition-all cursor-pointer ${
              system2Brake
                ? "border-emerald-500/50 bg-emerald-500/10 text-white"
                : "border-white/10 bg-white/5 text-slate-400"
            }`}
          >
            <div className="flex items-center gap-2">
              <Clock
                className={`w-4 h-4 ${system2Brake ? "text-emerald-400" : "text-slate-500"}`}
              />
              <div>
                <span className="text-xs font-bold block">雙歷程慢想煞車</span>
                <span className="text-[10px] text-slate-400 block">
                  Kahneman System 2
                </span>
              </div>
            </div>
            <div
              className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                system2Brake
                  ? "border-emerald-400 bg-emerald-400"
                  : "border-slate-600"
              }`}
            >
              {system2Brake && (
                <Check className="w-3 h-3 text-slate-950 font-bold" />
              )}
            </div>
          </button>

          {/* Reflex Card */}
          <button
            onClick={() => setReflexCard(!reflexCard)}
            className={`p-3 rounded-xl border flex items-center justify-between text-left transition-all cursor-pointer ${
              reflexCard
                ? "border-emerald-500/50 bg-emerald-500/10 text-white"
                : "border-white/10 bg-white/5 text-slate-400"
            }`}
          >
            <div className="flex items-center gap-2">
              <Zap
                className={`w-4 h-4 ${reflexCard ? "text-emerald-400" : "text-slate-500"}`}
              />
              <div>
                <span className="text-xs font-bold block">
                  執行意圖條件反射卡
                </span>
                <span className="text-[10px] text-slate-400 block">
                  Gollwitzer IF-THEN
                </span>
              </div>
            </div>
            <div
              className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                reflexCard
                  ? "border-emerald-400 bg-emerald-400"
                  : "border-slate-600"
              }`}
            >
              {reflexCard && (
                <Check className="w-3 h-3 text-slate-950 font-bold" />
              )}
            </div>
          </button>

          {/* Official Verification */}
          <button
            onClick={() => setOfficialVerify(!officialVerify)}
            className={`p-3 rounded-xl border flex items-center justify-between text-left transition-all cursor-pointer ${
              officialVerify
                ? "border-emerald-500/50 bg-emerald-500/10 text-white"
                : "border-white/10 bg-white/5 text-slate-400"
            }`}
          >
            <div className="flex items-center gap-2">
              <Search
                className={`w-4 h-4 ${officialVerify ? "text-emerald-400" : "text-slate-500"}`}
              />
              <div>
                <span className="text-xs font-bold block">
                  司法行政事實查證
                </span>
                <span className="text-[10px] text-slate-400 block">
                  FSC / 165 Independent Audit
                </span>
              </div>
            </div>
            <div
              className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                officialVerify
                  ? "border-emerald-400 bg-emerald-400"
                  : "border-slate-600"
              }`}
            >
              {officialVerify && (
                <Check className="w-3 h-3 text-slate-950 font-bold" />
              )}
            </div>
          </button>
        </div>
      </div>

      {/* Real-time Dynamic Simulation Output Dashboard */}
      <div className="rounded-2xl border border-sky-500/30 bg-slate-900/90 p-5 shadow-[0_0_30px_rgba(56,189,248,0.08)] backdrop-blur-xl space-y-4">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-sky-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-sky-300">
              即時預測評量指標（Simulated Cognitive Outcomes）
            </h3>
          </div>
          <span className="rounded-full border border-sky-400/30 bg-sky-400/10 px-2 py-0.5 text-[10px] font-mono font-bold text-sky-300">
            動態模擬生效中
          </span>
        </div>

        {/* 4 Core Predicted Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          <div className="rounded-xl border border-white/10 bg-white/5 p-3">
            <span className="text-[10px] text-slate-400 block">
              決策沉思時長
            </span>
            <span className="text-lg font-bold font-mono text-white block mt-0.5">
              {simLat.toFixed(1)}s
            </span>
            <span className="text-[9px] text-emerald-400 font-bold block mt-0.5">
              基準 {profile.baseLat}s ({latMultiplier}x 煞車)
            </span>
          </div>

          <div className="rounded-xl border border-white/10 bg-white/5 p-3">
            <span className="text-[10px] text-slate-400 block">
              穿透敏感度 (d')
            </span>
            <span className="text-lg font-bold font-mono text-emerald-400 block mt-0.5">
              {simD.toFixed(2)}
            </span>
            <span className="text-[9px] text-emerald-300 font-bold block mt-0.5">
              {simD >= 2.5
                ? "頂尖特級 (PR 95+)"
                : simD >= 1.5
                  ? "良好水準"
                  : "易感脆弱"}
            </span>
          </div>

          <div className="rounded-xl border border-white/10 bg-white/5 p-3">
            <span className="text-[10px] text-slate-400 block">
              詐騙識破檢出率
            </span>
            <span className="text-lg font-bold font-mono text-sky-300 block mt-0.5">
              {detectionPct}%
            </span>
            <span className="text-[9px] text-slate-400 block mt-0.5">
              穿透詐騙偽裝機率
            </span>
          </div>

          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3">
            <span className="text-[10px] text-amber-300/80 block">
              校準誤差 (Brier)
            </span>
            <span className="text-lg font-bold font-mono text-amber-300 block mt-0.5">
              {simBrier}
            </span>
            <span className="text-[9px] text-emerald-400 block mt-0.5 truncate">
              {Number(simBrier) <= 0.08 ? "良性理性校準" : "過度自信風險"}
            </span>
          </div>
        </div>

        {/* Expected Asset Preservation Bar */}
        <div className="rounded-xl border border-white/10 bg-white/5 p-3 space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-300 font-bold">
              預估資產存續率 (Asset Preservation Rate)
            </span>
            <span className="font-mono text-emerald-400 font-bold">
              {assetPreservation}%
            </span>
          </div>
          <div className="h-2 w-full rounded-full bg-white/10 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-500"
              style={{ width: `${assetPreservation}%` }}
            />
          </div>
        </div>

        {/* Pedagogical Takeaway */}
        <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-xs leading-relaxed text-slate-300">
          <span className="font-bold text-amber-300 mr-1.5">
            評審實證結論：
          </span>
          {interventionsCount >= 3
            ? `當受試者配置多重認知防禦（透視鏡、慢想煞車與客觀查證）時，前額葉決策時間自 ${profile.baseLat}s 延長至 ${simLat.toFixed(1)}s，成功阻斷熱認知心理劫持，檢出率自初始低谷躍升至 ${detectionPct}%。`
            : interventionsCount >= 1
              ? `受試者具備基礎煞車（時長 ${simLat.toFixed(1)}s），但在高壓話術下仍有情緒突破破綻，需進一步結合獨立事實查證以達到完全防護。`
              : `完全無介入狀態下，受試者在前額葉直覺裸奔狀態下作答，反應時間僅 ${profile.baseLat}s，極易被貪念或恐懼直接攻破。`}
        </div>
      </div>
    </div>
  )
}
