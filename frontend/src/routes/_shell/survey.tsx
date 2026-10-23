import { createFileRoute, Link } from "@tanstack/react-router"
import { useEffect, useState } from "react"
import { TrialSurveyForm } from "@/components/survey/TrialSurveyForm"
import { Button } from "@/components/ui/button"
import { extractErrorCode } from "@/hooks/useEconomy"
import {
  trialSurveyQuery,
  useStartTrialSurvey,
  useSubmitTrialSurvey,
  useTrialSurvey,
} from "@/hooks/useTrialSurvey"
import { warmQueries } from "@/lib/prefetch"

export const Route = createFileRoute("/_shell/survey")({
  loader: ({ context: { queryClient } }) => {
    warmQueries(queryClient, [trialSurveyQuery])
  },
  component: SurveyPage,
})

function errorDetail(error: unknown): { questionId?: string; message: string } {
  const detail = (error as { body?: { detail?: Record<string, unknown> } })
    ?.body?.detail
  if (extractErrorCode(error) === "survey_invalid" && detail) {
    return {
      questionId: String(detail.question_id),
      message: String(detail.message),
    }
  }
  if (extractErrorCode(error) === "survey_submitted")
    return { message: "這份問卷已經交過了。" }
  return { message: "送出失敗，請再送一次。" }
}

function SurveyPage() {
  const { data, error, isPending } = useTrialSurvey()
  const start = useStartTrialSurvey()
  const submit = useSubmitTrialSurvey()
  const [startFailed, setStartFailed] = useState(false)
  const canStart = data?.exam_done === true && data.submitted === false
  const { mutate: startSurvey } = start

  // 打開問卷頁才開始計時；重開不會重新計時（後端只記第一次）
  useEffect(() => {
    if (canStart)
      startSurvey(undefined, { onError: () => setStartFailed(true) })
  }, [canStart, startSurvey])

  if (error) {
    return (
      <Message>
        {extractErrorCode(error) === "trial_only"
          ? "這份問卷只給參加試測的人填。"
          : "問卷載入失敗，請稍後再試。"}
      </Message>
    )
  }
  if (isPending) return <Message>載入中…</Message>
  if (data.submitted) {
    return (
      <Message>
        <p className="font-bold text-foreground">問卷收到了，謝謝你！</p>
        <Button asChild className="mt-4">
          <Link to="/">回房間</Link>
        </Button>
      </Message>
    )
  }
  if (!data.exam_done) {
    return (
      <Message>
        <p>問卷會問到檢測的感想，請先完成一次檢測再來填。</p>
        <Button asChild className="mt-4">
          <Link to="/exam">去檢測</Link>
        </Button>
      </Message>
    )
  }
  if (startFailed) return <Message>問卷開不起來，請重新整理再試一次。</Message>
  if (!data.started) return <Message>載入中…</Message>

  return (
    <div className="flex flex-col gap-4 pb-8">
      <div>
        <h2 className="text-lg font-bold">試測問卷</h2>
        <p className="text-xs text-muted-foreground">
          照你玩過的感覺回答就好，大約五分鐘。每題都要仔細看，送出後就不能改。
        </p>
      </div>
      <TrialSurveyForm
        questions={data.questions}
        submitting={submit.isPending}
        error={submit.error ? errorDetail(submit.error) : null}
        onSubmit={(answers) => submit.mutate(answers)}
      />
    </div>
  )
}

function Message({ children }: { children: React.ReactNode }) {
  return (
    <div className="py-12 text-center text-sm text-muted-foreground">
      {children}
    </div>
  )
}
