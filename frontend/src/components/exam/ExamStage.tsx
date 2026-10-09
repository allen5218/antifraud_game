import { useRef, useState } from "react"
import type {
  ExamMessageAnswer,
  ExamPretestAnswer,
  ExamState,
  ExamSwipeAnswer,
} from "@/client"
import { PretestQuestion } from "@/components/Pretest/PretestQuestion"
import { TacticsQuestion } from "@/components/quiz/TacticsQuestion"
import { VerdictQuestion } from "@/components/quiz/VerdictQuestion"
import { SwipeCard } from "@/components/swipe/SwipeCard"
import { Button } from "@/components/ui/button"
import { type DraftAnswer, readDraft, saveDraft } from "./exam"

export function ExamStage({
  state,
  onSubmit,
  busy,
}: {
  state: ExamState
  onSubmit: (answers: DraftAnswer[]) => Promise<void>
  busy: boolean
}) {
  const [answers, setAnswers] = useState(() => readDraft(state))
  const currentAnswers = useRef(answers)
  const index = answers.length
  const item = state.stage_items[index]
  const answer = (value: DraftAnswer) => {
    if (busy || currentAnswers.current.length !== index) return
    const next = [...currentAnswers.current, value]
    currentAnswers.current = next
    saveDraft(state, next)
    setAnswers(next)
  }
  if (!state.stage_items.length)
    return <p role="alert">這一關的題目讀不到，請重新讀取檢測。</p>
  if (!item)
    return (
      <section className="rounded-2xl border bg-card p-5 text-center">
        <p className="mb-4">這一關的 {answers.length} 題都答完了。</p>
        <Button
          disabled={busy}
          onClick={() => onSubmit(currentAnswers.current)}
        >
          {busy ? "正在送出…" : "送出這一關"}
        </Button>
      </section>
    )
  const metadata = { fraud_type: state.fraud_type ?? "", difficulty: 1 }
  return (
    <section className="min-h-0">
      <p className="mb-3 text-sm text-muted-foreground">
        第 {index + 1} 題，共 {state.stage_items.length} 題
      </p>
      {state.stage === "pretest" && "question_text" in item && (
        <PretestQuestion
          key={item.id}
          questionText={item.question_text}
          options={item.options}
          onAnswer={(selected) =>
            answer({
              question_id: item.id,
              selected_option: selected,
            } satisfies ExamPretestAnswer)
          }
        />
      )}
      {state.stage === "swipe" && "scenario" in item && (
        <SwipeCard
          key={item.id}
          card={item}
          onJudge={(guess) =>
            answer({
              card_id: item.id,
              guess_is_scam: guess,
            } satisfies ExamSwipeAnswer)
          }
        />
      )}
      {state.stage === "message" &&
        "item_id" in item &&
        (item.kind === "verdict" ? (
          <VerdictQuestion
            key={item.item_id}
            item={{ ...item, ...metadata }}
            hideMeta
            index={index}
            total={state.stage_items.length}
            disabled={busy}
            onSubmit={(guess) =>
              answer({
                item_id: item.item_id,
                guess_is_scam: guess,
              } satisfies ExamMessageAnswer)
            }
          />
        ) : (
          <TacticsQuestion
            key={item.item_id}
            item={{
              ...item,
              ...metadata,
              question: item.question ?? "這則詐騙訊息用了哪些話術？（可複選）",
              options: item.options ?? [],
            }}
            hideMeta
            index={index}
            total={state.stage_items.length}
            disabled={busy}
            onSubmit={(tags) =>
              answer({
                item_id: item.item_id,
                tags: tags as NonNullable<ExamMessageAnswer["tags"]>,
              })
            }
          />
        ))}
    </section>
  )
}
