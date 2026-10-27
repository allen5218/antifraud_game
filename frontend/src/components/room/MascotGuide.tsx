import { Link } from "@tanstack/react-router"
import { Flame } from "lucide-react"
import { ExamActiveNotice } from "@/components/exam/ExamActiveNotice"
import type { MascotLine } from "./logic"

export function MascotGuide({
  line,
  streakDays,
  onClose,
}: {
  line: MascotLine | null
  streakDays: number
  onClose: () => void
}) {
  return (
    <div className="absolute top-[34%] left-1/2 z-30 w-[78%] -translate-x-1/2 rounded-2xl border bg-card p-3 text-sm text-card-foreground shadow-lg">
      {line && <p>{line.text}</p>}
      {line?.action && (
        <Link
          to={line.action.to}
          className="mt-3 inline-flex rounded-xl bg-primary px-3 py-2 text-sm font-bold text-primary-foreground"
        >
          {line.action.label}
        </Link>
      )}
      <ExamActiveNotice />
      <button
        type="button"
        onClick={onClose}
        className="mt-2 text-xs font-bold text-muted-foreground"
      >
        收起
      </button>
      {streakDays > 0 && (
        <p className="mt-2 flex items-center gap-1 text-[11px] text-muted-foreground">
          <Flame aria-hidden className="size-3.5 text-warning" />
          連續 {streakDays} 天
        </p>
      )}
    </div>
  )
}
