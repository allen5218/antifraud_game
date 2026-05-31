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

export const Route = createFileRoute("/pretest")({
  component: PretestPage,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({ to: "/login" })
    }
  },
  head: () => ({
    meta: [{ title: "前測評估 - 反詐騙訓練" }],
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
  const childMatch = useMatch({ from: "/pretest/result", shouldThrow: false })
  const [questions, setQuestions] = useState<QuestionData[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState<Answer[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 載入題目
  useState(() => {
    PretestService.getPretestQuestions()
      .then((data: any) => {
        setQuestions(data.questions ?? [])
        setLoading(false)
      })
      .catch(() => {
        setError("無法載入題目，請稍後再試。")
        setLoading(false)
      })
  })

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
      setSubmitting(true)
      try {
        const result = await PretestService.submitPretest({
          requestBody: { answers: newAnswers },
        })
        sessionStorage.setItem("pretestResult", JSON.stringify(result))
        navigate({ to: "/pretest/result" })
      } catch {
        setError("送出失敗，請稍後再試。")
        setSubmitting(false)
      }
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
          <p className="text-muted-foreground">載入題目中...</p>
        </div>
      </div>
    )
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

  if (submitting) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-muted-foreground">分析你的作答結果...</p>
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
          回答以下問題，讓我們了解你對各類詐騙的認知程度
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
