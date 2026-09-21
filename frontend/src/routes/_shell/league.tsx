import { createFileRoute } from "@tanstack/react-router"
import {
  Check,
  Compass,
  GraduationCap,
  Shield,
  Sparkles,
  Trophy,
} from "lucide-react"
import { useState } from "react"

export const Route = createFileRoute("/_shell/league")({
  component: CollegiateLeaguePage,
})

interface UniversityCohort {
  id: string
  name: string
  short_name: string
  motto: string
  active_investigators: number
  total_cases_audited: number
  avg_d_prime: number
  avg_brier_score: number
  guardians_protected: number
  defense_points: number
  shield_tier: "gold" | "silver" | "bronze"
  shield_tier_label: string
  rank: number
}

const SEED_COHORTS: UniversityCohort[] = [
  {
    id: "ntu",
    name: "國立臺灣大學",
    short_name: "臺大 NTU",
    motto: "敦品勵學 · 智慧破防捍衛正義",
    active_investigators: 328,
    total_cases_audited: 4210,
    avg_d_prime: 2.94,
    avg_brier_score: 0.051,
    guardians_protected: 940,
    defense_points: 142800,
    shield_tier: "gold",
    shield_tier_label: "全國頂尖金盾陣線",
    rank: 1,
  },
  {
    id: "nthu",
    name: "國立清華大學",
    short_name: "清大 NTHU",
    motto: "自強不息 · 認知理性嚴謹查證",
    active_investigators: 295,
    total_cases_audited: 3890,
    avg_d_prime: 2.91,
    avg_brier_score: 0.054,
    guardians_protected: 875,
    defense_points: 136500,
    shield_tier: "gold",
    shield_tier_label: "全國頂尖金盾陣線",
    rank: 2,
  },
  {
    id: "nycu",
    name: "國立陽明交通大學",
    short_name: "陽明交大 NYCU",
    motto: "知新致遠 · 數位韌性情報先驅",
    active_investigators: 284,
    total_cases_audited: 3720,
    avg_d_prime: 2.89,
    avg_brier_score: 0.058,
    guardians_protected: 830,
    defense_points: 131200,
    shield_tier: "gold",
    shield_tier_label: "全國頂尖金盾陣線",
    rank: 3,
  },
  {
    id: "ncku",
    name: "國立成功大學",
    short_name: "成大 NCKU",
    motto: "窮理致知 · 南臺社群堅韌守門",
    active_investigators: 260,
    total_cases_audited: 3410,
    avg_d_prime: 2.84,
    avg_brier_score: 0.062,
    guardians_protected: 790,
    defense_points: 121400,
    shield_tier: "silver",
    shield_tier_label: "全國卓越銀盾先鋒",
    rank: 4,
  },
  {
    id: "nccu",
    name: "國立政治大學",
    short_name: "政大 NCCU",
    motto: "親愛精誠 · 司法行政嚴密把關",
    active_investigators: 245,
    total_cases_audited: 3180,
    avg_d_prime: 2.86,
    avg_brier_score: 0.059,
    guardians_protected: 760,
    defense_points: 118900,
    shield_tier: "silver",
    shield_tier_label: "全國卓越銀盾先鋒",
    rank: 5,
  },
  {
    id: "ntpu",
    name: "國立臺北大學",
    short_name: "北大 NTPU",
    motto: "追求真理 · 公共事實嚴格查核",
    active_investigators: 210,
    total_cases_audited: 2740,
    avg_d_prime: 2.78,
    avg_brier_score: 0.066,
    guardians_protected: 640,
    defense_points: 99500,
    shield_tier: "silver",
    shield_tier_label: "全國卓越銀盾先鋒",
    rank: 6,
  },
  {
    id: "ncu",
    name: "國立中央大學",
    short_name: "中央 NCU",
    motto: "誠樸開物 · 空間情境精準拆解",
    active_investigators: 185,
    total_cases_audited: 2360,
    avg_d_prime: 2.72,
    avg_brier_score: 0.071,
    guardians_protected: 550,
    defense_points: 86200,
    shield_tier: "bronze",
    shield_tier_label: "校園新銳青銅衛隊",
    rank: 7,
  },
  {
    id: "nsysu",
    name: "國立中山大學",
    short_name: "中山 NSYSU",
    motto: "山海胸襟 · 全球跨域情報防禦",
    active_investigators: 170,
    total_cases_audited: 2150,
    avg_d_prime: 2.69,
    avg_brier_score: 0.075,
    guardians_protected: 510,
    defense_points: 79800,
    shield_tier: "bronze",
    shield_tier_label: "校園新銳青銅衛隊",
    rank: 8,
  },
]

