import { useState } from "react"
import type { CardPublic, Choice } from "@/client"
import { cn } from "@/lib/utils"
import {
  EMPTY_MATCH,
  type MatchState,
  matchAnswer,
  SINGLE_ANSWER_KINDS,
  splitBlank,
  tapLeft,
  tapRight,
  toggleStep,
} from "./cardPlay"

export interface Answered {
  picked: string[]
  correctIds: string[]
  correct: boolean
}

interface Props {
  card: CardPublic
  answered: Answered | null
  busy: boolean
  onSubmit: (ids: string[]) => void
}

/** 一張卡的作答區：依題型畫選項。答完後標出正解（綠）與選錯的（紅），不能再改。 */
export function CardQuestion({ card, answered, busy, onSubmit }: Props) {
  const locked = answered !== null || busy
  if (card.kind === "order")
    return (
      <OrderQuestion
        card={card}
        answered={answered}
        locked={locked}
        onSubmit={onSubmit}
      />
    )
  if (card.kind === "match")
    return (
      <MatchQuestion
        card={card}
        answered={answered}
        locked={locked}
        onSubmit={onSubmit}
      />
    )
  if (SINGLE_ANSWER_KINDS.has(card.kind))
    return (
      <SingleQuestion
        card={card}
        answered={answered}
        locked={locked}
        onSubmit={onSubmit}
      />
    )
  return null
}

function tone(id: string, answered: Answered | null): string {
  if (!answered) return "border-border bg-card hover:bg-surface-2"
  if (answered.correctIds.includes(id)) return "border-legit bg-legit/15"
  if (answered.picked.includes(id)) return "border-scam bg-scam/15"
  return "border-border bg-card opacity-60"
}

interface PartProps {
  card: CardPublic
  answered: Answered | null
  locked: boolean
  onSubmit: (ids: string[]) => void
}

function SingleQuestion({ card, answered, locked, onSubmit }: PartProps) {
  const choices = card.choices ?? []
  const spot = card.kind === "spot"
  const judge = card.kind === "judge"
  return (
    <div
      className={cn("grid gap-3", judge && "grid-cols-2")}
      data-testid="card-choices"
    >
      {choices.map((c) => (
        <button
          key={c.id}
          type="button"
          disabled={locked}
          onClick={() => onSubmit([c.id])}
          className={cn(
            "min-h-14 rounded-2xl border-2 px-4 py-3 text-left text-lg font-semibold transition-colors disabled:cursor-default",
            judge && "text-center",
            spot && "rounded-bl-sm font-normal",
            tone(c.id, answered),
          )}
        >
          {c.text}
        </button>
      ))}
    </div>
  )
}

function OrderQuestion({ card, answered, locked, onSubmit }: PartProps) {
  const steps = card.choices ?? []
  const [picked, setPicked] = useState<string[]>([])
  const byId = new Map(steps.map((s) => [s.id, s]))
  const shown = answered
    ? answered.correctIds.map((id) => byId.get(id)).filter(Boolean)
    : picked.map((id) => byId.get(id)).filter(Boolean)
  return (
    <div className="space-y-4">
      <ol className="min-h-28 space-y-2 rounded-2xl border-2 border-dashed border-border p-3">
        {(shown as Choice[]).map((s, i) => (
          <li key={s.id}>
            <button
              type="button"
              disabled={locked}
              onClick={() => setPicked(toggleStep(picked, s.id))}
              className={cn(
                "flex w-full items-center gap-3 rounded-xl border-2 px-3 py-2 text-left text-lg",
                answered
                  ? "border-legit bg-legit/15"
                  : "border-primary bg-card",
              )}
            >
              <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground">
                {i + 1}
              </span>
              {s.text}
            </button>
          </li>
        ))}
      </ol>
      {!answered && (
        <div className="flex flex-wrap gap-2">
          {steps
            .filter((s) => !picked.includes(s.id))
            .map((s) => (
              <button
                key={s.id}
                type="button"
                disabled={locked}
                onClick={() => setPicked(toggleStep(picked, s.id))}
                className="rounded-xl border-2 border-border bg-card px-3 py-2 text-lg hover:bg-surface-2"
              >
                {s.text}
              </button>
            ))}
        </div>
      )}
      {!answered && (
        <SubmitButton
          disabled={locked || picked.length !== steps.length}
          onClick={() => onSubmit(picked)}
        />
      )}
      {answered && !answered.correct && (
        <p className="text-sm text-muted-foreground">上面是正確的順序。</p>
      )}
    </div>
  )
}

function MatchQuestion({ card, answered, locked, onSubmit }: PartProps) {
  const left = card.left ?? []
  const right = card.right ?? []
  const [state, setState] = useState<MatchState>(EMPTY_MATCH)
  const answer = matchAnswer(left, state.pairs)
  // 答完顯示正解：第 n 個左邊配的是正解的第 n 個右邊
  const solved = answered
    ? Object.fromEntries(left.map((l, i) => [l.id, answered.correctIds[i]]))
    : state.pairs
  const rightText = new Map(right.map((r) => [r.id, r.text]))
  const pairedRights = new Set(Object.values(state.pairs))
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          {left.map((l) => (
            <button
              key={l.id}
              type="button"
              disabled={locked}
              onClick={() => setState(tapLeft(state, l.id))}
              className={cn(
                "flex min-h-14 w-full flex-col items-start rounded-xl border-2 px-3 py-2 text-left",
                state.pending === l.id
                  ? "border-primary bg-primary/10"
                  : solved[l.id]
                    ? answered
                      ? "border-legit bg-legit/15"
                      : "border-primary/60 bg-card"
                    : "border-border bg-card",
              )}
            >
              <span className="text-base font-semibold">{l.text}</span>
              {solved[l.id] && (
                <span className="text-sm text-muted-foreground">
                  {rightText.get(solved[l.id])}
                </span>
              )}
            </button>
          ))}
        </div>
        <div className="space-y-2">
          {right.map((r) => (
            <button
              key={r.id}
              type="button"
              disabled={locked}
              onClick={() => setState(tapRight(state, r.id))}
              className={cn(
                "min-h-14 w-full rounded-xl border-2 px-3 py-2 text-left text-base",
                !answered && pairedRights.has(r.id)
                  ? "border-border bg-surface-2 text-muted-foreground"
                  : "border-border bg-card",
              )}
            >
              {r.text}
            </button>
          ))}
        </div>
      </div>
      {!answered && (
        <SubmitButton
          disabled={locked || answer === null}
          onClick={() => answer && onSubmit(answer)}
        />
      )}
    </div>
  )
}

function SubmitButton({
  disabled,
  onClick,
}: {
  disabled: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="h-14 w-full rounded-2xl bg-primary text-lg font-bold text-primary-foreground disabled:opacity-40"
    >
      送出
    </button>
  )
}

/** 填空題的題目：空格先空著，答完填上正解 */
export function CardPrompt({
  card,
  answered,
}: {
  card: CardPublic
  answered: Answered | null
}) {
  const parts = card.kind === "fill" ? splitBlank(card.prompt) : null
  if (!parts)
    return <p className="text-xl font-bold leading-relaxed">{card.prompt}</p>
  const filled = answered
    ? card.choices?.find((c) => answered.correctIds.includes(c.id))?.text
    : null
  return (
    <p className="text-xl font-bold leading-relaxed">
      {parts[0]}
      <span
        className={cn(
          "mx-1 inline-block min-w-16 border-b-2 px-1 text-center",
          filled ? "border-legit text-legit" : "border-primary",
        )}
      >
        {filled ?? "　"}
      </span>
      {parts[1]}
    </p>
  )
}
