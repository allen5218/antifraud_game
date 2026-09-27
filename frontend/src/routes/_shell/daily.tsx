import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { CalendarCheck, Flame, Trophy } from "lucide-react"
import { useState } from "react"
import type {
  DailyTodayResponse,
  QuickQuizAnswerResponse,
  QuizCompleteResponse,
} from "@/client"
import { QuizCard, type QuizDraftAnswer } from "@/components/quiz/QuizCard"
import { QuizReveal } from "@/components/quiz/QuizReveal"
import { QuizSummary } from "@/components/quiz/QuizSummary"
import { useDailyToday } from "@/hooks/useDaily"
import { extractErrorCode, useEconomyMe } from "@/hooks/useEconomy"
import { useQuizAnswer, useQuizComplete } from "@/hooks/useQuiz"
import { formatDuration } from "@/lib/duration"

export const Route = createFileRoute("/_shell/daily")({
  component: DailyPage,
})

const PRIMARY_LINK =
  "flex w-full items-center justify-center gap-1.5 rounded-xl bg-primary py-2.5 text-sm font-bold text-primary-foreground"

function DailyPage() {
  const { data, error, isPending } = useDailyToday()

  if (error) {
    const code = extractErrorCode(error)
    return (
      <p className="py-12 text-center text-xs text-muted-foreground">
        {code === "level_required"
          ? "每日訓練在 Lv.5 解鎖，先到題組或滑卡多練幾輪。"
          : code === "daily_unavailable"
            ? "今天的題目還沒準備好，請稍後再試"
            : "題目載入失敗，請稍後再試"}
      </p>
    )
  }
  if (isPending || !data) {
    return (
      <p className="py-12 text-center text-xs text-muted-foreground">載入中…</p>
    )
  }
  if (data.status === "completed") {
    return <DailyDone today={data} />
  }
  // key 綁 session_id：換日後拿到新的牌局時，作答進度從頭開始
  return <DailyRun key={data.session_id} today={data} />
}

/** 今天已經完成：成績、名次、明天再來 */
function DailyDone({ today }: { today: DailyTodayResponse }) {
  const { data: economy } = useEconomyMe()
  const result = today.result
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 px-6 py-10 text-center">
      <CalendarCheck aria-hidden className="size-12 text-primary" />
      <h2 className="text-lg font-bold">今天的每日訓練已完成</h2>
      {result && (
        <>
          <p className="text-2xl font-extrabold">
            {result.correct} / {result.total}
          </p>
          <p className="text-sm text-muted-foreground">
            用時 {formatDuration(result.duration_seconds)} · 今日第{" "}
            {result.rank} 名（共 {result.participants} 人）
          </p>
        </>
      )}
      {economy && economy.streak_days > 0 && (
        <p className="inline-flex items-center gap-1 text-xs text-muted-foreground">
          <Flame aria-hidden className="size-3.5 text-warning" />
          已連續練習 {economy.streak_days} 天
        </p>
      )}
      <p className="text-xs text-muted-foreground">明天再來挑戰新的 10 題。</p>
      <Link to="/leaderboard" className={PRIMARY_LINK}>
        <Trophy aria-hidden className="size-4" />
        看排行榜
      </Link>
      <Link to="/" className="text-xs text-muted-foreground underline">
        回首頁
      </Link>
    </div>
  )
}

/** 作答中：從第一個還沒作答的題目接著做 */
function DailyRun({ today }: { today: DailyTodayResponse }) {
  const qc = useQueryClient()
  const answerM = useQuizAnswer()
  const completeM = useQuizComplete()
  const answered = new Set(today.answered_item_ids)
  const firstOpen = today.items.findIndex((item) => !answered.has(item.item_id))
  const [index, setIndex] = useState(
    firstOpen === -1 ? today.items.length : firstOpen,
  )
  const [reveal, setReveal] = useState<QuickQuizAnswerResponse | null>(null)
  const [summary, setSummary] = useState<QuizCompleteResponse | null>(null)

  const complete = () => {
    if (completeM.isPending) return
    completeM.mutate(today.session_id, {
      onSuccess: (data) => {
        setSummary(data)
        qc.invalidateQueries({ queryKey: ["leaderboard"] })
      },
    })
  }

  if (summary) {
    return (
      <QuizSummary result={summary}>
        <p className="text-xs text-muted-foreground">已含每日完成獎勵。</p>
        <Link
          to="/leaderboard"
          className={PRIMARY_LINK}
          onClick={() => qc.invalidateQueries({ queryKey: ["daily"] })}
        >
          <Trophy aria-hidden className="size-4" />
          看今天的排名
        </Link>
      </QuizSummary>
    )
  }

  // 題目都答完了但還沒結算（例如結算時斷線、重新整理）：直接讓玩家結算
  if (index >= today.items.length) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 px-6 py-10 text-center">
        <p className="text-sm">今天的 {today.items.length} 題都答完了</p>
        <button
          type="button"
          onClick={complete}
          disabled={completeM.isPending}
          className={PRIMARY_LINK}
        >
          看結算
        </button>
        {completeM.isError && (
          <p className="text-xs text-destructive">結算失敗，請再按一次</p>
        )}
      </div>
    )
  }

  const current = today.items[index]
  const submitAnswer = (answer: QuizDraftAnswer) => {
    if (answerM.isPending || reveal !== null) return
    answerM.mutate(
      { session_id: today.session_id, item_id: current.item_id, ...answer },
      { onSuccess: (data) => setReveal(data) },
    )
  }
  const next = () => {
    if (index + 1 < today.items.length) {
      setReveal(null)
      setIndex((currentIndex) => currentIndex + 1)
    } else {
      complete()
    }
  }

  return (
    <div className="flex h-full flex-col">
      {index === 0 && (
        <p className="mx-4 mt-1 inline-flex items-center gap-1 text-[11px] text-muted-foreground">
          <CalendarCheck aria-hidden className="size-3.5 text-primary" />
          每日訓練 · 一天一次，成績會上排行榜
        </p>
      )}
      <div className="min-h-0 flex-1">
        <QuizCard
          key={current.item_id}
          item={current}
          index={index}
          total={today.items.length}
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
          isLast={index + 1 >= today.items.length}
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
