import { useQuery, useQueryClient } from "@tanstack/react-query"
import {
  createFileRoute,
  Outlet,
  redirect,
  useMatch,
  useNavigate,
} from "@tanstack/react-router"
import { useState } from "react"
import { PretestService } from "@/client"
import { PretestProgress } from "@/components/Pretest/PretestProgress"
import { PretestQuestion } from "@/components/Pretest/PretestQuestion"
import { isLoggedIn } from "@/hooks/useAuth"
import { refreshPracticeProfileSoon } from "@/hooks/usePractice"

export const Route = createFileRoute("/pretest")({
  component: PretestPage,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({ to: "/login" })
    }
  },
  head: () => ({
    meta: [{ title: "前測 - ScamGym 識詐練習場" }],
  }),
})

interface QuestionData {
  id: string
  question_text: string
  options: { key: string; text: string }[]
  fraud_type: string
}

interface Answer {
  question_id: string
  selected_option: string
}

function PretestPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const childMatch = useMatch({ from: "/pretest/result", shouldThrow: false })
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState<Answer[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  // 題目每次都重新抽、順序也打亂。原本在 useState 的初始化函式裡直接呼叫 API:
  // 開發模式的 StrictMode 會跑兩次初始化,發出兩個請求、拿到兩種題序,
  // 畫面用的是後回來的那一份。改用 useQuery,同一時間只會有一個請求。
  // gcTime 0:離開再回來(重新做前測)要抽新的一組,不沿用快取。
  const questionsQuery = useQuery({
    queryKey: ["pretest", "questions"],
    queryFn: () => PretestService.getPretestQuestions(),
    staleTime: Number.POSITIVE_INFINITY,
    gcTime: 0,
    refetchOnWindowFocus: false,
  })
  const questions: QuestionData[] =
    (questionsQuery.data as { questions?: QuestionData[] } | undefined)
      ?.questions ?? []
  const loading = questionsQuery.isPending
  const error = questionsQuery.isError
    ? "無法載入題目，請稍後再試。"
    : submitError

  const handleAnswer = async (selectedKey: string) => {
    const question = questions[currentIndex]
    const newAnswers = [
      ...answers,
      { question_id: question.id, selected_option: selectedKey },
    ]
    setAnswers(newAnswers)

    if (currentIndex + 1 < questions.length) {
      setCurrentIndex(currentIndex + 1)
    } else {
      await submit(newAnswers)
    }
  }

  const submit = async (all: Answer[]) => {
    setSubmitting(true)
    setSubmitError(null)
    try {
      const result = await PretestService.submitPretest({
        requestBody: { answers: all },
      })
      sessionStorage.setItem("pretestResult", JSON.stringify(result))
      refreshPracticeProfileSoon(queryClient)
      // 結果頁是這一頁的子路由,這一頁不會卸載。交卷後把作答清掉並取代這筆瀏覽紀錄,
      // 否則按上一頁會回到最後一題,再選一次就把整份前測又交一次。
      setAnswers([])
      setCurrentIndex(0)
      setSubmitting(false)
      navigate({ to: "/pretest/result", replace: true })
      queryClient.resetQueries({ queryKey: ["pretest", "questions"] })
    } catch {
      // 答案留著,讓玩家直接重送,不必把 20 題重做一次
      setSubmitError("送出失敗，請再送一次。")
      setSubmitting(false)
    }
  }

  // 子路由匹配時，直接渲染子路由內容（必須在所有 hooks 之後）
  if (childMatch) {
    return <Outlet />
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-muted-foreground">載入題目中…</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="rounded-xl border border-destructive/50 bg-destructive/10 p-6 text-center">
          <p role="alert" className="text-destructive">
            {error}
          </p>
          {submitError && answers.length > 0 && (
            <button
              type="button"
              onClick={() => submit(answers)}
              className="mt-3 rounded-xl bg-primary px-4 py-2 text-sm font-bold text-primary-foreground"
            >
              再送一次
            </button>
          )}
        </div>
      </div>
    )
  }

  if (submitting) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-muted-foreground">正在計算結果…</p>
        </div>
      </div>
    )
  }

  const currentQuestion = questions[currentIndex]

  return (
    <div className="mx-auto flex min-h-screen max-w-2xl flex-col px-4 py-8">
      <div className="mb-2 text-center">
        <h1 className="text-2xl font-bold">防詐能力前測</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          先做 {questions.length} 題，看看你對哪一類詐騙最沒把握
        </p>
      </div>

      <div className="my-6">
        <PretestProgress current={currentIndex + 1} total={questions.length} />
      </div>

      <div className="flex-1">
        {currentQuestion && (
          <PretestQuestion
            questionText={currentQuestion.question_text}
            options={currentQuestion.options}
            onAnswer={handleAnswer}
          />
        )}
      </div>
    </div>
  )
}
