import { useState } from "react"
import type { QuizTacticsPublic } from "@/client"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { QuestionMeta } from "./QuestionMeta"

interface TacticsQuestionProps {
  item: QuizTacticsPublic
  index: number
  total: number
  disabled: boolean
  onSubmit: (selectedTags: string[]) => void
}

/** 話術辨識題：送出前可自由增減複選答案。 */
export function TacticsQuestion({
  item,
  index,
  total,
  disabled,
  onSubmit,
}: TacticsQuestionProps) {
  const [selectedTags, setSelectedTags] = useState<string[]>([])

  const toggleTag = (tag: string) => {
    if (disabled) return
    setSelectedTags((current) =>
      current.includes(tag)
        ? current.filter((selected) => selected !== tag)
        : [...current, tag],
    )
  }

  return (
    <div className="flex h-full flex-col">
      <QuestionMeta
        fraudType={item.fraud_type}
        difficulty={item.difficulty}
        index={index}
        total={total}
      />
      <div className="flex-1 overflow-y-auto px-4 pb-4">
        <h2 className="pt-2 text-base font-bold">{item.title}</h2>
        <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed">
          {item.narrative}
        </p>
        <div className="mt-4 flex items-center justify-between gap-3">
          <h3 className="text-sm font-bold">{item.question}</h3>
          <span className="shrink-0 rounded-full bg-primary/10 px-2 py-1 text-xs font-semibold text-primary">
            已選 {selectedTags.length} 個
          </span>
        </div>
        <div className="mt-3 grid gap-2">
          {item.options.map((option) => {
            const checked = selectedTags.includes(option.tag)
            const checkboxId = `tactics-${item.item_id}-${option.tag}`
            return (
              <label
                key={option.tag}
                htmlFor={checkboxId}
                className={`flex cursor-pointer items-center gap-3 rounded-xl border p-3 text-sm transition-colors ${
                  checked ? "border-primary bg-primary/10" : "bg-card"
                } ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
              >
                <Checkbox
                  id={checkboxId}
                  aria-label={option.label}
                  checked={checked}
                  disabled={disabled}
                  onCheckedChange={() => toggleTag(option.tag)}
                />
                <span className="font-medium">{option.label}</span>
              </label>
            )
          })}
        </div>
      </div>
      <div className="border-t border-border bg-background p-3">
        <Button
          type="button"
          disabled={disabled}
          onClick={() => onSubmit(selectedTags)}
          className="h-11 w-full rounded-xl font-bold"
        >
          送出答案
        </Button>
      </div>
    </div>
  )
}
