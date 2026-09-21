import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  HeartHandshake,
  Paperclip,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react"
import { type ComponentType, useEffect, useState } from "react"
import type { RewardBreakdown, ScenarioJudgeResponse } from "@/client"

const OUTCOME_META: Record<
  string,
  {
    icon: ComponentType<{ className?: string }>
    title: string
    win: boolean
    flagsTitle: string
  }
> = {
  win_report: {
    icon: ShieldCheck,
    title: "識破成功!",
    win: true,
    flagsTitle: "你抓到的破綻",
  },
  win_trust: {
    icon: HeartHandshake,
    title: "正確信任!",
    win: true,
    flagsTitle: "對方的正當訊號",
  },
  lose_scammed: {
    icon: ShieldAlert,
    title: "你被騙了…",
    win: false,
    flagsTitle: "你錯過的警訊",
  },
  lose_misreport: {
    icon: AlertCircle,
    title: "誤判了好人…",
    win: false,
    flagsTitle: "對方其實有這些正當訊號",
  },
  safe_exit: {
    icon: ShieldCheck,
    title: "謹慎處置成功!",
    win: true,
    flagsTitle: "存疑停損與查證核對紀錄",
  },
  paused: {
    icon: ShieldCheck,
    title: "已暫停調查",
    win: true,
    flagsTitle: "已封存事證",
  },
}

const ROLE_LABELS: Record<string, string> = {
  scam: "詐騙者",
  legit: "正當聯絡人",
  scam_event: "詐騙事件",
  legit_event: "正當事件",
  uncertain_event: "資訊仍不足",
}

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(() => {
    if (typeof window === "undefined" || !window.matchMedia) return true
    try {
      return window.matchMedia("(prefers-reduced-motion: reduce)").matches
    } catch {
      return true
    }
  })

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return
    try {
      const mq = window.matchMedia("(prefers-reduced-motion: reduce)")
      const handler = (e: MediaQueryListEvent) => setReduced(e.matches)
      mq.addEventListener("change", handler)
      return () => mq.removeEventListener("change", handler)
    } catch {
      // ignore
    }
  }, [])

  return reduced
}

export function buildSettlementFormula(breakdown: RewardBreakdown): string {
  if (breakdown.is_replay) {
    return "$0（重玩練習不發放現金與經驗）"
  }
  if (breakdown.base_cash === 0) {
    return "$0（案件處置完成）"
  }

  let formula = `$${breakdown.base_cash.toLocaleString()}`

  if (breakdown.chapter_multiplier > 1) {
    formula += ` × ${breakdown.chapter_multiplier.toFixed(2)}（天梯）`
  }

  if (breakdown.is_chapter_finale) {
    formula +=
      breakdown.chapter_multiplier > 1 ? "× 2.50（終局）" : " × 2.50（終局）"
  } else if (breakdown.total_chat_factor > 0) {
    const chatMult = 1.0 + breakdown.total_chat_factor
    const multStr = `${chatMult.toFixed(2)}（本案）`
    formula +=
      breakdown.chapter_multiplier > 1 ? `× ${multStr}` : ` × ${multStr}`
  }

  formula += `= $${breakdown.final_cash.toLocaleString()}`
  return formula
}

interface ResultSheetProps {
  result: ScenarioJudgeResponse
  onBack: () => void
  onGoAssets: () => void
}

