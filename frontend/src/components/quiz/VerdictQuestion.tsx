import { useEffect, useRef, useState } from "react"
import type { QuizVerdictPublic } from "@/client"

export interface VerdictSignals {
  response_time_ms: number
  option_switch_count: number
  interaction_obscured: boolean
}

interface VerdictQuestionProps {
  item: QuizVerdictPublic
  index: number
  total: number
  disabled: boolean
  onSubmit: (guessIsScam: boolean, signals?: VerdictSignals) => void
}

function sanitizeTitle(title: string): string {
  if (!title) return "情境案例"
  const cleaned = title
    .replace(/【.*?】/g, "")
    .replace(/陷阱|詐騙|詐欺|騙局|假買家|假物流|假客服|假冒|假|關懷|正派/g, "")
    .trim()
  return cleaned || "通訊情境"
}

/** 情境判斷題：閱讀短情境後，表達直覺判斷並確認。 */
export function VerdictQuestion({
  item,
  index,
  total,
  disabled,
  onSubmit,
}: VerdictQuestionProps) {
  const [selectedGuess, setSelectedGuess] = useState<boolean | null>(null)
  const switchCountRef = useRef(0)
  const mountTimeRef = useRef<number>(Date.now())
  const obscuredRef = useRef(false)

  useEffect(() => {
    const handleVisibility = () => {
      if (
        typeof document !== "undefined" &&
        document.visibilityState === "hidden"
      ) {
        obscuredRef.current = true
      }
    }
    document.addEventListener("visibilitychange", handleVisibility)
    return () => {
      document.removeEventListener("visibilitychange", handleVisibility)
    }
  }, [])

  const handleSelect = (guess: boolean) => {
    if (disabled) return
    setSelectedGuess((prev) => {
      if (prev !== null && prev !== guess) {
        switchCountRef.current += 1
      }
      return guess
    })
  }

  const handleConfirm = () => {
    if (selectedGuess === null || disabled) return
    const elapsed = Math.max(0, Math.round(Date.now() - mountTimeRef.current))
    onSubmit(selectedGuess, {
      response_time_ms: elapsed,
      option_switch_count: switchCountRef.current,
      interaction_obscured: obscuredRef.current,
    })
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 px-4 pt-3 text-xs text-muted-foreground">
        <span className="rounded-md bg-white/10 px-2 py-0.5 font-semibold text-slate-300 border border-white/10">
          你覺得呢？
        </span>
        <span className="ml-auto">
          {index + 1} / {total}
        </span>
      </div>
      <h2 className="px-4 pt-2 text-base font-bold text-white">
        {sanitizeTitle(item.title)}
      </h2>
      <div className="mt-2 flex-1 overflow-y-auto px-4 pb-4">
        <p className="whitespace-pre-wrap text-sm leading-relaxed">
          {item.narrative}
        </p>
      </div>

      <div className="border-t border-border bg-background p-3 space-y-2">
        <div className="flex gap-2">
          <button
            type="button"
            disabled={disabled}
            onClick={() => handleSelect(true)}
            className={`flex-1 rounded-xl py-3 text-sm font-bold transition-all border ${
              selectedGuess === true
                ? "bg-red-500/20 text-red-300 border-red-500 shadow-sm ring-1 ring-red-500"
                : "border-border/60 bg-muted/40 text-muted-foreground hover:bg-muted/70"
            }`}
          >
            我覺得有問題
          </button>
          <button
            type="button"
            disabled={disabled}
            onClick={() => handleSelect(false)}
            className={`flex-1 rounded-xl py-3 text-sm font-bold transition-all border ${
              selectedGuess === false
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500 shadow-sm ring-1 ring-emerald-500"
                : "border-border/60 bg-muted/40 text-muted-foreground hover:bg-muted/70"
            }`}
          >
            我覺得還好
          </button>
        </div>

        <button
          type="button"
          disabled={disabled || selectedGuess === null}
          onClick={handleConfirm}
          className="w-full rounded-xl bg-foreground py-2.5 text-sm font-bold text-background disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-200 transition-colors"
        >
          就這樣
        </button>
      </div>
    </div>
  )
}
