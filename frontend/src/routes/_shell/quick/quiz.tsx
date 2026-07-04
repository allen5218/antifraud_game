import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import type { QuizAnswerResponse, QuizCompleteResponse } from "@/client"
import { QuizCard } from "@/components/quiz/QuizCard"
import { QuizReveal } from "@/components/quiz/QuizReveal"
import { QuizSummary } from "@/components/quiz/QuizSummary"
import { useQuizAnswer, useQuizComplete, useQuizDeck } from "@/hooks/useQuiz"

export const Route = createFileRoute("/_shell/quick/quiz")({
  component: QuizPage,
})

function QuizPage() {
  const { data: deck, isPending, refetch } = useQuizDeck()
  const answerM = useQuizAnswer()
  const completeM = useQuizComplete()
  const [index, setIndex] = useState(0)
  const [reveal, setReveal] = useState<QuizAnswerResponse | null>(null)
  const [answers, setAnswers] = useState<
    { case_id: number; guess_is_scam: boolean }[]
  >([])
  const [summary, setSummary] = useState<QuizCompleteResponse | null>(null)

  if (isPending || !deck) {
    return (
      <p className="py-12 text-center text-xs text-muted-foreground">載入中…</p>
    )
  }
  if (deck.cases.length === 0) {
    return (
      <p className="py-12 text-center text-xs text-muted-foreground">
        題庫暫無題目
      </p>
    )
  }
  if (summary) {
    return (
      <QuizSummary
        result={summary}
        onRestart={() => {
          setSummary(null)
          setAnswers([])
          setIndex(0)
          refetch()
        }}
      />
    )
  }

  const current = deck.cases[index]
  const judge = (guessIsScam: boolean) => {
    if (answerM.isPending) return
    const nextAnswers = [
      ...answers,
      { case_id: current.id, guess_is_scam: guessIsScam },
    ]
    answerM.mutate(
      { caseId: current.id, guessIsScam },
      { onSuccess: (data) => setReveal(data) },
    )
    setAnswers(nextAnswers)
  }
  const next = () => {
    setReveal(null)
    if (index + 1 < deck.cases.length) {
      setIndex(index + 1)
    } else {
      completeM.mutate(
        { sessionId: deck.session_id, answers },
        { onSuccess: (data) => setSummary(data) },
      )
    }
  }

  return (
    <div className="h-full">
      <QuizCard
        fraudType={current.fraud_type}
        title={current.title}
        narrative={current.narrative}
        difficulty={current.difficulty}
        index={index}
        total={deck.cases.length}
        onJudge={judge}
        disabled={answerM.isPending || reveal !== null}
      />
      {reveal && (
        <QuizReveal
          result={reveal}
          onNext={next}
          isLast={index + 1 >= deck.cases.length}
        />
      )}
    </div>
  )
}
