import { createFileRoute } from "@tanstack/react-router"
import { ExamAttempt } from "@/components/exam/ExamAttempt"
export const Route = createFileRoute("/_shell/exam_/$attemptId")({
  component: AttemptPage,
  head: () => ({ meta: [{ title: "檢測進度與結果 - ScamGym 識詐練習場" }] }),
})
function AttemptPage() {
  const { attemptId } = Route.useParams()
  return <ExamAttempt key={attemptId} attemptId={attemptId} />
}
