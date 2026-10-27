import { Link } from "@tanstack/react-router"
import { ClipboardList } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
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
          大約五分鐘，填完會顯示你的受試編號。
        </span>
      </span>
    </Link>
  )
}

/** 檢測結果頁一打開就跳出來：試測的下一步是填問卷。關掉後頁面上還有 SurveyPrompt */
export function SurveyNextDialog() {
  const { data } = useHomeSummary()
  const [dismissed, setDismissed] = useState(false)
  return (
    <Dialog
      open={Boolean(data?.survey_ready) && !dismissed}
      onOpenChange={(open) => {
        if (!open) setDismissed(true)
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>最後一步：填試測問卷</DialogTitle>
          <DialogDescription>
            大約五分鐘。填完會顯示你的受試編號，給工作人員核對。
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button asChild>
            <Link to="/survey">去填問卷</Link>
          </Button>
          <Button variant="outline" onClick={() => setDismissed(true)}>
            先看成績
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
