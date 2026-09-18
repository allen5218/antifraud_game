import { useState } from "react"
import type { QuizVerificationPublic } from "@/client"
import { Button } from "@/components/ui/button"

interface VerificationQuestionProps {
  item: QuizVerificationPublic
  index: number
  total: number
  disabled: boolean
  onSubmit: (selectedOption: string) => void
}

/** 查證問答題：針對情境選擇下一步最佳查證途徑或證據意涵。 */
export function VerificationQuestion({
  item,
  index,
  total,
  disabled,
  onSubmit,
}: VerificationQuestionProps) {
  const [selectedKey, setSelectedKey] = useState<string | null>(null)

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 px-4 pt-3 text-xs text-muted-foreground">
        <span className="rounded-md bg-amber-500/10 px-1.5 py-0.5 font-semibold text-amber-600 dark:text-amber-400">
          查證處置
        </span>
        <span className="ml-auto">
          {index + 1} / {total}
        </span>
      </div>
      <div className="flex-1 overflow-y-auto px-4 pb-4">
        <h2 className="pt-2 text-base font-bold">{item.title}</h2>
        <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
          {item.narrative}
        </p>
        <div className="mt-4">
          <h3 className="text-sm font-bold text-foreground">{item.question}</h3>
        </div>
        <div className="mt-3 grid gap-2.5">
          {item.options.map((option) => {
            const isSelected = selectedKey === option.key
            return (
              <button
                key={option.key}
                type="button"
                disabled={disabled}
                onClick={() => setSelectedKey(option.key)}
                className={`flex items-start gap-3 rounded-xl border p-3 text-left transition-colors ${
                  isSelected
                    ? "border-primary bg-primary/5 ring-1 ring-primary"
                    : "border-border bg-card hover:bg-accent/40"
                }`}
              >
                <span
                  className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                    isSelected
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {option.key.toUpperCase()}
                </span>
                <span className="text-sm leading-normal">{option.text}</span>
              </button>
            )
          })}
        </div>
      </div>
      <div className="border-t border-border bg-background p-3">
        <Button
          type="button"
          disabled={disabled || !selectedKey}
          onClick={() => selectedKey && onSubmit(selectedKey)}
          className="w-full rounded-xl py-3 text-sm font-bold"
        >
          確認送出查證決策
        </Button>
      </div>
    </div>
  )
}
