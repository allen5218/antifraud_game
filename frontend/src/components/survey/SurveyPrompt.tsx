import { Link } from "@tanstack/react-router"
import { ClipboardList } from "lucide-react"
import { useHomeSummary } from "@/hooks/useHomeSummary"

/** 試測帳號做完檢測、還沒交問卷時，提醒去填 */
export function SurveyPrompt() {
  const { data } = useHomeSummary()
  if (!data?.survey_ready) return null
  return (
    <Link
      to="/survey"
      className="flex items-center gap-3 rounded-2xl border border-primary bg-primary/10 p-4"
    >
      <ClipboardList aria-hidden className="size-6 shrink-0 text-primary" />
      <span className="flex-1">
        <span className="block font-bold">填試測問卷</span>
        <span className="block text-xs text-muted-foreground">
          大約五分鐘，填完才算完成試測。
        </span>
      </span>
    </Link>
  )
}
