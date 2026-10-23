import { Check } from "lucide-react"
import { type FormEvent, useState } from "react"
import type { SurveyQuestionPublic } from "@/client"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import {
  choseOther,
  firstMissing,
  type SurveyAnswers,
  sections,
  toggle,
} from "./survey"

const CHOICE =
  "relative flex min-h-11 w-full items-center gap-2 rounded-xl border px-3 py-2 text-left text-sm"
const PICKED = "border-primary bg-primary/10 font-bold"

export function TrialSurveyForm({
  questions,
  submitting,
  error,
  onSubmit,
}: {
  questions: SurveyQuestionPublic[]
  submitting: boolean
  // 後端退回時指出哪一題、為什麼
  error: { questionId?: string; message: string } | null
  onSubmit: (answers: SurveyAnswers) => void
}) {
  const [answers, setAnswers] = useState<SurveyAnswers>({})
  const [showMissing, setShowMissing] = useState(false)
  const missing = firstMissing(questions, answers)
  const set = (id: string, value: unknown) =>
    setAnswers((prev) => ({ ...prev, [id]: value }))

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (missing) {
      setShowMissing(true)
      document
        .getElementById(`q-${missing}`)
        ?.scrollIntoView({ behavior: "smooth", block: "center" })
      return
    }
    onSubmit(answers)
  }

  let number = 0
  return (
    <form onSubmit={submit} className="flex flex-col gap-6" noValidate>
      {sections(questions).map((group) => (
        <section key={group.title} className="flex flex-col gap-3">
          <h3 className="text-sm font-bold text-muted-foreground">
            {group.title}
          </h3>
          {group.questions.map((q) => {
            if (q.kind !== "consent") number += 1
            const flagged =
              (showMissing && missing === q.id) || error?.questionId === q.id
            return (
              <fieldset
                key={q.id}
                id={`q-${q.id}`}
                aria-invalid={flagged || undefined}
                className={cn(
                  "flex flex-col gap-2 rounded-2xl border bg-card p-3",
                  flagged && "border-scam",
                )}
              >
                {q.kind !== "consent" && (
                  <legend className="sr-only">{q.text}</legend>
                )}
                {q.kind !== "consent" && (
                  <p aria-hidden className="text-sm font-bold">
                    {number}. {q.text}
                  </p>
                )}
                <QuestionInput
                  q={q}
                  value={answers[q.id]}
                  other={answers[`${q.id}_other`]}
                  onChange={(value) => set(q.id, value)}
                  onOther={(text) => set(`${q.id}_other`, text)}
                />
                {flagged && (
                  <p role="alert" className="text-xs text-scam">
                    {error?.questionId === q.id
                      ? error.message
                      : "這一題還沒完成"}
                  </p>
                )}
              </fieldset>
            )
          })}
        </section>
      ))}
      {error && !error.questionId && (
        <p role="alert" className="text-sm text-scam">
          {error.message}
        </p>
      )}
      <Button type="submit" size="lg" disabled={submitting}>
        {submitting ? "送出中…" : "送出問卷"}
      </Button>
    </form>
  )
}

function QuestionInput({
  q,
  value,
  other,
  onChange,
  onOther,
}: {
  q: SurveyQuestionPublic
  value: unknown
  other: unknown
  onChange: (value: unknown) => void
  onOther: (text: string) => void
}) {
  if (q.kind === "consent") {
    return (
      <label className="flex items-start gap-3 text-sm">
        <input
          type="checkbox"
          className="mt-0.5 size-5 shrink-0 accent-primary"
          checked={value === true}
          onChange={(e) => onChange(e.target.checked)}
        />
        <span>{q.text}</span>
      </label>
    )
  }
  if (q.kind === "scale") {
    return (
      <div className="grid grid-cols-5 gap-1">
        {q.labels.map((label, i) => {
          const point = i + 1
          const picked = value === point
          return (
            <label
              key={label}
              className={cn(
                "relative flex min-h-16 cursor-pointer flex-col items-center justify-center gap-1 rounded-xl border px-0.5 py-2 has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-ring",
                picked && PICKED,
              )}
            >
              <input
                type="radio"
                name={q.id}
                className="sr-only"
                checked={picked}
                onChange={() => onChange(point)}
              />
              <span className="text-base font-bold">{point}</span>
              <span className="text-[11px] leading-tight">
                {/* 「非常不同意」在手機上會斷成「非常不同／意」，固定在「非常」後面換行 */}
                {label.length > 3 ? (
                  <>
                    {label.slice(0, 2)}
                    <br />
                    {label.slice(2)}
                  </>
                ) : (
                  label
                )}
              </span>
            </label>
          )
        })}
      </div>
    )
  }
  if (q.kind === "text") {
    return (
      <textarea
        aria-label={q.text}
        maxLength={500}
        rows={3}
        value={typeof value === "string" ? value : ""}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl border bg-background px-3 py-2 text-sm"
      />
    )
  }
  const multi = q.kind === "multi"
  return (
    <div className="flex flex-col gap-1.5">
      {q.options.map((option) => {
        const picked = multi
          ? Array.isArray(value) && value.includes(option)
          : value === option
        return (
          <label
            key={option}
            className={cn(
              CHOICE,
              "cursor-pointer has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-ring",
              picked && PICKED,
            )}
          >
            <input
              type={multi ? "checkbox" : "radio"}
              name={q.id}
              className="sr-only"
              checked={picked}
              onChange={() => onChange(multi ? toggle(value, option) : option)}
            />
            <span
              aria-hidden
              className={cn(
                "grid size-5 shrink-0 place-content-center border",
                multi ? "rounded" : "rounded-full",
                picked && "border-primary bg-primary text-primary-foreground",
              )}
            >
              {picked && <Check className="size-3.5" />}
            </span>
            {option}
          </label>
        )
      })}
      {q.other && choseOther(value) && (
        <input
          aria-label="其他：請寫一下"
          placeholder="請寫一下"
          maxLength={500}
          value={typeof other === "string" ? other : ""}
          onChange={(e) => onOther(e.target.value)}
          className="min-h-11 rounded-xl border bg-background px-3 text-sm"
        />
      )}
    </div>
  )
}
