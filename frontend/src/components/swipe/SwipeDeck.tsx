import { useEffect, useRef, useState } from "react"
import type { ApiError, QuizWeaknessDetail } from "@/client"
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
  // 這張卡送出失敗時選的答案(畫面顯示「再送一次」用)
  const [failedGuess, setFailedGuess] = useState<boolean | null>(null)
  const [expired, setExpired] = useState(false)
  // 這張卡第一次選的答案,送出後就鎖定:連點、失敗重送都只能送這個
  // (伺服器只記第一次,換答案會被拒絕)。用 ref 同步上鎖,因為 isPending 要等下一次
  // render 才更新,連點兩下會在那之前送出兩個不同的答案。
  const lockedGuess = useRef<boolean | null>(null)
  const inFlight = useRef(false)
  const [feedback, setFeedback] = useState<{
    correct: boolean
    explanation: string
    weaknessDetails: QuizWeaknessDetail[]
  } | null>(null)

  const cards = deck.data?.cards ?? []
  const sessionId = deck.data?.session_id
  const done = !deck.isLoading && (idx >= cards.length || alertness <= 0)

  // 每一輪只自動結算一次。用 ref 記住已送出的輪次:開發模式的 StrictMode 會把
  // effect 跑兩次,而且結算失敗後 isPending 變回 false,不擋的話會一直重送、重複發獎。
  // 失敗就停下來讓玩家按「再試一次」。
  const settledRound = useRef<number | null>(null)
  useEffect(() => {
    if (done && sessionId && settledRound.current !== round) {
      settledRound.current = round
      completeM.mutate(sessionId)
    }
  }, [done, round, completeM, sessionId])

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

  const restart = () => {
    setIdx(0)
    setAlertness(MAX_ALERTNESS)
    setStreak(0)
    setFeedback(null)
    setFailedGuess(null)
    setExpired(false)
    lockedGuess.current = null
    completeM.reset()
    // 換新一輪的牌:練習重點在上一輪結算後可能已經更新,新牌組照新比例出
    setRound((r) => r + 1)
  }

  if (completeM.data) {
    return <SwipeRoundSummary result={completeM.data} onRestart={restart} />
  }

  if (done && completeM.isError) {
    // 400/404:這一局已經不能結算(例如沒有任何作答),重試也沒用,改成重新發牌
    const status = (completeM.error as ApiError | null)?.status
    const gone = status === 400 || status === 404
    return (
      <div className="py-12 text-center text-sm">
        <p role="alert" className="text-scam">
          {gone ? "這一局已經失效了。" : "結算沒有成功，請再試一次。"}
        </p>
        <button
          type="button"
          onClick={() =>
            gone ? restart() : sessionId && completeM.mutate(sessionId)
          }
          className="mt-3 rounded-xl bg-primary px-4 py-2 text-sm font-bold text-primary-foreground"
        >
          {gone ? "重新發牌" : "再試一次"}
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

  const onJudge = (picked: boolean) => {
    if (feedback || inFlight.current || !sessionId) return
    // 送出失敗時伺服器可能已經記下答案(只是回應沒回來),重送一定要用原本的答案
    const guessIsScam = lockedGuess.current ?? picked
    lockedGuess.current = guessIsScam
    inFlight.current = true
    answerM.mutate(
      { sessionId, cardId: card.id, guessIsScam },
      {
        onSettled: () => {
          inFlight.current = false
        },
        onError: (err) => {
          // 400/404:這一局已經不能再作答(別的分頁結算了、卡片被移除),重送也沒用
          const status = (err as ApiError | undefined)?.status
          if (status === 400 || status === 404) setExpired(true)
          else setFailedGuess(guessIsScam)
        },
        onSuccess: (res) => {
          setFailedGuess(null)
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
    lockedGuess.current = null
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
      ) : expired ? (
        <div className="rounded-2xl border border-border bg-card p-4 text-center text-sm">
          <p role="alert" className="text-scam">
            這一局已經失效了。
          </p>
          <button
            type="button"
            onClick={restart}
            className="mt-3 rounded-xl bg-primary px-4 py-2 font-bold text-primary-foreground"
          >
            重新發牌
          </button>
        </div>
      ) : failedGuess !== null ? (
        <div className="rounded-2xl border border-border bg-card p-4 text-center text-sm">
          <p role="alert" className="text-scam">
            剛才的答案沒有送出成功。
          </p>
          <button
            type="button"
            disabled={answerM.isPending}
            onClick={() => onJudge(failedGuess)}
            className="mt-3 rounded-xl bg-primary px-4 py-2 font-bold text-primary-foreground disabled:opacity-50"
          >
            再送一次
          </button>
        </div>
      ) : (
        <SwipeCard card={card} onJudge={onJudge} />
      )}
    </div>
  )
}
