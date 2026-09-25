import { CornerDownRight } from "lucide-react"
import { useState } from "react"
import type { QuizMatchPublic } from "@/client"
import { Button } from "@/components/ui/button"

interface MatchQuestionProps {
  item: QuizMatchPublic
  index: number
  total: number
  disabled: boolean
  onSubmit: (pairs: Record<string, string>) => void
}

/** 點選配對題：先選例句，再選話術；配對維持一對一。 */
export function MatchQuestion({
  item,
  index,
  total,
  disabled,
  onSubmit,
}: MatchQuestionProps) {
  const [selectedPairId, setSelectedPairId] = useState<string | null>(null)
  const [pairs, setPairs] = useState<Record<string, string>>({})
  const pairedCount = Object.keys(pairs).length
  const isComplete = pairedCount === item.match_prompts.length

  const assignTarget = (tag: string) => {
    if (disabled || selectedPairId === null) return
    setPairs((current) => {
      const next = Object.fromEntries(
        Object.entries(current).filter(([, pairedTag]) => pairedTag !== tag),
      )
      next[selectedPairId] = tag
      return next
    })
    setSelectedPairId(null)
  }

  const cancelPair = (pairId: string) => {
    if (disabled) return
    setPairs((current) => {
      const next = { ...current }
      delete next[pairId]
      return next
    })
    setSelectedPairId(pairId)
  }

  const targetLabel = (tag: string) =>
    item.match_targets.find((target) => target.tag === tag)?.label ?? "其他話術"

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 px-4 pt-3 text-xs text-muted-foreground">
        <span className="rounded-md bg-primary/10 px-1.5 py-0.5 font-semibold text-primary">
          配對題
        </span>
        <span className="ml-auto">
          {index + 1} / {total}
        </span>
      </div>
      <div className="flex-1 overflow-y-auto px-4 pb-4">
        <div className="mt-3 flex items-center justify-between gap-3">
          <h2 className="text-base font-bold">{item.question}</h2>
          <span className="shrink-0 rounded-full bg-primary/10 px-2 py-1 text-xs font-semibold text-primary">
            已配對 {pairedCount} / {item.match_prompts.length}
          </span>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          先點一則例句，再點它使用的話術
        </p>

        <div className="mt-4 grid gap-2">
          {item.match_prompts.map((prompt, promptIndex) => {
            const pairedTag = pairs[prompt.pair_id]
            const selected = selectedPairId === prompt.pair_id
            return (
              <div
                key={prompt.pair_id}
                className={`rounded-xl border p-3 ${
                  selected ? "border-primary bg-primary/10" : "bg-card"
                }`}
              >
                <button
                  type="button"
                  disabled={disabled}
                  aria-pressed={selected}
                  onClick={() => setSelectedPairId(prompt.pair_id)}
                  className="w-full text-left text-sm leading-relaxed disabled:opacity-60"
                >
                  <span className="mr-2 font-bold text-primary">
                    {promptIndex + 1}.
                  </span>
                  {prompt.text}
                </button>
                {pairedTag && (
                  <div className="mt-2 flex items-center justify-between gap-2 border-t pt-2">
                    <span className="flex items-center gap-1 text-xs font-semibold text-primary">
                      <CornerDownRight aria-hidden className="size-3.5" />
                      {targetLabel(pairedTag)}
                    </span>
                    <button
                      type="button"
                      disabled={disabled}
                      aria-label={`取消「${prompt.text}」的配對`}
                      onClick={() => cancelPair(prompt.pair_id)}
                      className="text-xs text-muted-foreground underline underline-offset-2 disabled:opacity-60"
                    >
                      取消
                    </button>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        <p className="mt-5 text-xs font-bold text-muted-foreground">
          {selectedPairId ? "選擇對應話術" : "請先選擇例句"}
        </p>
        <div className="mt-2 grid grid-cols-2 gap-2">
          {item.match_targets.map((target) => {
            const used = Object.values(pairs).includes(target.tag)
            return (
              <button
                key={target.tag}
                type="button"
                disabled={disabled || selectedPairId === null}
                aria-label={target.label}
                onClick={() => assignTarget(target.tag)}
                className={`rounded-xl border px-3 py-2.5 text-sm font-semibold transition-colors disabled:opacity-50 ${
                  used ? "border-primary bg-primary/10 text-primary" : "bg-card"
                }`}
              >
                {target.label}
                {used && <span className="ml-1 text-[10px]">已配對</span>}
              </button>
            )
          })}
        </div>
      </div>
      <div className="border-t border-border bg-background p-3">
        <Button
          type="button"
          disabled={disabled || !isComplete}
          onClick={() => onSubmit(pairs)}
          className="h-11 w-full rounded-xl font-bold"
        >
          送出答案
        </Button>
      </div>
    </div>
  )
}
