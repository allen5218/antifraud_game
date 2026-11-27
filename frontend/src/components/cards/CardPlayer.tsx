import { Link } from "@tanstack/react-router"
import { CircleCheck, CircleX } from "lucide-react"
import { useRef, useState } from "react"
import type { AnswerResponse, RoundResponse, RoundResult } from "@/client"
import { formatYuan } from "@/components/estate/format"
import { ExamInProgress } from "@/components/exam/ExamInProgress"
import { errorCode } from "@/components/exam/exam"
import { useAnswerCard, useCardRound, useCompleteRound } from "@/hooks/useCards"
import { FRAUD_TYPE_LABELS } from "@/lib/fraudTypes"
import { cn } from "@/lib/utils"
import { formatMoney } from "@/utils/money"
import { CardArt } from "./CardArt"
import { type Answered, CardPrompt, CardQuestion } from "./CardQuestion"

/** 加速的時間：「2 小時 40 分鐘」 */
export function formatBoost(minutes: number): string {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  if (h === 0) return `${m} 分鐘`
  return m === 0 ? `${h} 小時` : `${h} 小時 ${m} 分鐘`
}

/**
 * 卡片練習：發一輪、出錯時換成提示。每一輪的作答狀態在 `CardRound`，
 * 用牌局 id 當 key，再一輪就是全新的狀態。
 */
export function CardPlayer({ topic }: { topic: string | null }) {
  const [roundNo, setRoundNo] = useState(0)
  const deal = useCardRound(topic, roundNo)
  const again = () => setRoundNo((n) => n + 1)

  if (errorCode(deal.error) === "exam_in_progress")
    return <ExamInProgress error={deal.error} />
  if (deal.isError)
    return <Retry text="題目載入失敗，請稍後再試。" onRetry={again} />
  if (!deal.data)
    return (
      <div className="py-12 text-center text-muted-foreground">發牌中…</div>
    )
  return (
    <CardRound key={deal.data.round_id} round={deal.data} onAgain={again} />
  )
}

/**
 * 一輪卡片：一次一張，答完看解說再按「下一張」，最後一張看完結算。
 * 每張卡第一次的答案就是最終答案（伺服器只記第一次），連點也只送一次。
 */
