import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import type { QuickQuizAnswerResponse, QuizCompleteResponse } from "@/client"
import { PracticeFocusBadge } from "@/components/practice/PracticeFocus"
import { QuizCard, type QuizDraftAnswer } from "@/components/quiz/QuizCard"
import { QuizReveal } from "@/components/quiz/QuizReveal"
import { QuizSummary } from "@/components/quiz/QuizSummary"
import { useQuizAnswer, useQuizComplete, useQuizDeck } from "@/hooks/useQuiz"

export const Route = createFileRoute("/_shell/quick/quiz")({
  component: QuizPage,
})

function QuizPage() {
  const [round, setRound] = useState(0)
  const { data: deck, isError: isDeckError, isPending } = useQuizDeck(round)
  const answerM = useQuizAnswer()
  const completeM = useQuizComplete()
  const [index, setIndex] = useState(0)
  const [reveal, setReveal] = useState<QuickQuizAnswerResponse | null>(null)
  const [summary, setSummary] = useState<QuizCompleteResponse | null>(null)

  if (isDeckError) {
    return (
      <p className="py-12 text-center text-xs text-destructive">
        題目載入失敗，請稍後再試
      </p>
    )
  }
  if (isPending || !deck) {
    return (
      <p className="py-12 text-center text-xs text-muted-foreground">載入中…</p>
    )
  }
  if (deck.items.length === 0) {
    return (
      <p className="py-12 text-center text-xs text-muted-foreground">
        目前沒有題目
      </p>
    )
  }
  if (summary) {
    return (
      <QuizSummary
        result={summary}
        onRestart={() => {
          setSummary(null)
          setReveal(null)
          setIndex(0)
          answerM.reset()
          completeM.reset()
          // 遞增 round → 取全新牌與 session_id,不重用已結算的舊 deck
          setRound((r) => r + 1)
        }}
      />
    )
  }

  const current = deck.items[index]
  const submitAnswer = (answer: QuizDraftAnswer) => {
    if (answerM.isPending || reveal !== null) return
    answerM.mutate(
      {
        session_id: deck.session_id,
        item_id: current.item_id,
        ...answer,
      },
      { onSuccess: (data) => setReveal(data) },
    )
  }
  const next = () => {
    if (completeM.isPending) return
    if (index + 1 < deck.items.length) {
      setReveal(null)
      setIndex((currentIndex) => currentIndex + 1)
    } else {
      completeM.mutate(deck.session_id, {
        onSuccess: (data) => setSummary(data),
      })
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* 整輪的偏重只在第一題提示一次,之後把空間留給題目 */}
      {index === 0 && <PracticeFocusBadge className="mx-4 mt-1" />}
      <div className="min-h-0 flex-1">
        <QuizCard
          key={current.item_id}
          item={current}
          index={index}
          total={deck.items.length}
          onSubmit={submitAnswer}
          disabled={answerM.isPending || reveal !== null}
        />
      </div>
      {answerM.isError && reveal === null && (
        <p className="fixed inset-x-4 bottom-20 z-40 rounded-xl bg-destructive px-3 py-2 text-center text-xs font-semibold text-primary-foreground shadow-lg">
          答案送出失敗，請再試一次
        </p>
      )}
      {reveal && (
        <QuizReveal
          item={current}
          result={reveal}
          onNext={next}
          isLast={index + 1 >= deck.items.length}
          disabled={completeM.isPending}
        />
      )}
      {completeM.isError && (
        <p className="fixed inset-x-4 bottom-4 z-[60] rounded-xl bg-destructive px-3 py-2 text-center text-xs font-semibold text-primary-foreground shadow-lg">
          結算失敗，請再按一次「看結算」
        </p>
      )}
    </div>
  )
}
