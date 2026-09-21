import { useState } from "react"
import type { QuizTacticsPublic } from "@/client"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"

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
      <div className="flex items-center gap-2 px-4 pt-3 text-xs text-muted-foreground">
        <span className="rounded-md bg-primary/10 px-1.5 py-0.5 font-semibold text-primary">
          他在用哪一招？
        </span>
        <span className="ml-auto">
          {index + 1} / {total}
        </span>
      </div>
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
          {item.options.map((option, optIdx) => {
            const labelText =
              typeof option === "string"
                ? option
                : option.label ||
                  (option as any).text ||
                  (option as any).prompt ||
                  option.tag ||
                  `選項 ${optIdx + 1}`
            const tagVal =
              typeof option === "string" ? option : option.tag || labelText
            const checked = selectedTags.includes(tagVal)
            const checkboxId = `tactics-${item.item_id}-${tagVal}`
            return (
              <label
                key={tagVal}
                htmlFor={checkboxId}
                className={`flex cursor-pointer items-center gap-3 rounded-xl border p-3.5 text-sm transition-colors ${
                  checked
                    ? "border-emerald-500/60 bg-emerald-500/10 text-emerald-100 shadow-sm"
                    : "border-white/10 bg-slate-900/60 text-slate-200 hover:bg-slate-800/60"
                } ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
              >
                <Checkbox
                  id={checkboxId}
                  aria-label={labelText}
                  checked={checked}
                  disabled={disabled}
                  onCheckedChange={() => toggleTag(tagVal)}
                />
                <span className="font-medium leading-relaxed">{labelText}</span>
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
          選好了
        </Button>
      </div>
    </div>
  )
}