function CardRound({
  round,
  onAgain,
}: {
  round: RoundResponse
  onAgain: () => void
}) {
  const answerM = useAnswerCard()
  const completeM = useCompleteRound()
  const [idx, setIdx] = useState(0)
  const [answers, setAnswers] = useState<Record<string, Answered>>({})
  const [feedback, setFeedback] = useState<AnswerResponse | null>(null)
  const [result, setResult] = useState<RoundResult | null>(null)
  const inFlight = useRef(false)

  if (errorCode(answerM.error) === "exam_in_progress")
    return <ExamInProgress error={answerM.error} />

  const cards = round.cards
  const card = cards[idx]
  const answered = card ? (answers[card.card_key] ?? null) : null
  const last = idx >= cards.length - 1

  if (result) return <RoundSummary result={result} onAgain={onAgain} />

  const submit = (ids: string[]) => {
    if (inFlight.current || answered || !card) return
    inFlight.current = true
    answerM.mutate(
      { roundId: round.round_id, cardKey: card.card_key, ids },
      {
        onSuccess: (res) => {
          setAnswers((prev) => ({
            ...prev,
            [card.card_key]: {
              picked: ids,
              correctIds: res.correct_ids,
              correct: res.correct,
            },
          }))
          setFeedback(res)
        },
        onSettled: () => {
          inFlight.current = false
        },
      },
    )
  }

  const next = () => {
    if (!last) {
      setIdx(idx + 1)
      setFeedback(null)
      return
    }
    completeM.mutate(round.round_id, { onSuccess: setResult })
  }

  const done = Object.keys(answers).length
  return (
    <div className="mx-auto flex max-w-md flex-col gap-4 pb-28">
      <div className="flex items-center gap-3">
        <div
          className="h-2 flex-1 overflow-hidden rounded-full bg-surface-2"
          role="progressbar"
          aria-valuenow={done}
          aria-valuemax={cards.length}
          aria-label="這一輪的進度"
        >
          <div
            className="h-full rounded-full bg-primary transition-all"
            style={{ width: `${(done / cards.length) * 100}%` }}
          />
        </div>
        <span className="text-sm tabular-nums text-muted-foreground">
          {idx + 1}／{cards.length}
        </span>
      </div>

      {card && (
        <article
          key={card.card_key}
          data-testid="card"
          className="overflow-hidden rounded-3xl border border-border bg-card shadow-sm"
        >
          <CardArt {...card.art} />
          <div className="space-y-4 p-4">
            <p className="text-sm text-muted-foreground">
              {FRAUD_TYPE_LABELS[card.fraud_type] ?? "防詐常識"}
            </p>
            <CardPrompt card={card} answered={answered} />
            <CardQuestion
              card={card}
              answered={answered}
              busy={answerM.isPending}
              onSubmit={submit}
            />
          </div>
        </article>
      )}

      {answerM.isError && !answered && (
        <p role="alert" className="text-center text-sm text-scam">
          沒有送出去，請再按一次。
        </p>
      )}

      {feedback && (
        <div
          data-testid="card-feedback"
          className={cn(
            "fixed inset-x-0 bottom-0 z-20 border-t-2 p-4 pb-[calc(1rem+env(safe-area-inset-bottom))]",
            feedback.correct
              ? "border-legit bg-legit/15 backdrop-blur"
              : "border-scam bg-scam/15 backdrop-blur",
          )}
        >
          <div className="mx-auto max-w-md space-y-3">
            <p
              className={cn(
                "flex items-center gap-2 text-lg font-bold",
                feedback.correct ? "text-legit" : "text-scam",
              )}
            >
              {feedback.correct ? (
                <CircleCheck aria-hidden className="size-6" />
              ) : (
                <CircleX aria-hidden className="size-6" />
              )}
              {feedback.correct ? "答對了" : "答錯了，過幾天會再考一次"}
            </p>
            <p className="text-base">{feedback.explanation}</p>
            {feedback.weakness && (
              <p className="text-sm text-muted-foreground">
                對方用的招數：{feedback.weakness.label}
              </p>
            )}
            <button
              type="button"
              onClick={next}
              disabled={completeM.isPending}
              className="h-14 w-full rounded-2xl bg-primary text-lg font-bold text-primary-foreground disabled:opacity-50"
            >
              {last ? "看結果" : "下一張"}
            </button>
            {completeM.isError && (
              <p role="alert" className="text-center text-sm text-scam">
                結算失敗，請再按一次。
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function RoundSummary({
  result,
  onAgain,
}: {
  result: RoundResult
  onAgain: () => void
}) {
  const goalMet = result.today_done >= result.daily_goal
  return (
    <div
      data-testid="round-summary"
      className="mx-auto flex max-w-md flex-col items-center gap-4 py-8 text-center"
    >
      <p className="text-5xl font-extrabold tabular-nums">
        {result.correct_count}／{result.total}
      </p>
      <p className="text-lg">這一輪答對的張數</p>
      <p className="text-base text-muted-foreground">
        拿到 ${formatMoney(result.cash_earned)}、經驗值 {result.xp_earned}
      </p>
      {(result.boost_minutes ?? 0) > 0 && (
        <Link
          to="/room"
          data-testid="round-boost"
          className="rounded-2xl bg-legit/15 px-4 py-2 text-base font-semibold text-legit"
        >
          房產多收了 {formatBoost(result.boost_minutes ?? 0)}的租，
          {formatYuan(result.boost_cash ?? 0)} 元
        </Link>
      )}
      <p
        className={cn(
          "rounded-full px-4 py-1 text-base font-semibold",
          goalMet ? "bg-legit/15 text-legit" : "bg-surface-2",
        )}
      >
        {goalMet
          ? "今天的目標完成了"
          : `今天 ${result.today_done}／${result.daily_goal} 張`}
      </p>
      <div className="mt-4 grid w-full gap-3">
        <button
          type="button"
          onClick={onAgain}
          className="h-14 rounded-2xl bg-primary text-lg font-bold text-primary-foreground"
        >
          再一輪
        </button>
        <Link
          to="/"
          className="flex h-14 items-center justify-center rounded-2xl border-2 border-border text-lg font-semibold"
        >
          回首頁
        </Link>
      </div>
    </div>
  )
}

function Retry({ text, onRetry }: { text: string; onRetry: () => void }) {
  return (
    <div className="space-y-3 py-8 text-center">
      <p role="alert">{text}</p>
      <button
        type="button"
        onClick={onRetry}
        className="rounded-xl bg-primary px-4 py-2 text-primary-foreground"
      >
        再試一次
      </button>
    </div>
  )
}
