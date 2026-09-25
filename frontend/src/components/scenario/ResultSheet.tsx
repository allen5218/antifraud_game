import { Banknote, ChevronRight, Target } from "lucide-react"
import type { ScenarioJudgeResponse } from "@/client"
import { Provenance, SignalItem } from "@/components/quiz/Signals"
import { useDialogFocus } from "@/hooks/useDialogFocus"
import { fraudTypeLabel } from "@/lib/fraudTypes"

/** 結局插圖在 public/assets/outcome/,檔名就是 outcome 值。 */
const OUTCOME_META: Record<
  string,
  { title: string; win: boolean; flagsTitle: string }
> = {
  win_report: {
    title: "識破成功！",
    win: true,
    flagsTitle: "你抓到的破綻",
  },
  win_trust: {
    title: "正確信任！",
    win: true,
    flagsTitle: "看得出對方是正常的地方",
  },
  lose_scammed: {
    title: "你被騙了",
    win: false,
    flagsTitle: "你錯過的警訊",
  },
  lose_misreport: {
    title: "誤判了好人",
    win: false,
    flagsTitle: "其實看得出對方是正常的",
  },
}

const ROLE_LABELS: Record<string, string> = {
  scam: "詐騙者",
  legit: "一般人",
}

/** 結束後直接再練一場練習重點那一類(app/practice/)。 */
export interface NextPractice {
  fraudType: string
  onStart: () => void
  pending: boolean
  /** 開不了的原因(例如今天練滿了) */
  notice: string | null
}

interface ResultSheetProps {
  result: ScenarioJudgeResponse
  onBack: () => void
  onGoAssets: () => void
  next?: NextPractice
}

/** 判斷後的揭曉卡：真實身分、破綻或正常跡象、金錢結算、強制變賣警示。 */
export function ResultSheet({
  result,
  onBack,
  onGoAssets,
  next,
}: ResultSheetProps) {
  // 要先處理變賣時不推薦下一場,免得玩家跳過資產頁
  const showNext = next && !result.triggers_forced_sell
  const dialogRef = useDialogFocus<HTMLDivElement>(true)
  const meta = OUTCOME_META[result.outcome]
  const gained = result.cash_delta >= 0
  const cashText = `${gained ? "+" : "-"}$${Math.abs(
    result.cash_delta,
  ).toLocaleString()}`
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div
        ref={dialogRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="result-sheet-title"
        className="max-h-[90vh] w-full max-w-sm overflow-y-auto rounded-2xl border border-border bg-card outline-none"
      >
        <div
          className={`px-4 py-5 text-center ${
            meta.win
              ? "bg-legit text-legit-foreground"
              : "bg-scam text-scam-foreground"
          }`}
        >
          <img
            src={`/assets/outcome/${result.outcome}.webp`}
            alt=""
            aria-hidden="true"
            width={80}
            height={80}
            className="mx-auto size-20 rounded-full border-2 border-current/30 object-cover"
          />
          <h3 id="result-sheet-title" className="mt-2 text-lg font-extrabold">
            {meta.title}
          </h3>
          <p className="mt-1 text-xs opacity-90">
            對方的真實身分：<b>{ROLE_LABELS[result.true_role]}</b>（
            {result.persona_name}）
          </p>
        </div>
        <div className="p-4">
          <p className="mb-2 text-[11px] font-bold text-muted-foreground">
            {meta.flagsTitle}
          </p>
          <ul className="flex flex-col gap-1.5">
            {result.flags.map((f) => (
              <SignalItem
                key={`${f.tag}-${f.detail}`}
                suspicious={Boolean(f.tag)}
                text={f.detail}
                label={f.label}
              />
            ))}
          </ul>
          {result.case_provenance && (
            <Provenance text={result.case_provenance} className="mt-2" />
          )}
          <div
            className={`mt-3 flex items-center justify-between rounded-xl px-3 py-2.5 ${
              gained ? "bg-legit/15" : "bg-scam/15"
            }`}
          >
            <span className="text-xs font-bold">
              {gained ? "獎勵" : "損失"}
            </span>
            <span
              className={`text-base font-extrabold ${gained ? "text-legit" : "text-scam"}`}
            >
              {cashText}
              {result.xp_delta > 0 && ` · +${result.xp_delta} XP`}
            </span>
          </div>
          {result.triggers_forced_sell && (
            <p className="mt-2 flex gap-1.5 rounded-lg border border-warning/40 bg-warning/15 px-3 py-2 text-[11px]">
              <Banknote
                aria-hidden
                className="mt-px size-3.5 shrink-0 text-warning"
              />
              <span>現金不夠付，要變賣房產來還。請到資產頁處理。</span>
            </p>
          )}
          {showNext && (
            <>
              <button
                type="button"
                onClick={next.onStart}
                disabled={next.pending}
                data-testid="practice-next"
                className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-xl bg-primary py-2.5 text-sm font-bold text-primary-foreground disabled:opacity-50"
              >
                <Target aria-hidden className="size-4" />
                再練一場「{fraudTypeLabel(next.fraudType)}」
              </button>
              <p className="mt-1 text-center text-[11px] text-muted-foreground">
                這是你目前的練習重點
              </p>
              {next.notice && (
                <p
                  role="alert"
                  className="mt-1 text-center text-[11px] text-scam"
                >
                  {next.notice}
                </p>
              )}
            </>
          )}
          <button
            type="button"
            onClick={result.triggers_forced_sell ? onGoAssets : onBack}
            className={`mt-3 flex w-full items-center justify-center gap-1 rounded-xl py-2.5 text-sm font-bold ${
              showNext
                ? "border border-border bg-card text-foreground"
                : "bg-primary text-primary-foreground"
            }`}
          >
            {result.triggers_forced_sell ? "查看資產" : "回到聯絡人"}
            <ChevronRight aria-hidden className="size-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
