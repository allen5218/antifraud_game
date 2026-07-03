import { FRAUD_TYPE_LABELS } from "@/components/scenario/labels"

interface QuizCardProps {
  fraudType: string
  title: string
  narrative: string
  difficulty: number
  index: number
  total: number
  onJudge: (guessIsScam: boolean) => void
  disabled: boolean
}

/** 長敘事題卡:可捲動全文 + 底部判斷雙鈕 */
export function QuizCard({
  fraudType,
  title,
  narrative,
  difficulty,
  index,
  total,
  onJudge,
  disabled,
}: QuizCardProps) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 px-4 pt-3 text-xs text-muted-foreground">
        <span className="rounded-md bg-primary/10 px-1.5 py-0.5 font-semibold text-primary">
          {FRAUD_TYPE_LABELS[fraudType] ?? fraudType}
        </span>
        <span>{"★".repeat(difficulty)}</span>
        <span className="ml-auto">
          {index + 1} / {total}
        </span>
      </div>
      <h2 className="px-4 pt-2 text-base font-bold">{title}</h2>
      <div className="mt-2 flex-1 overflow-y-auto px-4 pb-4">
        <p className="whitespace-pre-wrap text-sm leading-relaxed">
          {narrative}
        </p>
      </div>
      <div className="flex gap-2 border-t border-border bg-background p-3">
        <button
          type="button"
          disabled={disabled}
          onClick={() => onJudge(true)}
          className="flex-1 rounded-xl bg-red-500 py-3 text-sm font-bold text-white disabled:opacity-50"
        >
          🚩 這是詐騙
        </button>
        <button
          type="button"
          disabled={disabled}
          onClick={() => onJudge(false)}
          className="flex-1 rounded-xl bg-green-600 py-3 text-sm font-bold text-white disabled:opacity-50"
        >
          ✅ 這是正當
        </button>
      </div>
    </div>
  )
}
