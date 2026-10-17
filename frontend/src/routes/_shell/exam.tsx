import { createFileRoute } from "@tanstack/react-router"
import { ExamHome } from "@/components/exam/ExamHome"
export const Route = createFileRoute("/_shell/exam")({
  component: ExamHome,
  head: () => ({ meta: [{ title: "檢測 - ScamGym 識詐練習場" }] }),
})
