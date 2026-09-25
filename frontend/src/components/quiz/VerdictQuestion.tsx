import { Flag, ShieldCheck } from "lucide-react"
import type { QuizVerdictPublic } from "@/client"
import { QuestionMeta } from "./QuestionMeta"

interface VerdictQuestionProps {
  item: QuizVerdictPublic
  index: number
  total: number
  disabled: boolean
  onSubmit: (guessIsScam: boolean) => void
}

/** 是非判斷題：閱讀完整敘事後判斷是否為詐騙。 */
export function VerdictQuestion({
  item,
  index,
  total,
  disabled,
  onSubmit,
}: VerdictQuestionProps) {
  return (
    <div className="flex h-full flex-col">
      <QuestionMeta
        fraudType={item.fraud_type}
        difficulty={item.difficulty}
        index={index}
        total={total}
      />
      <h2 className="px-4 pt-2 text-base font-bold">{item.title}</h2>
      <div className="mt-2 flex-1 overflow-y-auto px-4 pb-4">
        <p className="whitespace-pre-wrap text-sm leading-relaxed">
          {item.narrative}
        </p>
      </div>
      <div className="flex gap-2 border-t border-border bg-background p-3">
        <button
          type="button"
          disabled={disabled}
          onClick={() => onSubmit(true)}
          className="flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-scam py-3 text-sm font-bold text-scam-foreground disabled:opacity-50"
        >
          <Flag aria-hidden className="size-4" />
          這是詐騙
        </button>
        <button
          type="button"
          disabled={disabled}
          onClick={() => onSubmit(false)}
          className="flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-legit py-3 text-sm font-bold text-legit-foreground disabled:opacity-50"
        >
          <ShieldCheck aria-hidden className="size-4" />
          這是正常的
        </button>
      </div>
    </div>
  )
}
