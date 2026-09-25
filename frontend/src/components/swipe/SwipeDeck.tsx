import { useEffect, useRef, useState } from "react"
import type { QuizWeaknessDetail } from "@/client"
import { PracticeFocusBadge } from "@/components/practice/PracticeFocus"
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
  const [round, setRound] = useState(0)
  const deck = useSwipeDeck(12, round)
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
    weaknessDetails: QuizWeaknessDetail[]
  } | null>(null)

  const cards = deck.data ?? []
  const done = !deck.isLoading && (idx >= cards.length || alertness <= 0)

  // 每一輪只自動結算一次。用 ref 記住已送出的輪次:開發模式的 StrictMode 會把
  // effect 跑兩次,而且結算失敗後 isPending 變回 false,不擋的話會一直重送、重複發獎。
  // 失敗就停下來讓玩家按「再試一次」。
  const settledRound = useRef<number | null>(null)
  useEffect(() => {
    if (done && settledRound.current !== round) {
      settledRound.current = round
      completeM.mutate(answers)
    }
  }, [done, round, completeM, answers])

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
    const restart = () => {
      setIdx(0)
      setAlertness(MAX_ALERTNESS)
      setStreak(0)
      setAnswers([])
      setFeedback(null)
      completeM.reset()
      // 換新一輪的牌:練習重點在上一輪結算後可能已經更新,新牌組照新比例出
      setRound((r) => r + 1)
    }
    return <SwipeRoundSummary result={completeM.data} onRestart={restart} />
  }

  if (done && completeM.isError) {
    return (
      <div className="py-12 text-center text-sm">
        <p role="alert" className="text-scam">
          結算沒有成功，請再試一次。
        </p>
        <button
          type="button"
          onClick={() => completeM.mutate(answers)}
          className="mt-3 rounded-xl bg-primary px-4 py-2 text-sm font-bold text-primary-foreground"
        >
          再試一次
        </button>
      </div>
    )
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
            weaknessDetails: res.tag_details,
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
      <PracticeFocusBadge />
      <SwipeStatsBar
        alertness={alertness}
        maxAlertness={MAX_ALERTNESS}
        streak={streak}
        progress={idx}
        total={cards.length}
      />
      {feedback ? (
        <>
          {/* 回饋出現時保留剛才那則訊息,解說才對得起來 */}
          <div className="rounded-2xl border border-border bg-card/60 p-4 text-muted-foreground">
            <div className="mb-1 text-[11px]">{card.source_label}</div>
            <p className="text-xs leading-relaxed">{card.scenario}</p>
          </div>
          <SwipeFeedback
            correct={feedback.correct}
            explanation={feedback.explanation}
            weaknessDetails={feedback.weaknessDetails}
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
