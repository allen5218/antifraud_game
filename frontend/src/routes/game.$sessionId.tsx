import {
  createFileRoute,
  Outlet,
  redirect,
  useMatch,
  useNavigate,
} from "@tanstack/react-router"
import { useCallback, useEffect, useState } from "react"
import type { AnswerResponse, GameResponse } from "@/client"
import { GameService } from "@/client"
import { AnswerFeedback } from "@/components/Game/AnswerFeedback"
import { ExperienceBar } from "@/components/Game/ExperienceBar"
import { MascotPopup } from "@/components/Game/MascotPopup"
import { NarrativeCard } from "@/components/Game/NarrativeCard"
import { OptionButton } from "@/components/Game/OptionButton"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/game/$sessionId")({
  component: GamePage,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({ to: "/login" })
    }
  },
  head: () => ({
    meta: [{ title: "遊戲進行中 - 反詐騙訓練" }],
  }),
})

type Phase = "question" | "feedback" | "mascot" | "loading"

function GamePage() {
  const { sessionId } = Route.useParams()
  const navigate = useNavigate()
  const childMatch = useMatch({
    from: "/game/$sessionId/result",
    shouldThrow: false,
  })

  const [phase, setPhase] = useState<Phase>("loading")
  const [question, setQuestion] = useState<GameResponse | null>(null)
  const [answerResult, setAnswerResult] = useState<AnswerResponse | null>(null)
  const [selectedOption, setSelectedOption] = useState<string | null>(null)
  const [score, setScore] = useState(0)
  const [level, setLevel] = useState(1)
  const [currentStep, setCurrentStep] = useState(0)
  const [maxSteps, setMaxSteps] = useState(10)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // 載入遊戲狀態（初始或斷線重連）
  useEffect(() => {
    GameService.getGameSession({ sessionId })
      .then((data: any) => {
        setScore(data.total_score ?? 0)
        setCurrentStep(data.current_step ?? 0)
        setMaxSteps(data.max_steps ?? 10)
        setLevel(data.level ?? 1)
        if (data.last_question) {
          setQuestion(data.last_question)
          setPhase("question")
        } else {
          setPhase("loading")
        }
      })
      .catch(() => {
        setError("無法載入遊戲狀態")
      })
  }, [sessionId])

  const handleSelectOption = async (optionKey: string) => {
    if (selectedOption) return
    setSelectedOption(optionKey)
    setSubmitting(true)

    try {
      const response = await GameService.submitAnswer({
        sessionId,
        requestBody: { selected_option: optionKey },
      })
      const data = response as AnswerResponse
      setAnswerResult(data)
      setScore(data.answer_result.total_score)
      setCurrentStep((prev) => prev + 1)
      setPhase("feedback")
    } catch {
      setError("送出答案失敗，請重新整理頁面。")
    } finally {
      setSubmitting(false)
    }
  }

  const handleContinue = useCallback(() => {
    if (!answerResult) return

    // 檢查吉祥物彈窗
    if (answerResult.mascot_popup?.show) {
      setPhase("mascot")
      return
    }

    // 檢查遊戲結束
    if (answerResult.game_over) {
      sessionStorage.setItem(
        "gameResult",
        JSON.stringify({
          ...answerResult.game_over,
          session_id: sessionId,
        }),
      )
      navigate({ to: `/game/${sessionId}/result` as string })
      return
    }

    // 下一題
    if (answerResult.next_question) {
      setQuestion(answerResult.next_question)
      setSelectedOption(null)
      setAnswerResult(null)
      setPhase("question")
    }
  }, [answerResult, sessionId, navigate])

  const handleMascotDismiss = useCallback(() => {
    if (!answerResult) return

    if (answerResult.game_over) {
      sessionStorage.setItem(
        "gameResult",
        JSON.stringify({
          ...answerResult.game_over,
          session_id: sessionId,
        }),
      )
      navigate({ to: `/game/${sessionId}/result` as string })
      return
    }

    if (answerResult.next_question) {
      setQuestion(answerResult.next_question)
      setSelectedOption(null)
      setAnswerResult(null)
      setPhase("question")
    }
  }, [answerResult, sessionId, navigate])

  // 子路由匹配時，直接渲染子路由內容（必須在所有 hooks 之後）
  if (childMatch) {
    return <Outlet />
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="rounded-xl border border-destructive/50 bg-destructive/10 p-6 text-center">
          <p className="text-destructive">{error}</p>
        </div>
      </div>
    )
  }

  if (phase === "loading" && !question) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-muted-foreground">載入遊戲中...</p>
        </div>
      </div>
    )
  }

  const getOptionState = (key: string) => {
    if (phase !== "feedback" || !answerResult) {
      if (selectedOption === key) return "selected"
      return "default"
    }
    if (key === answerResult.answer_result.correct_option) return "correct"
    if (key === selectedOption && !answerResult.answer_result.is_correct)
      return "wrong"
    return "dimmed"
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-2xl flex-col px-4 py-6">
      <div className="mb-6">
        <ExperienceBar
          score={score}
          level={level}
          currentStep={currentStep}
          maxSteps={maxSteps}
        />
      </div>

      <div className="flex flex-1 flex-col gap-4">
        {question && (
          <>
            <NarrativeCard
              narrative={question.narrative}
              question={question.question}
            />

            <div className="flex flex-col gap-3">
              {question.options.map((opt) => (
                <OptionButton
                  key={opt.key}
                  optionKey={opt.key}
                  text={opt.text}
                  state={getOptionState(opt.key)}
                  disabled={selectedOption !== null}
                  onClick={() => handleSelectOption(opt.key)}
                />
              ))}
            </div>

            {submitting && (
              <div className="flex items-center justify-center gap-3 rounded-xl border bg-muted/50 p-5">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                <span className="text-sm text-muted-foreground">
                  AI 正在分析你的答案...
                </span>
              </div>
            )}

            {phase === "feedback" && answerResult && (
              <AnswerFeedback
                isCorrect={answerResult.answer_result.is_correct}
                explanation={answerResult.answer_result.explanation}
                scoreEarned={answerResult.answer_result.score_earned}
                onContinue={handleContinue}
              />
            )}
          </>
        )}
      </div>

      {answerResult?.mascot_popup && (
        <MascotPopup
          show={phase === "mascot"}
          message={answerResult.mascot_popup.message}
          onDismiss={handleMascotDismiss}
        />
      )}
    </div>
  )
}
