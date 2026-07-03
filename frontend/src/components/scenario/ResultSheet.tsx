import type { ScenarioJudgeResponse } from "@/client"

const OUTCOME_META: Record<
  string,
  { icon: string; title: string; win: boolean; flagsTitle: string }
> = {
  win_report: {
    icon: "🎯",
    title: "識破成功!",
    win: true,
    flagsTitle: "你抓到的破綻",
  },
  win_trust: {
    icon: "🤝",
    title: "正確信任!",
    win: true,
    flagsTitle: "對方的正當訊號",
  },
  lose_scammed: {
    icon: "💔",
    title: "你被騙了…",
    win: false,
    flagsTitle: "你錯過的警訊",
  },
  lose_misreport: {
    icon: "😅",
    title: "誤判了好人…",
    win: false,
    flagsTitle: "對方其實有這些正當訊號",
  },
}

const ROLE_LABELS: Record<string, string> = {
  scam: "詐騙者",
  legit: "正當聯絡人",
}

interface ResultSheetProps {
  result: ScenarioJudgeResponse
  onBack: () => void
  onGoAssets: () => void
}

/** 判斷後的揭曉卡:真實身份 + 破綻/訊號 + 金錢結算 + 強制變賣警示 */
export function ResultSheet({ result, onBack, onGoAssets }: ResultSheetProps) {
  const meta = OUTCOME_META[result.outcome]
  const cashText = `${result.cash_delta >= 0 ? "+" : "-"}$${Math.abs(
    result.cash_delta,
  ).toLocaleString()}`
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-sm overflow-hidden rounded-2xl bg-background">
        <div
          className={`px-4 py-6 text-center text-white ${
            meta.win ? "bg-green-600" : "bg-red-600"
          }`}
        >
          <div className="text-4xl">{meta.icon}</div>
          <h3 className="mt-1 text-lg font-extrabold">{meta.title}</h3>
          <p className="mt-1 text-xs opacity-90">
            對方真實身份:<b>{ROLE_LABELS[result.true_role]}</b>(
            {result.persona_name})
          </p>
        </div>
        <div className="p-4">
          <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            {meta.flagsTitle}
          </p>
          <ul className="flex flex-col gap-1.5">
            {result.flags.map((f) => (
              <li key={`${f.tag}-${f.detail}`} className="text-xs leading-snug">
                {f.tag ? "🚩" : "✅"} {f.detail}
                {f.tag && (
                  <span className="ml-1 rounded bg-red-50 px-1 py-0.5 text-[9px] font-bold text-red-600 dark:bg-red-950">
                    {f.label}
                  </span>
                )}
              </li>
            ))}
          </ul>
          {result.case_provenance && (
            <p className="mt-2 rounded-lg bg-muted px-3 py-2 text-[11px] text-muted-foreground">
              {`📎 本情境素材 ${result.case_provenance}`}
            </p>
          )}
          <div
            className={`mt-3 flex items-center justify-between rounded-xl px-3 py-2.5 ${
              meta.win
                ? "bg-green-50 dark:bg-green-950/40"
                : "bg-red-50 dark:bg-red-950/40"
            }`}
          >
            <span className="text-xs font-bold">
              {result.cash_delta >= 0 ? "獎勵" : "損失"}
            </span>
            <span
              className={`text-base font-extrabold ${
                result.cash_delta >= 0 ? "text-green-600" : "text-red-600"
              }`}
            >
              {cashText}
              {result.xp_delta > 0 && ` · +${result.xp_delta} XP`}
            </span>
          </div>
          {result.triggers_forced_sell && (
            <p className="mt-2 rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-[11px] text-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
              💸 現金不足,觸發強制變賣!需要變賣房產償還——前往資產頁處理
            </p>
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
