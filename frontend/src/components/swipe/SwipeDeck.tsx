import { useEffect, useState } from "react"
import {
  useSwipeAnswer,
  useSwipeComplete,
  useSwipeDeck,
} from "@/hooks/useSwipe"
import { SwipeCard } from "./SwipeCard"
import { SwipeFeedback } from "./SwipeFeedback"
import { SwipeRoundSummary } from "./SwipeRoundSummary"
import { SwipeStatsBar } from "./SwipeStatsBar"

const MAX_ALERTNESS = 3

export function SwipeDeck() {
  const deck = useSwipeDeck(12)
  const answerM = useSwipeAnswer()
  const completeM = useSwipeComplete()

  const [idx, setIdx] = useState(0)
  const [alertness, setAlertness] = useState(MAX_ALERTNESS)
  const [streak, setStreak] = useState(0)
  const [answers, setAnswers] = useState<
    { card_id: string; guess_is_scam: boolean }[]
  >([])
  const [feedback, setFeedback] = useState<{
    correct: boolean
    explanation: string
    weaknessTags: string[]
  } | null>(null)

  const cards = deck.data ?? []
  const done = !deck.isLoading && (idx >= cards.length || alertness <= 0)

  useEffect(() => {
    if (done && !completeM.data && !completeM.isPending) {
      completeM.mutate(answers)
    }
  }, [done, completeM, answers])

  if (deck.isLoading) {
    return (
      <div className="py-12 text-center text-sm text-muted-foreground">
        發牌中…
      </div>
    )
  }

  if (cards.length === 0) {
    return <div className="py-12 text-center text-sm">目前沒有題目</div>
  }

  if (completeM.data) {
    return <SwipeRoundSummary result={completeM.data} />
  }

  if (done && !completeM.data) {
    return (
      <div className="py-12 text-center text-sm text-muted-foreground">
        結算中…
      </div>
    )
  }

  const card = cards[idx]

  const onJudge = (guessIsScam: boolean) => {
    if (feedback || answerM.isPending) return
    answerM.mutate(
      { cardId: card.id, guessIsScam },
      {
        onSuccess: (res) => {
          setAnswers((a) => [
            ...a,
            { card_id: card.id, guess_is_scam: guessIsScam },
          ])
          if (res.correct) {
            setStreak((s) => s + 1)
          } else {
            setStreak(0)
            setAlertness((h) => h - 1)
          }
          setFeedback({
            correct: res.correct,
            explanation: res.explanation,
            weaknessTags: res.weakness_tags,
          })
        },
      },
    )
  }

  const next = () => {
    setFeedback(null)
    setIdx((i) => i + 1)
  }

  return (
    <div className="space-y-3">
      <SwipeStatsBar
        alertness={alertness}
        maxAlertness={MAX_ALERTNESS}
        streak={streak}
        progress={idx}
        total={cards.length}
      />
      {feedback ? (
        <>
          <SwipeFeedback
            correct={feedback.correct}
            explanation={feedback.explanation}
            weaknessTags={feedback.weaknessTags}
          />
          <button
            type="button"
            onClick={next}
            className="w-full rounded-xl bg-primary py-3 font-bold text-primary-foreground"
          >
            下一張
          </button>
        </>
      ) : (
        <SwipeCard card={card} onJudge={onJudge} />
      )}
    </div>
  )
}