function CollegiateLeaguePage() {
  const [selectedUnivId, setSelectedUnivId] = useState<string>("ntu")
  const [affiliationNotice, setAffiliationNotice] = useState<string | null>(
    null,
  )

  const myUniv =
    SEED_COHORTS.find((c) => c.id === selectedUnivId) || SEED_COHORTS[0]

  const handleSwitchAffiliation = (id: string, name: string) => {
    setSelectedUnivId(id)
    setAffiliationNotice(`已成功隸屬至 ${name} 防詐防衛陣線！`)
    setTimeout(() => setAffiliationNotice(null), 3000)
  }

  return (
    <div className="space-y-4 pb-12 font-['Plus_Jakarta_Sans',sans-serif]">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-amber-500/30 bg-gradient-to-br from-amber-500/10 via-slate-900/90 to-slate-900/90 p-5 shadow-[0_0_25px_rgba(245,158,11,0.08)] backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-amber-400/10 border border-amber-400/30">
            <Trophy className="w-6 h-6 text-amber-300" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white tracking-wide">
              全國大專跨校聯防天梯（Collegiate Defense League）
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              自我決定論「關聯感（Relatedness）」·
              跨校校譽爭光與社群集體防護天梯
            </p>
          </div>
        </div>

        {affiliationNotice && (
          <div className="mt-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-300 flex items-center gap-2">
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{affiliationNotice}</span>
          </div>
        )}
      </div>

      {/* Vygotsky Zone of Proximal Development (ZPD) Dynamic Flow Monitor */}
      <div className="rounded-2xl border border-sky-500/30 bg-slate-900/80 p-4 shadow-[0_0_20px_rgba(56,189,248,0.06)] backdrop-blur-xl space-y-3">
        <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
          <div className="flex items-center gap-2">
            <Compass className="w-4 h-4 text-sky-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-sky-300">
              維高斯基近側發展區（ZPD Flow）動態平衡儀
            </h3>
          </div>
          <span className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2 py-0.5 text-[10px] font-bold text-emerald-300 flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-emerald-400" />
            <span>最佳心流區間 (+25% 戰備加成)</span>
          </span>
        </div>

        <p className="text-[11px] text-slate-400 leading-relaxed">
          依據 Csikszentmihalyi 心流模型與 Vygotsky
          鷹架理論，動態調控題組難度以防範倦怠或挫敗流失：
        </p>

        <div className="grid grid-cols-3 gap-2 text-center text-xs">
          <div className="rounded-xl border border-white/10 bg-white/5 p-2.5">
            <span className="text-[10px] text-slate-400 block">
              個人穿透敏感度
            </span>
            <span className="text-base font-mono font-bold text-emerald-400 mt-0.5 block">
              d' 2.25
            </span>
            <span className="text-[9px] text-slate-400 mt-0.5 block">
              能力值匹配
            </span>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/5 p-2.5">
            <span className="text-[10px] text-slate-400 block">
              當前情境挑戰係數
            </span>
            <span className="text-base font-mono font-bold text-sky-300 mt-0.5 block">
              1.40x
            </span>
            <span className="text-[9px] text-emerald-400 mt-0.5 block">
              黃金平衡點
            </span>
          </div>
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-2.5">
            <span className="text-[10px] text-amber-300/80 block">
              校準誤差 (Brier)
            </span>
            <span className="text-base font-mono font-bold text-amber-300 mt-0.5 block">
              0.052
            </span>
            <span className="text-[9px] text-emerald-400 mt-0.5 block">
              良性理性自知
            </span>
          </div>
        </div>

        <div className="rounded-xl border border-white/10 bg-white/5 p-2.5 text-xs text-slate-300 space-y-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
            即時認知鷹架介入 (Scaffolding Prescriptions):
          </span>
          <div className="flex items-center gap-1.5 text-[11px] text-emerald-300">
            <Check className="w-3 h-3 text-emerald-400 shrink-0" />
            <span>
              維持動態平衡之話術攻防張力，啟動全域調查賞金 +25% 心流加成
            </span>
          </div>
        </div>
      </div>

      {/* User's Affiliated University Card */}
      <div className="rounded-2xl border border-white/20 bg-slate-900/80 p-4 shadow-sm backdrop-blur-xl">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <GraduationCap className="w-4 h-4 text-white" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              個人當前隸屬校園隊列
            </h3>
          </div>
          <span className="rounded-md border border-amber-400/40 bg-amber-400/10 px-2 py-0.5 text-[10px] font-bold text-amber-300 font-mono">
            全國 Rank #{myUniv.rank}
          </span>
        </div>

        <div className="mt-3 flex items-center justify-between">
          <div>
            <h4 className="text-base font-bold text-white">{myUniv.name}</h4>
            <p className="text-xs text-slate-400 mt-0.5">{myUniv.motto}</p>
          </div>
          <span className="rounded-lg border border-amber-400/30 bg-amber-400/15 px-2.5 py-1 text-xs font-bold text-amber-300">
            {myUniv.shield_tier_label}
          </span>
        </div>

        <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-white/10 text-xs">
          <div className="bg-white/5 rounded-xl p-2 text-center">
            <span className="text-[10px] text-slate-400 block">
              校內個人排名
            </span>
            <span className="text-sm font-mono font-bold text-white mt-0.5 block">
              第 14 名
            </span>
            <span className="text-[9px] text-emerald-400 block mt-0.5">
              PR 95.7
            </span>
          </div>
          <div className="bg-white/5 rounded-xl p-2 text-center">
            <span className="text-[10px] text-slate-400 block">
              個人防護貢獻
            </span>
            <span className="text-sm font-mono font-bold text-amber-300 mt-0.5 block">
              1,420 點
            </span>
            <span className="text-[9px] text-slate-400 block mt-0.5">
              佔全校 1.0%
            </span>
          </div>
          <div className="bg-white/5 rounded-xl p-2 text-center">
            <span className="text-[10px] text-slate-400 block">
              全校守護人數
            </span>
            <span className="text-sm font-mono font-bold text-sky-300 mt-0.5 block">
              {myUniv.guardians_protected} 人
            </span>
            <span className="text-[9px] text-emerald-400 block mt-0.5">
              長者與學生
            </span>
          </div>
        </div>
      </div>

      {/* University Cohorts Leaderboard */}
      <div className="rounded-2xl border border-white/20 bg-slate-900/80 p-4 shadow-sm backdrop-blur-xl space-y-3">
        <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-white" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              全國大專院校聯防陣線天梯榜 (Inter-Collegiate Table)
            </h3>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            8 所代表隊列
          </span>
        </div>

        <div className="space-y-2">
          {SEED_COHORTS.map((c) => {
            const isMyUniv = c.id === selectedUnivId
            return (
              <div
                key={c.id}
                onClick={() => handleSwitchAffiliation(c.id, c.name)}
                className={`p-3 rounded-xl border transition-all cursor-pointer ${
                  isMyUniv
                    ? "border-amber-400/60 bg-amber-400/10 shadow-[0_0_15px_rgba(245,158,11,0.12)]"
                    : "border-white/10 bg-white/5 hover:bg-white/10"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`flex size-7 items-center justify-center rounded-lg font-mono text-xs font-bold ${
                        c.rank === 1
                          ? "bg-amber-400 text-slate-950 shadow-[0_0_10px_rgba(245,158,11,0.5)]"
                          : c.rank === 2
                            ? "bg-slate-300 text-slate-950"
                            : c.rank === 3
                              ? "bg-amber-700 text-white"
                              : "bg-white/10 text-slate-300"
                      }`}
                    >
                      {c.rank}
                    </span>
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-white">
                          {c.name}
                        </span>
                        {isMyUniv && (
                          <span className="rounded bg-amber-400/20 border border-amber-400/30 px-1.5 py-0.2 text-[9px] font-bold text-amber-300">
                            已隸屬
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-400 block mt-0.5">
                        {c.motto}
                      </span>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-xs font-mono font-bold text-amber-300 block">
                      {c.defense_points.toLocaleString()} 點
                    </span>
                    <span className="text-[9px] font-mono text-emerald-400 block">
                      d' {c.avg_d_prime} · {c.active_investigators} 人
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
