import { useState } from "react"
import type { QuizVerificationPublic } from "@/client"
import { FRAUD_TYPE_LABELS } from "@/components/scenario/labels"
import { Button } from "@/components/ui/button"

interface VerificationQuestionProps {
  item: QuizVerificationPublic
  index: number
  total: number
  disabled: boolean
  onSubmit: (selectedKey: string) => void
}

/**
 * 查證題：單選，問「下一步該怎麼查證」或「這個證據能證明什麼」。
 *
 * 與其他三種題型問的不一樣——那三種問「這是不是詐騙」的變體，這題問「接下來做什麼」。
 * 現實中受害者往往認得出可疑，卻不知道下一步，於是被對方牽著走完流程。
 */
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
        <span className="rounded-md bg-primary/10 px-1.5 py-0.5 font-semibold text-primary">
          {FRAUD_TYPE_LABELS[item.fraud_type] ?? "其他類型"}
        </span>
        <span>{"★".repeat(item.difficulty)}</span>
        <span className="ml-auto">
          {index + 1} / {total}
        </span>
      </div>
      <div className="flex-1 overflow-y-auto px-4 pb-4">
        <h2 className="pt-2 text-base font-bold">{item.title}</h2>
        <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed">
          {item.narrative}
        </p>
        <h3 id="verification-prompt" className="mt-4 text-sm font-bold">
          {item.question}
        </h3>
        {/* 用原生 radio 而不是 role="radio" 的按鈕:三個選項互斥,需要成組語意,
            否則螢幕閱讀器只會讀到三顆各自獨立的按鈕。原生 radio 還免費附帶
            方向鍵切換;自己用按鈕實作得補 roving tabindex 才有同樣效果。
            話術題是複選所以用核取方塊，這裡不能照抄。 */}
        <fieldset disabled={disabled} className="mt-3 grid gap-2 border-0 p-0">
          <legend className="sr-only">{item.question}</legend>
          {item.options.map((option) => {
            const checked = selectedKey === option.key
            return (
              <label
                key={option.key}
                className={`flex items-start gap-3 rounded-xl border p-3 text-left text-sm transition-colors focus-within:ring-2 focus-within:ring-ring ${
                  checked ? "border-primary bg-primary/10" : "bg-card"
                } ${disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
              >
                <input
                  type="radio"
                  name="verification-option"
                  value={option.key}
                  checked={checked}
                  onChange={() => setSelectedKey(option.key)}
                  className="sr-only"
                />
                <span
                  aria-hidden="true"
                  className={`mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full border text-[11px] font-bold ${
                    checked
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-border text-muted-foreground"
                  }`}
                >
                  {option.key}
                </span>
                <span className="font-medium">{option.text}</span>
              </label>
            )
          })}
        </fieldset>
      </div>
      <div className="border-t border-border bg-background p-3">
        <Button
          type="button"
          disabled={disabled || selectedKey === null}
          onClick={() => selectedKey !== null && onSubmit(selectedKey)}
          className="h-11 w-full rounded-xl font-bold"
        >
          送出答案
        </Button>
      </div>
    </div>
  )
}