/** 判斷後的揭曉卡:真實身份 + 破綻/訊號 + 金錢結算 + 強制變賣警示 */
export function ResultSheet({ result, onBack, onGoAssets }: ResultSheetProps) {
  const meta = OUTCOME_META[result.outcome] || {
    icon: ShieldCheck,
    title: "案件處置完成",
    win: true,
    flagsTitle: "處置紀錄",
  }
  const OutcomeIcon = meta.icon
  const isContactStory = result.true_role.endsWith("_event")
  const prefersReducedMotion = usePrefersReducedMotion()

  // 4-beat settlement:
  // Beat 1: base cash countup
  // Beat 2: chapter multiplier on rail -> chapter_subtotal
  // Beat 3: chat / finale bonuses -> final_cash
  // Beat 4: settle (scale 1.03, bright edge, permanent formula)
  const isReplay = result.reward_breakdown?.is_replay === true
  const hasRewardAnim =
    Boolean(result.reward_breakdown) && !isReplay && result.cash_delta > 0

  const [beat, setBeat] = useState<number>(() =>
    prefersReducedMotion || !hasRewardAnim ? 4 : 1,
  )

  useEffect(() => {
    if (prefersReducedMotion || !hasRewardAnim) {
      setBeat(4)
      return
    }

    setBeat(1)
    const t1 = setTimeout(() => setBeat(2), 500)
    const t2 = setTimeout(() => setBeat(3), 1100)
    const t3 = setTimeout(() => setBeat(4), 1800)

    return () => {
      clearTimeout(t1)
      clearTimeout(t2)
      clearTimeout(t3)
    }
  }, [prefersReducedMotion, hasRewardAnim])

  const beadPct =
    beat === 1 ? 25 : beat === 2 ? 60 : beat === 3 ? 85 : 100

  const cashText = `${result.cash_delta >= 0 ? "+" : "-"}$${Math.abs(
    result.cash_delta,
  ).toLocaleString()}`

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-sm overflow-hidden rounded-2xl bg-background border border-white/20 shadow-2xl">
        <div
          className={`px-4 py-6 text-center text-white ${
            meta.win ? "bg-emerald-600" : "bg-rose-600"
          }`}
        >
          <div className="flex justify-center mb-1">
            <OutcomeIcon className="w-12 h-12 text-white" />
          </div>
          <h3 className="mt-1 text-lg font-extrabold">{meta.title}</h3>
          <p className="mt-1 text-xs opacity-90">
            {isContactStory ? "事件真相" : "對方真實身份"}：
            <b>{ROLE_LABELS[result.true_role] ?? "仍待確認"}</b>（
            {result.persona_name}）
          </p>
        </div>
        <div className="p-4">
          <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            {meta.flagsTitle}
          </p>
          <ul className="flex flex-col gap-1.5">
            {result.flags.map((f) => (
              <li
                key={`${f.tag}-${f.detail}`}
                className="text-xs leading-snug flex items-start gap-1.5"
              >
                {f.tag ? (
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-500 shrink-0 mt-0.5" />
                ) : (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                )}
                <span>
                  {f.detail}
                  {f.tag && (
                    <span className="ml-1 rounded bg-rose-500/10 border border-rose-500/20 px-1 py-0.5 text-[9px] font-bold text-rose-400">
                      {f.label}
                    </span>
                  )}
                </span>
              </li>
            ))}
          </ul>
          {result.case_provenance && (
            <div className="mt-2.5 flex items-center gap-1.5 rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-[11px] text-slate-300">
              <Paperclip className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span>本情境素材：{result.case_provenance}</span>
            </div>
          )}

          {/* 席爾迪尼心理操縱手法與認知免疫學術解析 */}
          {(result as any).inoculation && (
            <div className="mt-2.5 rounded-xl border border-amber-500/30 bg-slate-900/80 p-3 text-[11px] text-slate-200">
              <div className="font-bold text-amber-400 flex items-center gap-1 mb-1">
                <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                <span>心理說服槓桿與認知煞車深度解析</span>
              </div>
              <p className="text-slate-300 leading-relaxed">
                {(result as any).inoculation.debrief ||
                  (result as any).inoculation.mechanism ||
                  "對話中對方運用時間緊迫感、專業威信與互惠誘因引導認知卸防，本案已成功記錄於雙歷程認知免疫數據庫。"}
              </p>
              {(result as any).inoculation.countermeasure && (
                <div className="mt-1.5 text-emerald-400 font-medium">
                  關鍵防禦思維：{(result as any).inoculation.countermeasure}
                </div>
              )}
            </div>
          )}

          {/* 獎勵明細核算與 4-beat Multiplier Countup */}
          {result.reward_breakdown && (
            <div
              className="mt-2.5 rounded-xl border border-slate-700/60 bg-slate-900/90 p-3 text-[11px] text-slate-300 select-none"
              onClick={() => setBeat(4)}
              title={hasRewardAnim ? "點擊可直接完成結算" : undefined}
            >
              <div className="font-bold text-slate-100 flex items-center justify-between mb-1.5">
                <span>獎勵明細核算</span>
                {result.reward_breakdown.is_replay && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                    純練習重玩
                  </span>
                )}
              </div>
              {result.reward_breakdown.is_replay ? (
                <p className="text-amber-300/90 text-[10px]">
                  重玩已完成事件為純練習模式：不發放現金、經驗與關係進度。
                </p>
              ) : (
                <div className="space-y-1 text-slate-400">
                  <div className="flex justify-between">
                    <span>基礎事件報酬</span>
                    <span className="font-mono text-slate-200">
                      ${result.reward_breakdown.base_cash}
                    </span>
                  </div>
                  {result.reward_breakdown.chapter_multiplier > 1 && (
                    <div className="flex justify-between">
                      <span>
                        章節加成 ({result.reward_breakdown.chapter_level} 級)
                      </span>
                      <span className="font-mono text-emerald-400">
                        {result.reward_breakdown.chapter_multiplier}x
                        {result.reward_breakdown.chapter_subtotal && (
                          <span className="ml-1 text-[10px] text-slate-400">
                            （小計 ${result.reward_breakdown.chapter_subtotal.toLocaleString()}）
                          </span>
                        )}
                      </span>
                    </div>
                  )}
                  {result.reward_breakdown.is_chapter_finale && (
                    <div className="flex justify-between text-indigo-300">
                      <span>章節終局加成</span>
                      <span className="font-mono">2.5x</span>
                    </div>
                  )}
                  {result.reward_breakdown.total_chat_factor > 0 && (
                    <div className="flex justify-between text-emerald-300">
                      <span>本次協助加成</span>
                      <span className="font-mono">
                        +{Math.round(result.reward_breakdown.total_chat_factor * 100)}%
                      </span>
                    </div>
                  )}
                  {Object.keys(result.reward_breakdown.chat_bonuses).length > 0 && (
                    <div className="border-t border-slate-800 pt-1 space-y-0.5 text-[10px] text-slate-400">
                      {result.reward_breakdown.chat_bonuses.new_referral && (
                        <div className="flex justify-between text-sky-400">
                          <span>首度推薦加成</span>
                          <span className="font-mono">+20%</span>
                        </div>
                      )}
                      {result.reward_breakdown.chat_bonuses.effective_tool_info && (
                        <div className="flex justify-between text-indigo-400">
                          <span>有效道具調查加成</span>
                          <span className="font-mono">+10%</span>
                        </div>
                      )}
                      {result.reward_breakdown.chat_bonuses.full_service_objective && (
                        <div className="flex justify-between text-emerald-400">
                          <span>服務目標達成加成</span>
                          <span className="font-mono">+20%</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* 4-beat metal bead along short rail */}
                  {hasRewardAnim && (
                    <div className="pt-2 border-t border-slate-800/80">
                      <div className="relative my-2 h-1.5 w-full rounded-full bg-slate-800 border border-slate-700/50 shadow-inner overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-emerald-600 via-teal-400 to-emerald-400 transition-all duration-300 ease-out"
                          style={{ width: `${beadPct}%` }}
                        />
                        <div
                          className="absolute top-1/2 -translate-y-1/2 size-3 rounded-full bg-gradient-to-b from-white via-slate-200 to-slate-400 border border-white shadow-[0_0_8px_rgba(255,255,255,0.7)] transition-all duration-300 ease-out"
                          style={{ left: `calc(${beadPct}% - 6px)` }}
                        />
                      </div>
                      <div className="flex justify-between text-[9px] font-mono text-slate-400">
                        <span className={beat >= 1 ? "text-emerald-300 font-semibold" : ""}>
                          基礎 ${result.reward_breakdown.base_cash}
                        </span>
                        {result.reward_breakdown.chapter_multiplier > 1 && (
                          <span className={beat >= 2 ? "text-emerald-300 font-semibold" : ""}>
                            天梯 ×{result.reward_breakdown.chapter_multiplier}
                          </span>
                        )}
                        {(result.reward_breakdown.is_chapter_finale ||
                          result.reward_breakdown.total_chat_factor > 0) && (
                          <span className={beat >= 3 ? "text-indigo-300 font-semibold" : ""}>
                            {result.reward_breakdown.is_chapter_finale
                              ? "終局 ×2.5"
                              : `本案 +${Math.round(result.reward_breakdown.total_chat_factor * 100)}%`}
                          </span>
                        )}
                        <span className={beat >= 4 ? "text-white font-bold" : ""}>
                          結算
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Permanent formula */}
              <div
                data-testid="settlement-formula"
                className="mt-2.5 rounded-lg bg-black/40 border border-slate-700/60 px-2 py-1.5 font-mono text-[10px] text-slate-200 text-center tracking-tight"
              >
                {buildSettlementFormula(result.reward_breakdown)}
              </div>
            </div>
          )}

          <div
            className={`mt-3 flex items-center justify-between rounded-xl px-3 py-2.5 transition-all duration-300 ${
              meta.win
                ? beat >= 4
                  ? "bg-emerald-950/50 border-[1.5px] border-emerald-400/50 shadow-[0_0_12px_rgba(16,185,129,0.15)]"
                  : "bg-emerald-950/40 border border-emerald-500/20"
                : "bg-rose-950/40 border border-rose-500/20"
            }`}
          >
            <span className="text-xs font-bold text-slate-200">
              {result.cash_delta >= 0 ? "獎勵" : "損失"}
            </span>
            <span
              className={`text-base font-extrabold font-mono transition-transform duration-200 ${
                beat >= 4 ? "scale-[1.03]" : ""
              } ${
                result.cash_delta >= 0 ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {cashText}
              {result.xp_delta > 0 && ` · +${result.xp_delta} XP`}
            </span>
          </div>
          {result.triggers_forced_sell && (
            <div className="mt-2.5 flex items-center gap-1.5 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-300">
              <AlertCircle className="w-4 h-4 shrink-0 text-amber-400" />
              <span>
                現金不足觸發強制變賣，需變賣房產償還，請前往資產頁處理。
              </span>
            </div>
          )}
          <button
            type="button"
            onClick={result.triggers_forced_sell ? onGoAssets : onBack}
            className="mt-3 w-full rounded-xl bg-foreground py-2.5 text-sm font-bold text-background"
          >
            {result.triggers_forced_sell ? "查看資產 ›" : "回到聯絡人 ›"}
          </button>
        </div>
      </div>
    </div>
  )
}
